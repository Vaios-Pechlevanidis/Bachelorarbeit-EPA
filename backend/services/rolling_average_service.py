from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from services.rating_series_service import OVERALL_DIMENSION, month_key, value_column
from services.review_service import validate_status

SHORT_MONTHS = 12
LONG_MONTHS = 24
LOW_BASIS_MIN_REVIEWS = 10
SIGN_EPS = 0.05
ANCHOR_RULE = "letzter voller Kalendermonat mit Bewertungen des Unternehmens, nicht das heutige Datum"


def _month_index(period: str) -> int:
    y, m = (int(x) for x in period.split("-"))
    return y * 12 + (m - 1)


def _period(index: int) -> str:
    return f"{index // 12:04d}-{index % 12 + 1:02d}"


def _current_month(today: Optional[datetime] = None) -> str:
    now = today or datetime.now(timezone.utc)
    return f"{now.year:04d}-{now.month:02d}"


def _value(row: Dict[str, Any], column: str) -> Optional[float]:
    value = row.get(column)
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def dated_values(rows: List[Dict[str, Any]], column: str = OVERALL_DIMENSION) -> List[tuple[str, float]]:
    out: List[tuple[str, float]] = []
    for row in rows:
        period = month_key(row.get("datum"))
        if period is None:
            continue
        v = _value(row, column)
        if v is None:
            continue
        out.append((period, v))
    return out


def last_full_month_with_data(values: List[tuple[str, float]], today: Optional[datetime] = None) -> Optional[str]:
    current = _current_month(today)
    months = [p for p, _ in values if p < current]
    return max(months) if months else None


def rolling_window(
    values: List[tuple[str, float]],
    anchor: str,
    months: int,
    min_reviews: int = LOW_BASIS_MIN_REVIEWS,
    first_month: Optional[str] = None,
) -> Dict[str, Any]:
    end = _month_index(anchor)
    start = end - months + 1
    window_from, window_to = _period(start), _period(end)
    inside = [v for p, v in values if window_from <= p <= window_to]
    n = len(inside)
    months_with_reviews = len({p for p, _ in values if window_from <= p <= window_to})
    data_from = first_month or (min(p for p, _ in values) if values else None)
    covered = bool(data_from) and data_from <= window_from
    return {
        "months": months,
        "from": window_from,
        "to": window_to,
        "mean": round(sum(inside) / n, 2) if n else None,
        "n": n,
        "months_with_reviews": months_with_reviews,
        "low_basis": n < min_reviews,
        "covered": covered,
        "covered_from": data_from if data_from and not covered else None,
    }


def _sign(difference: Optional[float]) -> Optional[str]:
    if difference is None:
        return None
    if difference > SIGN_EPS:
        return "up"
    if difference < -SIGN_EPS:
        return "down"
    return "flat"


def rolling_averages(
    rows: List[Dict[str, Any]],
    column: str = OVERALL_DIMENSION,
    today: Optional[datetime] = None,
    short_months: int = SHORT_MONTHS,
    long_months: int = LONG_MONTHS,
    min_reviews: int = LOW_BASIS_MIN_REVIEWS,
) -> Dict[str, Any]:
    values = dated_values(rows, column)
    anchor = last_full_month_with_data(values, today)
    result: Dict[str, Any] = {
        "mode": "rolling",
        "column": column,
        "today": _current_month(today),
        "anchor": anchor,
        "anchor_rule": ANCHOR_RULE,
        "first_month": min(p for p, _ in values) if values else None,
        "last_month": max(p for p, _ in values) if values else None,
        "n_total": len(values),
        "short": None,
        "long": None,
        "difference": None,
        "sign": None,
        "low_basis": False,
        "low_basis_rule": {"min_reviews_per_window": min_reviews, "origin": "E12, vorläufig (T5 offen)"},
        "history_months": 0,
        "insufficient_history": True,
    }
    if anchor is None:
        return result
    first_month = result["first_month"]
    short = rolling_window(values, anchor, short_months, min_reviews, first_month)
    long = rolling_window(values, anchor, long_months, min_reviews, first_month)
    short_vals = [v for p, v in values if short["from"] <= p <= short["to"]]
    long_vals = [v for p, v in values if long["from"] <= p <= long["to"]]
    difference = None
    if short_vals and long_vals:
        difference = round(sum(short_vals) / len(short_vals) - sum(long_vals) / len(long_vals), 2)
    history = _month_index(anchor) - _month_index(first_month) + 1
    result.update({
        "short": short,
        "long": long,
        "difference": difference,
        "sign": _sign(difference),
        "low_basis": bool(short["low_basis"] or long["low_basis"]),
        "history_months": history,
        "insufficient_history": history < long_months,
    })
    return result


def company_rolling_averages(
    company_id: int,
    source: str = "employee",
    dimension: str = OVERALL_DIMENSION,
    status: Optional[str] = None,
    today: Optional[datetime] = None,
) -> Dict[str, Any]:
    from services.rating_series_service import fetch_review_rows

    column = value_column(source, dimension)
    validate_status(source, status)
    rows = fetch_review_rows(source, company_id, column, status) if status is not None else fetch_review_rows(source, company_id, column)
    result = rolling_averages(rows, column, today)
    result.update({"company_id": int(company_id), "source": source, "dimension": dimension, "status": status})
    return result


__all__ = [
    "SHORT_MONTHS", "LONG_MONTHS", "LOW_BASIS_MIN_REVIEWS", "SIGN_EPS", "ANCHOR_RULE",
    "dated_values", "last_full_month_with_data", "rolling_window", "rolling_averages", "company_rolling_averages",
]
