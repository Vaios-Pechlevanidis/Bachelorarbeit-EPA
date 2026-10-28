from __future__ import annotations

import html
import re
from datetime import date, timedelta
from typing import Any, Dict, List, Optional

from services.topic_average_rating_service import _fetch_all_rows


def clean_html_text(text: str) -> str:
    if not text or not isinstance(text, str):
        return text

    text = html.unescape(text)

    text = re.sub(r'<br\s*/?\s*>\s*-\s*', '\n• ', text, flags=re.IGNORECASE)

    text = re.sub(r'<br\s*/?\s*>', '\n', text, flags=re.IGNORECASE)

    text = re.sub(r'<[^>]+>', '', text)

    text = re.sub(r'^-\s*$', '', text, flags=re.MULTILINE)
    text = re.sub(r'^-\s+', '• ', text, flags=re.MULTILINE)

    text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)

    text = re.sub(r'\s+-\s*$', '', text, flags=re.MULTILINE)

    text = text.strip()

    return text


def build_full_review(row: Dict[str, Any]) -> Dict[str, Any]:
    source_type = "Mitarbeiter" if 'gut_am_arbeitgeber_finde_ich' in row else "Bewerber"
    employer_status = row.get("status", "Unbekannt")
    return {
        "titel": clean_html_text(row.get("titel", "Keine Titel")),
        "datum": row.get("datum"),
        "durchschnittsbewertung": row.get("durchschnittsbewertung"),
        "status": employer_status,
        "sourceType": source_type,
        "gut_am_arbeitgeber": clean_html_text(row.get("gut_am_arbeitgeber_finde_ich", "")),
        "schlecht_am_arbeitgeber": clean_html_text(row.get("schlecht_am_arbeitgeber_finde_ich", "")),
        "verbesserungsvorschlaege": clean_html_text(row.get("verbesserungsvorschlaege", "")),
        "stellenbeschreibung": clean_html_text(row.get("stellenbeschreibung", "")),
        "jobbeschreibung": clean_html_text(row.get("jobbeschreibung", "")),
        "ratings": {
            "arbeitsatmosphaere": row.get("sternebewertung_arbeitsatmosphaere"),
            "image": row.get("sternebewertung_image"),
            "work_life_balance": row.get("sternebewertung_work_life_balance"),
            "karriere_weiterbildung": row.get("sternebewertung_karriere_weiterbildung"),
            "gehalt_sozialleistungen": row.get("sternebewertung_gehalt_sozialleistungen"),
            "kollegenzusammenhalt": row.get("sternebewertung_kollegenzusammenhalt"),
            "umwelt_sozialbewusstsein": row.get("sternebewertung_umwelt_sozialbewusstsein"),
            "vorgesetztenverhalten": row.get("sternebewertung_vorgesetztenverhalten"),
            "kommunikation": row.get("sternebewertung_kommunikation"),
            "interessante_aufgaben": row.get("sternebewertung_interessante_aufgaben"),
            "umgang_mit_aelteren_kollegen": row.get("sternebewertung_umgang_mit_aelteren_kollegen"),
            "arbeitsbedingungen": row.get("sternebewertung_arbeitsbedingungen"),
            "gleichberechtigung": row.get("sternebewertung_gleichberechtigung")
        }
    }


CATEGORY_TEXT_FIELDS: List[str] = [
    "arbeitsatmosphaere", "image", "work_life_balance", "karriere_weiterbildung", "gehalt_sozialleistungen",
    "kollegenzusammenhalt", "umwelt_sozialbewusstsein", "vorgesetztenverhalten", "kommunikation",
    "interessante_aufgaben", "umgang_mit_aelteren_kollegen", "arbeitsbedingungen", "gleichberechtigung",
]

TEXT_FIELDS_BY_SOURCE: Dict[str, List[str]] = {
    "employee": ["gut_am_arbeitgeber_finde_ich", "schlecht_am_arbeitgeber_finde_ich", "verbesserungsvorschlaege",
                 *CATEGORY_TEXT_FIELDS],
    "candidates": ["stellenbeschreibung", "verbesserungsvorschlaege"],
}

_LETTER_RE = re.compile(r"[A-Za-zÄÖÜäöüß]")


def has_text_content(value: Any) -> bool:
    return isinstance(value, str) and _LETTER_RE.search(value) is not None

PREVIEW_MAX_CHARS = 240


def review_text(row: Dict[str, Any], source: str) -> str:
    parts = [clean_html_text(row.get(f)) for f in TEXT_FIELDS_BY_SOURCE.get(source, [])]
    return "\n\n".join(p.strip() for p in parts if has_text_content(p))


def review_preview(row: Dict[str, Any], source: str, max_chars: int = PREVIEW_MAX_CHARS) -> str:
    text = re.sub(r"\s+", " ", review_text(row, source)).strip()
    if len(text) > max_chars:
        text = text[: max_chars - 1].rstrip() + "…"
    return text


UNKNOWN_STATUS = "unbekannt"

STATUS_LABELS: Dict[str, Dict[str, str]] = {
    "employee": {
        "angestellt": "Angestellt",
        "ex-angestellt": "Ex-Angestellt",
        UNKNOWN_STATUS: "ohne Angabe",
    },
    "candidates": {
        "eingestellt": "Eingestellt",
        "angebot-abgelehnt": "Angebot abgelehnt",
        "abgelehnt": "Abgelehnt",
        "zurueckgestellt": "Zurückgestellt oder Absage",
        UNKNOWN_STATUS: "ohne Angabe",
    },
}

_RAW_STATUS: Dict[str, Dict[str, str]] = {
    "employee": {
        "1": "angestellt", "1.0": "angestellt", "true": "angestellt", "angestellt": "angestellt",
        "0": "ex-angestellt", "0.0": "ex-angestellt", "false": "ex-angestellt",
    },
    "candidates": {
        "hired": "eingestellt",
        "offerdeclined": "angebot-abgelehnt",
        "rejected": "abgelehnt",
        "deferred": "zurueckgestellt",
    },
}


def normalize_status(source: str, raw: Any) -> str:
    if raw is None:
        return UNKNOWN_STATUS
    s = str(raw).strip().lower()
    if not s:
        return UNKNOWN_STATUS
    if source == "employee" and re.match(r"^ex[-\s]?angestell", s):
        return "ex-angestellt"
    return _RAW_STATUS.get(source, {}).get(s, UNKNOWN_STATUS)


def validate_status(source: str, status: Optional[str]) -> Optional[str]:
    if status is None:
        return None
    allowed = STATUS_LABELS.get(source)
    if allowed is None:
        raise ValueError(f"source '{source}' ungültig; erlaubt: {', '.join(STATUS_LABELS)}.")
    if status not in allowed:
        raise ValueError(f"status '{status}' ist für source '{source}' unbekannt; erlaubt: {', '.join(allowed)}.")
    return status


def filter_by_status(rows: List[Dict[str, Any]], source: str, status: Optional[str]) -> List[Dict[str, Any]]:
    if status is None:
        return rows
    return [r for r in rows if normalize_status(source, r.get("status")) == status]


PAGE_SIZE = 1000


def parse_day(value: Optional[str], name: str) -> Optional[date]:
    if value is None:
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        raise ValueError(f"{name} '{value}' ist kein Datum im Format YYYY-MM-DD.") from None


def fetch_review_rows_in_range(
    source: str,
    company_id: int,
    start: Optional[date] = None,
    end: Optional[date] = None,
    columns: str = "*",
) -> List[Dict[str, Any]]:
    from database.supabase_client import get_supabase_client

    query = get_supabase_client().table(source).select(columns).eq("company_id", company_id)
    if start is not None:
        query = query.gte("datum", start.isoformat())
    if end is not None:
        query = query.lt("datum", (end + timedelta(days=1)).isoformat())
    return _fetch_all_rows(query.order("id"), page_size=PAGE_SIZE)


def sort_by_date(rows: List[Dict[str, Any]], newest_first: bool = True) -> List[Dict[str, Any]]:
    with_date = sorted(
        (r for r in rows if r.get("datum")),
        key=lambda r: (str(r["datum"]), r.get("id") or 0),
        reverse=newest_first,
    )
    return with_date + [r for r in rows if not r.get("datum")]


def sort_newest_first(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return sort_by_date(rows, newest_first=True)


def full_review_item(row: Dict[str, Any], source: str) -> Dict[str, Any]:
    return {"id": row.get("id"), "preview": review_preview(row, source), "fullReview": build_full_review(row)}


__all__ = [
    "clean_html_text", "build_full_review", "CATEGORY_TEXT_FIELDS", "TEXT_FIELDS_BY_SOURCE", "has_text_content",
    "review_text", "review_preview",
    "UNKNOWN_STATUS", "STATUS_LABELS", "normalize_status", "validate_status", "filter_by_status",
    "parse_day", "fetch_review_rows_in_range", "sort_by_date", "sort_newest_first", "full_review_item",
]
