from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Tuple

DEFAULT_WINDOW_BEFORE = 3
DEFAULT_WINDOW_AFTER = 1
MAX_WINDOW_MONTHS = 24

KIND_CHANGE = "niveauwechsel"
KIND_OUTLIER = "einzelmonat"
KIND_SELECTION = "auswahl"
KIND_COMPARISON = "vergleich"

COMPARISON_OFFSETS = (-12, 12, -24, 24)
COMPARISON_MAX = 3

_PERIOD_RE = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")


def is_period(value: Any) -> bool:
    return isinstance(value, str) and _PERIOD_RE.fullmatch(value) is not None


def month_index(period: str) -> int:
    if not is_period(period):
        raise ValueError(f"Monat muss das Format YYYY-MM haben, nicht {period!r}.")
    return int(period[:4]) * 12 + int(period[5:7]) - 1


def period_from_index(index: int) -> str:
    return f"{index // 12:04d}-{index % 12 + 1:02d}"


def shift_month(period: str, months: int) -> str:
    return period_from_index(month_index(period) + months)


def month_range(first: str, last: str) -> List[str]:
    a, b = month_index(first), month_index(last)
    return [period_from_index(i) for i in range(a, b + 1)]


def _check_sizes(window_before: int, window_after: int) -> None:
    for name, value in (("window_before", window_before), ("window_after", window_after)):
        if not isinstance(value, int) or isinstance(value, bool) or value < 0 or value > MAX_WINDOW_MONTHS:
            raise ValueError(f"{name} muss eine ganze Zahl zwischen 0 und {MAX_WINDOW_MONTHS} sein, nicht {value!r}.")


def _window(kind: str, anchor_from: str, anchor_to: str, transition_from: str,
            window_before: int, window_after: int, anchor: Dict[str, Any]) -> Dict[str, Any]:
    start = shift_month(transition_from, -window_before)
    end = shift_month(anchor_to, window_after)
    return {
        "kind": kind,
        "from": start,
        "to": end,
        "months": month_index(end) - month_index(start) + 1,
        "transition_from": transition_from,
        "anchor_from": anchor_from,
        "anchor_to": anchor_to,
        "window_before": window_before,
        "window_after": window_after,
        "anchor": anchor,
    }


def window_for_change(
    date: str,
    previous_period: Optional[str] = None,
    gap_months: Optional[int] = None,
    window_before: int = DEFAULT_WINDOW_BEFORE,
    window_after: int = DEFAULT_WINDOW_AFTER,
) -> Dict[str, Any]:
    _check_sizes(window_before, window_after)
    if previous_period is not None and month_index(previous_period) >= month_index(date):
        raise ValueError("previous_period muss vor date liegen.")
    transition_from = shift_month(previous_period, 1) if previous_period else date
    gap = (month_index(date) - month_index(previous_period) - 1) if previous_period else 0
    anchor = {"date": date, "previous_period": previous_period, "gap_months": gap if gap_months is None else gap_months}
    return _window(KIND_CHANGE, date, date, transition_from, window_before, window_after, anchor)


def window_for_anomaly(anomaly: Dict[str, Any], window_before: int = DEFAULT_WINDOW_BEFORE,
                       window_after: int = DEFAULT_WINDOW_AFTER) -> Dict[str, Any]:
    return window_for_change(
        anomaly["date"], anomaly.get("previous_period"), anomaly.get("gap_months"), window_before, window_after,
    )


def window_for_outlier(date: str, window_before: int = DEFAULT_WINDOW_BEFORE,
                       window_after: int = DEFAULT_WINDOW_AFTER) -> Dict[str, Any]:
    _check_sizes(window_before, window_after)
    month_index(date)
    return _window(KIND_OUTLIER, date, date, date, window_before, window_after, {"date": date})


def window_for_selection(from_month: str, to_month: str, window_before: int = DEFAULT_WINDOW_BEFORE,
                         window_after: int = DEFAULT_WINDOW_AFTER) -> Dict[str, Any]:
    _check_sizes(window_before, window_after)
    if month_index(from_month) > month_index(to_month):
        raise ValueError("from liegt nach to.")
    return _window(KIND_SELECTION, from_month, to_month, from_month, window_before, window_after,
                   {"from": from_month, "to": to_month})


def window_months(window: Dict[str, Any]) -> List[str]:
    return month_range(window["from"], window["to"])


def windows_overlap(a: Dict[str, Any], b: Dict[str, Any]) -> bool:
    return a["from"] <= b["to"] and b["from"] <= a["to"]


def shift_window(window: Dict[str, Any], months: int) -> Dict[str, Any]:
    return {
        "kind": KIND_COMPARISON,
        "from": shift_month(window["from"], months),
        "to": shift_month(window["to"], months),
        "months": window["months"],
        "transition_from": shift_month(window["transition_from"], months),
        "anchor_from": shift_month(window["anchor_from"], months),
        "anchor_to": shift_month(window["anchor_to"], months),
        "window_before": window["window_before"],
        "window_after": window["window_after"],
        "offset_months": months,
        "reference": {"kind": window["kind"], "from": window["from"], "to": window["to"],
                      "anchor_from": window["anchor_from"], "anchor_to": window["anchor_to"]},
    }


def comparison_windows(
    window: Dict[str, Any],
    marker_windows: List[Dict[str, Any]],
    series_from: Optional[str] = None,
    series_to: Optional[str] = None,
    offsets: Tuple[int, ...] = COMPARISON_OFFSETS,
    max_count: int = COMPARISON_MAX,
) -> List[Dict[str, Any]]:
    if series_from is not None and series_to is not None and month_index(series_from) > month_index(series_to):
        raise ValueError("series_from liegt nach series_to.")
    out: List[Dict[str, Any]] = []
    for offset in offsets:
        if len(out) >= max_count:
            break
        candidate = shift_window(window, offset)
        if series_from is not None and candidate["from"] < series_from:
            continue
        if series_to is not None and candidate["to"] > series_to:
            continue
        if any(windows_overlap(candidate, m) for m in marker_windows):
            continue
        out.append(candidate)
    return out


__all__ = [
    "DEFAULT_WINDOW_BEFORE", "DEFAULT_WINDOW_AFTER", "MAX_WINDOW_MONTHS",
    "KIND_CHANGE", "KIND_OUTLIER", "KIND_SELECTION", "KIND_COMPARISON", "COMPARISON_OFFSETS", "COMPARISON_MAX",
    "is_period", "month_index", "period_from_index", "shift_month", "month_range",
    "window_for_change", "window_for_anomaly", "window_for_outlier", "window_for_selection", "window_months",
    "windows_overlap", "shift_window", "comparison_windows",
]


import json  # noqa: E402
import logging  # noqa: E402
import os  # noqa: E402
import tempfile  # noqa: E402
import threading  # noqa: E402
import time  # noqa: E402
from concurrent.futures import ThreadPoolExecutor  # noqa: E402
from datetime import datetime, timedelta, timezone  # noqa: E402
from pathlib import Path  # noqa: E402
from typing import Callable  # noqa: E402

from services import news_service  # noqa: E402
from services.dimension_scope import scope_evidence, single_dimension_topic  # noqa: E402
from services.evidence_sources import (  # noqa: E402
    SOURCE_EQS, SOURCE_GDELT, SOURCE_GLOBAL, SOURCE_GNEWS, SOURCE_LABELS, TYPE_ADHOC, TYPE_GLOBAL, TYPE_NEWS,
    dedupe, fetch_gnews_month, gnews_month_query, guess_language, make_item, throttle, utc_now,
)

logger = logging.getLogger(__name__)

BACKEND_DIR = Path(__file__).resolve().parent.parent
STORE_DIR = BACKEND_DIR / "data" / "context"
LIVE_FETCH_ENV = "CONTEXT_LIVE_FETCH"
GDELT_ENV = "CONTEXT_GDELT"
CURRENT_MONTH_MAX_AGE = timedelta(hours=12)
FAILED_FETCH_TTL = 15 * 60
STORE_VERSION = 1
GLOBAL_EVENTS_PATH: Optional[Path] = None
MAX_GLOBAL_EVENT_MONTHS = 6

EVIDENCE_NOTE = ("Belege sind zeitlich nahe Meldungen aus externen Quellen. Sie sind keine Aussage über "
                 "Ursachen; interne Auslöser sind von außen nicht sichtbar.")

_failed_fetches: Dict[Tuple[str, int, str], Tuple[float, str]] = {}
_month_locks: Dict[Tuple[str, int, str], threading.Lock] = {}
_month_locks_guard = threading.Lock()


def month_lock(key: Tuple[str, int, str]) -> threading.Lock:
    with _month_locks_guard:
        lock = _month_locks.get(key)
        if lock is None:
            lock = _month_locks[key] = threading.Lock()
        return lock


def live_fetch_enabled() -> bool:
    return os.getenv(LIVE_FETCH_ENV, "1").strip() != "0"


def gdelt_enabled() -> bool:
    return os.getenv(GDELT_ENV, "0").strip() == "1"


def _normalize_name(raw: Any) -> str:
    return " ".join(str(raw or "").split()).casefold()


def company_context_info(company_id: int, metadata: Optional[Dict[int, Dict[str, Any]]] = None) -> Optional[Dict[str, Any]]:
    from services.context_service import company_ticker_info, load_metadata

    info = company_ticker_info(company_id)
    if info is None:
        return None
    meta_all = load_metadata() if metadata is None else metadata
    meta = meta_all.get(int(company_id)) or {}
    if meta and _normalize_name(meta.get("name")) != _normalize_name(info.get("name")):
        meta = {}
    name = info.get("name") or ""
    eqs = meta.get("eqs") or {}
    return {
        "company_id": int(company_id),
        "name": name,
        "search_term": (meta.get("news_term") or "").strip() or news_service.search_term(name),
        "exclude": [str(e) for e in (meta.get("news_exclude") or []) if str(e).strip()],
        "term_confirmed": bool(meta.get("news_term_confirmed")),
        "ticker": info.get("ticker"),
        "ticker_scope": info.get("ticker_scope"),
        "eqs_uuid": eqs.get("uuid") or None,
        "eqs_name": eqs.get("company_name") or None,
        "title_words": [str(w).strip() for w in (meta.get("title_words") or []) if str(w).strip()],
    }


def available_sources(info: Dict[str, Any]) -> List[str]:
    sources = [SOURCE_GNEWS]
    if info.get("eqs_uuid"):
        sources.append(SOURCE_EQS)
    if gdelt_enabled():
        sources.append(SOURCE_GDELT)
    return sources


def record_path(company_id: int, source: str, month: str, store_dir: Optional[Path] = None) -> Path:
    if not is_period(month):
        raise ValueError(f"Monat muss das Format YYYY-MM haben, nicht {month!r}.")
    if not re.fullmatch(r"[a-z]+", source):
        raise ValueError(f"Quelle '{source}' ungültig.")
    return Path(store_dir or STORE_DIR) / str(int(company_id)) / source / f"{month}.json"


def load_record(company_id: int, source: str, month: str, store_dir: Optional[Path] = None) -> Optional[Dict[str, Any]]:
    path = record_path(company_id, source, month, store_dir)
    if not path.exists():
        return None
    try:
        with open(path, "r", encoding="utf-8") as fh:
            record = json.load(fh)
    except (OSError, ValueError) as exc:
        logger.warning("Belegspeicher %s nicht lesbar: %s", path, exc)
        return None
    if not isinstance(record, dict):
        return None
    if (record.get("company_id"), record.get("source"), record.get("month")) != (int(company_id), source, month):
        return None
    return record


def save_record(record: Dict[str, Any], store_dir: Optional[Path] = None) -> Path:
    path = record_path(record["company_id"], record["source"], record["month"], store_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=f".{path.stem}.", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(record, fh, ensure_ascii=False, indent=1)
        os.replace(tmp, path)
    except BaseException:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise
    return path


def is_month_complete(month: str, now: datetime) -> bool:
    return month < now.strftime("%Y-%m")


def build_record(company_id: int, source: str, month: str, query: Optional[str], items: List[Dict[str, Any]],
                 now: datetime) -> Dict[str, Any]:
    return {
        "version": STORE_VERSION,
        "company_id": int(company_id),
        "source": source,
        "month": month,
        "query": query,
        "fetched_at": now.replace(microsecond=0).isoformat(),
        "complete_month": is_month_complete(month, now),
        "status": "ok",
        "items": list(items),
    }


def record_is_current(record: Optional[Dict[str, Any]], month: str, now: datetime, query: Optional[str] = None) -> bool:
    if not isinstance(record, dict) or record.get("status") != "ok":
        return False
    if query is not None and record.get("query") != query:
        return False
    if is_month_complete(month, now):
        return True
    try:
        fetched = datetime.fromisoformat(str(record.get("fetched_at")))
    except (TypeError, ValueError):
        return False
    if fetched.tzinfo is None:
        fetched = fetched.replace(tzinfo=timezone.utc)
    return now - fetched < CURRENT_MONTH_MAX_AGE


Fetcher = Callable[[str], bytes]


def expected_query(info: Dict[str, Any], source: str, month: str) -> Optional[str]:
    if source == SOURCE_GNEWS:
        return gnews_month_query(info["search_term"], month, info.get("exclude") or [])
    return None


def fetch_source_month(info: Dict[str, Any], source: str, month: str,
                       fetcher: Optional[Fetcher] = None) -> Tuple[List[Dict[str, Any]], Optional[str]]:
    if source == SOURCE_GNEWS:
        return fetch_gnews_month(info["search_term"], month, info.get("exclude") or [], fetcher)
    if source == SOURCE_EQS:
        from services.evidence_sources import fetch_eqs_month
        return fetch_eqs_month(info, month, fetcher)
    if source == SOURCE_GDELT:
        from services.evidence_sources import fetch_gdelt_month
        return fetch_gdelt_month(info, month, fetcher)
    raise ValueError(f"Quelle '{source}' unbekannt.")


def month_record(
    info: Dict[str, Any],
    source: str,
    month: str,
    *,
    fetcher: Optional[Fetcher] = None,
    store_dir: Optional[Path] = None,
    now: Optional[datetime] = None,
    live: bool = True,
    sleep: Optional[Callable[[float], None]] = None,
    clock: Optional[Callable[[], float]] = None,
) -> Dict[str, Any]:
    now = now or utc_now()
    sleep = sleep or time.sleep
    clock = clock or time.monotonic
    company_id = int(info["company_id"])
    with month_lock((source, company_id, month)):
        return _month_record_locked(info, source, month, company_id, fetcher, store_dir, now, live, sleep, clock)


def _month_record_locked(info, source, month, company_id, fetcher, store_dir, now, live, sleep, clock) -> Dict[str, Any]:
    query = expected_query(info, source, month)
    record = load_record(company_id, source, month, store_dir)
    if record is not None and record_is_current(record, month, now, query):
        return {"record": record, "fetched_now": False, "error": None, "stale": False}
    stale = record if (record and record.get("status") == "ok" and (query is None or record.get("query") == query)) else None
    if not live or not live_fetch_enabled():
        error = None if stale is not None else (
            f"Kein gespeicherter Beleg für {month}; der Live-Abruf ist abgeschaltet ({LIVE_FETCH_ENV}=0)."
        )
        return {"record": stale, "fetched_now": False, "error": error, "stale": stale is not None}
    key = (source, company_id, month)
    failed = _failed_fetches.get(key)
    if failed and clock() - failed[0] < FAILED_FETCH_TTL:
        return {"record": stale, "fetched_now": False, "error": failed[1], "stale": stale is not None}
    throttle(source, sleep=sleep, clock=clock)
    try:
        items, used_query = fetch_source_month(info, source, month, fetcher)
    except Exception as exc:  # noqa: BLE001
        reason = f"{SOURCE_LABELS.get(source, source)} für {month} nicht abrufbar ({type(exc).__name__}: {exc})."
        logger.warning("Belegabruf %s/%s/%s fehlgeschlagen: %s", source, company_id, month, exc)
        _failed_fetches[key] = (clock(), reason)
        return {"record": stale, "fetched_now": False, "error": reason, "stale": stale is not None}
    new = build_record(company_id, source, month, used_query, items, now)
    save_record(new, store_dir)
    _failed_fetches.pop(key, None)
    return {"record": new, "fetched_now": True, "error": None, "stale": False}


_EVENT_FIELDS = ("id", "date_from", "date_to", "title", "scope", "note", "url", "confirmed")


def event_months(event: Dict[str, Any]) -> int:
    return month_index(event["date_to"]) - month_index(event["date_from"]) + 1


def load_global_events(path: Optional[Path] = None, confirmed_only: bool = True,
                       max_months: int = MAX_GLOBAL_EVENT_MONTHS) -> List[Dict[str, Any]]:
    if path is None and GLOBAL_EVENTS_PATH is None:
        from services import macro_events
        return macro_events.global_events(max_months=max_months)
    path = Path(path or GLOBAL_EVENTS_PATH)
    if not path.exists():
        return []
    try:
        with open(path, "r", encoding="utf-8") as fh:
            doc = json.load(fh)
    except (OSError, ValueError) as exc:
        logger.warning("global_events.json nicht lesbar: %s", exc)
        return []
    events = []
    for raw in (doc.get("events") if isinstance(doc, dict) else []) or []:
        if not isinstance(raw, dict) or any(k not in raw for k in _EVENT_FIELDS):
            continue
        if not (is_period(raw["date_from"]) and is_period(raw["date_to"])) or raw["date_from"] > raw["date_to"]:
            continue
        if event_months(raw) > max_months:
            logger.warning("Allgemeines Ereignis %r zurückgewiesen: %d Monate, erlaubt sind höchstens %d.",
                           raw.get("id"), event_months(raw), max_months)
            continue
        if confirmed_only and raw.get("confirmed") is not True:
            continue
        events.append({k: raw[k] for k in _EVENT_FIELDS})
    return events


def global_event_items(events: List[Dict[str, Any]], window: Dict[str, Any]) -> List[Dict[str, Any]]:
    items = []
    for e in events:
        if e["date_from"] > window["to"] or e["date_to"] < window["from"]:
            continue
        item = make_item(title=e["title"], url=e["url"], published_at=f"{e['date_from']}-01", publisher="Allgemeines Ereignis",
                         source=SOURCE_GLOBAL, source_type=TYPE_GLOBAL, language="de", category=e.get("scope") or None)
        item["id"] = f"global:{e['id']}"
        item["event"] = {"id": e["id"], "from": e["date_from"], "to": e["date_to"], "scope": e.get("scope"), "note": e.get("note")}
        items.append(item)
    return items


def _in_window(item: Dict[str, Any], window: Dict[str, Any]) -> bool:
    date = item.get("date") or ""
    return bool(date) and window["from"] <= date[:7] <= window["to"]


def with_language(item: Dict[str, Any]) -> Dict[str, Any]:
    if item.get("language"):
        return item
    return {**item, "language": guess_language(item.get("title") or "")}


def _sort_key(item: Dict[str, Any]) -> str:
    return str(item.get("datetime") or item.get("date") or "")


def evidence_for_window(
    info: Dict[str, Any],
    window: Dict[str, Any],
    *,
    sources: Optional[List[str]] = None,
    fetchers: Optional[Dict[str, Fetcher]] = None,
    store_dir: Optional[Path] = None,
    now: Optional[datetime] = None,
    live: bool = True,
    sleep: Optional[Callable[[float], None]] = None,
    clock: Optional[Callable[[], float]] = None,
    events: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    now = now or utc_now()
    months = window_months(window)
    used_sources = list(sources) if sources else available_sources(info)

    def collect(source: str) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
        fetcher = (fetchers or {}).get(source)
        s: Dict[str, Any] = {"label": SOURCE_LABELS.get(source, source), "months": len(months), "from_store": 0,
                             "fetched_now": 0, "missing": 0, "stale": 0, "errors": [], "fetched_at": None}
        found: List[Dict[str, Any]] = []
        for month in months:
            try:
                result = month_record(info, source, month, fetcher=fetcher, store_dir=store_dir, now=now, live=live,
                                      sleep=sleep, clock=clock)
            except Exception as exc:  # noqa: BLE001
                logger.warning("Beleg %s/%s/%s: %s", source, info.get("company_id"), month, exc)
                result = {"record": None, "fetched_now": False, "stale": False,
                          "error": f"{SOURCE_LABELS.get(source, source)} für {month} nicht lesbar ({type(exc).__name__}: {exc})."}
            record = result["record"]
            if record is None:
                s["missing"] += 1
            else:
                s["fetched_now" if result["fetched_now"] else "from_store"] += 1
                if result["stale"]:
                    s["stale"] += 1
                fetched_at = record.get("fetched_at")
                if fetched_at and (s["fetched_at"] is None or fetched_at > s["fetched_at"]):
                    s["fetched_at"] = fetched_at
                found.extend(with_language(it) for it in record.get("items") or [] if _in_window(it, window))
            if result["error"]:
                s["errors"].append({"month": month, "error": result["error"]})
        if not s["errors"] and s["missing"] == 0:
            s["status"] = "ok"
        elif s["missing"] == len(months):
            s["status"] = "fehlgeschlagen"
        else:
            s["status"] = "teilweise"
        return s, found

    if len(used_sources) > 1:
        with ThreadPoolExecutor(max_workers=len(used_sources), thread_name_prefix="evidence") as pool:
            collected = list(pool.map(collect, used_sources))
    else:
        collected = [collect(source) for source in used_sources]
    items: List[Dict[str, Any]] = []
    summary: Dict[str, Dict[str, Any]] = {}
    for source, (s, found) in zip(used_sources, collected):
        summary[source] = s
        items.extend(found)
    if events is None:
        events = load_global_events()
    if events:
        items.extend(global_event_items(events, window))
    items = dedupe(items)
    items.sort(key=_sort_key, reverse=True)
    counts = {TYPE_NEWS: 0, TYPE_ADHOC: 0, TYPE_GLOBAL: 0}
    for item in items:
        counts[item["source_type"]] = counts.get(item["source_type"], 0) + 1
    reason = None
    if not items:
        if summary and all(s["missing"] == s["months"] for s in summary.values()):
            errors = [e["error"] for s in summary.values() for e in s["errors"]]
            reason = errors[0] if errors else "Keine gespeicherten Belege für dieses Fenster."
        else:
            reason = "Kein Beleg im Fenster gefunden."
    return {
        "window": window,
        "items": items,
        "total": len(items),
        "counts": counts,
        "sources": summary,
        "coverage": counts[TYPE_NEWS] + counts[TYPE_ADHOC] > 0,
        "reason": reason,
        "note": EVIDENCE_NOTE,
    }


__all__ += [
    "STORE_DIR", "LIVE_FETCH_ENV", "GDELT_ENV", "CURRENT_MONTH_MAX_AGE", "FAILED_FETCH_TTL", "EVIDENCE_NOTE",
    "live_fetch_enabled", "gdelt_enabled", "company_context_info", "available_sources",
    "record_path", "load_record", "save_record", "is_month_complete", "build_record", "record_is_current",
    "expected_query", "fetch_source_month", "month_lock", "month_record", "with_language", "evidence_for_window",
    "GLOBAL_EVENTS_PATH", "MAX_GLOBAL_EVENT_MONTHS", "event_months", "load_global_events", "global_event_items",
]


OUTLIER_SUFFIX = "einzelmonat"


def resolve_anchor(company_id: int, anomaly_id: str, source: Optional[str] = None, dimension: Optional[str] = None,
                   status: Optional[str] = None) -> Optional[Dict[str, Any]]:
    from services.anomaly_service import company_anomalies

    parts = anomaly_id.split(":")
    if len(parts) == 4 and parts[3] == OUTLIER_SUFFIX and all(parts[:3]):
        kind = KIND_OUTLIER
    elif len(parts) == 3 and all(parts):
        kind = KIND_CHANGE
    else:
        return None
    if not is_period(parts[2]):
        return None
    source = source or parts[0]
    dimension = dimension or parts[1]
    detected = company_anomalies(company_id, source=source, dimension=dimension, status=status)
    if kind == KIND_CHANGE:
        anomaly = next((a for a in detected["anomalies"] if a["id"] == anomaly_id), None)
        if anomaly is None:
            return None
        return {"kind": kind, "id": anomaly_id, "source": source, "dimension": dimension, "status": status,
                "date": anomaly["date"], "direction": anomaly["direction"], "previous_period": anomaly.get("previous_period"),
                "gap_months": anomaly.get("gap_months"), "delta": anomaly.get("delta")}
    outlier = next((o for o in detected.get("outlier_months") or [] if o["id"] == anomaly_id), None)
    if outlier is None:
        return None
    return {"kind": kind, "id": anomaly_id, "source": source, "dimension": dimension, "status": status,
            "date": outlier["date"], "direction": outlier["direction"], "previous_period": None, "gap_months": None,
            "deviation": outlier.get("deviation")}


def _context_response(info: Dict[str, Any], anchor: Dict[str, Any], window: Dict[str, Any], evidence: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "company_id": info["company_id"],
        "company": info["name"],
        "search_term": info["search_term"],
        "anchor": anchor,
        **evidence,
    }


def context_for_anchor(
    company_id: int,
    anomaly_id: str,
    *,
    source: Optional[str] = None,
    dimension: Optional[str] = None,
    status: Optional[str] = None,
    dimension_only: bool = False,
    window_before: int = DEFAULT_WINDOW_BEFORE,
    window_after: int = DEFAULT_WINDOW_AFTER,
    **evidence_kwargs: Any,
) -> Optional[Dict[str, Any]]:
    info = company_context_info(company_id)
    if info is None:
        return None
    anchor = resolve_anchor(company_id, anomaly_id, source, dimension, status)
    if anchor is None:
        return {"anchor": None}
    if anchor["kind"] == KIND_CHANGE:
        window = window_for_change(anchor["date"], anchor["previous_period"], anchor["gap_months"], window_before, window_after)
    else:
        window = window_for_outlier(anchor["date"], window_before, window_after)
    if dimension_only:
        single_dimension_topic(anchor["source"], anchor["dimension"])
    evidence = evidence_for_window(info, window, **evidence_kwargs)
    if dimension_only:
        evidence = scope_evidence(evidence, anchor["source"], anchor["dimension"], company_id=info.get("company_id"))
    return _context_response(info, anchor, window, evidence)


def context_for_selection(
    company_id: int,
    from_month: str,
    to_month: str,
    *,
    source: Optional[str] = None,
    dimension: Optional[str] = None,
    dimension_only: bool = False,
    window_before: int = DEFAULT_WINDOW_BEFORE,
    window_after: int = DEFAULT_WINDOW_AFTER,
    **evidence_kwargs: Any,
) -> Optional[Dict[str, Any]]:
    from services.rating_series_service import value_column

    source = source or "employee"
    if dimension is not None:
        value_column(source, dimension)
    if dimension_only:
        single_dimension_topic(source, dimension)
    info = company_context_info(company_id)
    if info is None:
        return None
    window = window_for_selection(from_month, to_month, window_before, window_after)
    anchor = {"kind": KIND_SELECTION, "id": None, "from": from_month, "to": to_month}
    evidence = evidence_for_window(info, window, **evidence_kwargs)
    if dimension_only:
        evidence = scope_evidence(evidence, source, dimension, company_id=info.get("company_id"))
    return _context_response(info, anchor, window, evidence)


def paginate(result: Dict[str, Any], offset: int = 0, limit: int = 25) -> Dict[str, Any]:
    items = result.get("items") or []
    return {**result, "items": items[offset:offset + limit], "offset": offset, "limit": limit, "total": len(items)}


__all__ += ["OUTLIER_SUFFIX", "resolve_anchor", "context_for_anchor", "context_for_selection", "paginate"]
