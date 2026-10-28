from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

MIGRATION_FILE = "backend/migrations/007_create_user_events.sql"
TABLE = "user_events"
TITLE_MAX = 120
NOTE_MAX = 1000
MONTH_RE = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")

USER_EVENT_NOTE = (
    "Eigene Ereignisse sind von Nutzerinnen und Nutzern eingetragene Zeiträume zur Einordnung. "
    "Sie sind keine Aussage über Ursachen und gehen nicht in Erkennung, Rangfolge oder Belege ein; "
    "bei den Erklärungsansätzen stehen sie nur nach zeitlicher Nähe als möglicher Zusammenhang."
)

FIELDS = ("id", "company_id", "date_from", "date_to", "title", "note", "created_at", "updated_at")

_MISSING_TABLE_CODES = ("42P01", "PGRST205")


class MissingTableError(RuntimeError):
    def __init__(self) -> None:
        super().__init__(
            f"Eigene Ereignisse sind nicht eingerichtet: Die Tabelle {TABLE} fehlt. "
            f"Bitte die Migration {MIGRATION_FILE} in der Datenbank ausführen."
        )


def is_missing_table_error(exc: Exception) -> bool:
    code = str(getattr(exc, "code", "") or "")
    text = str(exc)
    return any(c in code or c in text for c in _MISSING_TABLE_CODES) or f"'public.{TABLE}'" in text


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def month_count(date_from: str, date_to: str) -> int:
    y1, m1 = (int(p) for p in date_from.split("-"))
    y2, m2 = (int(p) for p in date_to.split("-"))
    return (y2 * 12 + m2) - (y1 * 12 + m1) + 1


def normalize_event(payload: Dict[str, Any]) -> Dict[str, Any]:
    title = str(payload.get("title") or "").strip()
    if not title:
        raise ValueError("Bitte einen Titel angeben.")
    if len(title) > TITLE_MAX:
        raise ValueError(f"Der Titel darf höchstens {TITLE_MAX} Zeichen haben.")

    date_from = str(payload.get("date_from") or "").strip()
    if not MONTH_RE.match(date_from):
        raise ValueError("Bitte einen Startmonat im Format JJJJ-MM angeben.")
    date_to = str(payload.get("date_to") or "").strip() or date_from
    if not MONTH_RE.match(date_to):
        raise ValueError("Bitte einen Endmonat im Format JJJJ-MM angeben.")
    if date_to < date_from:
        raise ValueError("Der Endmonat darf nicht vor dem Startmonat liegen.")

    note_raw = payload.get("note")
    note = str(note_raw).strip() if note_raw is not None else ""
    if len(note) > NOTE_MAX:
        raise ValueError(f"Der Vermerk darf höchstens {NOTE_MAX} Zeichen haben.")

    return {"title": title, "date_from": date_from, "date_to": date_to, "note": note or None}


def _public(row: Dict[str, Any]) -> Dict[str, Any]:
    out = {k: row.get(k) for k in FIELDS}
    out["months"] = month_count(out["date_from"], out["date_to"])
    return out


def _sorted(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return sorted(rows, key=lambda r: (str(r.get("date_from")), str(r.get("date_to")), int(r.get("id") or 0)))


def _run(query):
    try:
        return query.execute()
    except Exception as exc:  # noqa: BLE001
        if is_missing_table_error(exc):
            raise MissingTableError() from exc
        raise


def company_exists(client, company_id: int) -> bool:
    result = client.table("companies").select("id").eq("id", company_id).limit(1).execute()
    return bool(result.data)


def list_events(client, company_id: int) -> List[Dict[str, Any]]:
    result = _run(client.table(TABLE).select("*").eq("company_id", company_id))
    return [_public(r) for r in _sorted(result.data or [])]


def get_event(client, company_id: int, event_id: int) -> Optional[Dict[str, Any]]:
    result = _run(client.table(TABLE).select("*").eq("company_id", company_id).eq("id", event_id).limit(1))
    return _public(result.data[0]) if result.data else None


def create_event(client, company_id: int, payload: Dict[str, Any]) -> Dict[str, Any]:
    values = normalize_event(payload)
    now = _now()
    row = {"company_id": company_id, **values, "created_at": now, "updated_at": now}
    result = _run(client.table(TABLE).insert(row))
    if not result.data:
        raise RuntimeError("Das Ereignis konnte nicht gespeichert werden.")
    return _public(result.data[0])


def update_event(client, company_id: int, event_id: int, payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    values = normalize_event(payload)
    if get_event(client, company_id, event_id) is None:
        return None
    result = _run(client.table(TABLE).update({**values, "updated_at": _now()}).eq("company_id", company_id).eq("id", event_id))
    rows = result.data or []
    return _public(rows[0]) if rows else get_event(client, company_id, event_id)


def delete_event(client, company_id: int, event_id: int) -> bool:
    if get_event(client, company_id, event_id) is None:
        return False
    _run(client.table(TABLE).delete().eq("company_id", company_id).eq("id", event_id))
    return True
