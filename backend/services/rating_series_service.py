from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from services.review_service import filter_by_status, validate_status
from services.topic_average_rating_service import TOPIC_COLUMNS_BY_SOURCE, _fetch_all_rows

OVERALL_DIMENSION = "durchschnittsbewertung"
VALID_SOURCES = ("employee", "candidates")
DIMENSIONS_BY_SOURCE: Dict[str, List[str]] = {
    source: [OVERALL_DIMENSION] + list(TOPIC_COLUMNS_BY_SOURCE[source].keys())
    for source in VALID_SOURCES
}

MIN_REVIEWS_PER_MONTH = 5
MIN_EVALUATED_MONTHS = 12


def value_column(source: str, dimension: str = OVERALL_DIMENSION) -> str:
    if source not in VALID_SOURCES:
        raise ValueError(f"source '{source}' ungültig; erlaubt: {', '.join(VALID_SOURCES)}.")
    if dimension not in DIMENSIONS_BY_SOURCE[source]:
        raise ValueError(
            f"dimension '{dimension}' ist für source '{source}' unbekannt; "
            f"erlaubt: {', '.join(DIMENSIONS_BY_SOURCE[source])}."
        )
    if dimension == OVERALL_DIMENSION:
        return OVERALL_DIMENSION
    return TOPIC_COLUMNS_BY_SOURCE[source][dimension]


def month_key(datum_raw: Any) -> Optional[str]:
    if not datum_raw:
        return None
    try:
        dt = datetime.fromisoformat(str(datum_raw).replace("Z", "+00:00"))
    except ValueError:
        return None
    return f"{dt.year:04d}-{dt.month:02d}"


def month_range(first: str, last: str) -> List[str]:
    y, m = (int(x) for x in first.split("-"))
    last_y, last_m = (int(x) for x in last.split("-"))
    out: List[str] = []
    while (y, m) <= (last_y, last_m):
        out.append(f"{y:04d}-{m:02d}")
        m += 1
        if m == 13:
            y, m = y + 1, 1
    return out


def build_monthly_series(
    rows: List[Dict[str, Any]],
    column: str = OVERALL_DIMENSION,
    min_reviews: int = MIN_REVIEWS_PER_MONTH,
) -> List[Dict[str, Any]]:
    sums: Dict[str, float] = {}
    n_values: Dict[str, int] = {}
    counts: Dict[str, int] = {}
    for row in rows:
        period = month_key(row.get("datum"))
        if period is None:
            continue
        counts[period] = counts.get(period, 0) + 1
        value = row.get(column)
        if value is None:
            continue
        try:
            v = float(value)
        except (TypeError, ValueError):
            continue
        sums[period] = sums.get(period, 0.0) + v
        n_values[period] = n_values.get(period, 0) + 1

    if not counts:
        return []

    series: List[Dict[str, Any]] = []
    for period in month_range(min(counts), max(counts)):
        n = n_values.get(period, 0)
        series.append({
            "period": period,
            "mean": round(sums[period] / n, 3) if n else None,
            "count": counts.get(period, 0),
            "n_values": n,
            "evaluated": n >= min_reviews,
        })
    return series


def fetch_review_rows(
    source: str, company_id: int, column: str, status: Optional[str] = None,
) -> List[Dict[str, Any]]:
    from database.supabase_client import get_supabase_client

    columns = f"id,datum,{column}" + (",status" if status is not None else "")
    query = (
        get_supabase_client()
        .table(source)
        .select(columns)
        .eq("company_id", company_id)
        .order("id")
    )
    return filter_by_status(_fetch_all_rows(query, page_size=1000), source, status)


def _fetch_group_rows(source: str, company_id: int, column: str, status: Optional[str]) -> List[Dict[str, Any]]:
    if status is None:
        return fetch_review_rows(source, company_id, column)
    return fetch_review_rows(source, company_id, column, status)


def monthly_series(
    company_id: int,
    source: str,
    dimension: str = OVERALL_DIMENSION,
    min_reviews: int = MIN_REVIEWS_PER_MONTH,
    status: Optional[str] = None,
) -> Dict[str, Any]:
    column = value_column(source, dimension)
    validate_status(source, status)
    rows = _fetch_group_rows(source, company_id, column, status)
    series = build_monthly_series(rows, column, min_reviews)
    return {
        "company_id": company_id,
        "source": source,
        "dimension": dimension,
        "status": status,
        "column": column,
        "min_reviews": min_reviews,
        "evaluated_months": evaluated_months(series),
        "series": series,
    }


def monthly_series_by_dimension(
    company_id: int,
    source: str,
    min_reviews: int = MIN_REVIEWS_PER_MONTH,
    status: Optional[str] = None,
) -> Dict[str, List[Dict[str, Any]]]:
    columns = {dimension: value_column(source, dimension) for dimension in DIMENSIONS_BY_SOURCE.get(source, [])}
    if not columns:
        value_column(source)
    validate_status(source, status)
    rows = _fetch_group_rows(source, company_id, ",".join(dict.fromkeys(columns.values())), status)
    return {dimension: build_monthly_series(rows, column, min_reviews) for dimension, column in columns.items()}


def evaluated_months(series: List[Dict[str, Any]]) -> int:
    return sum(1 for month in series if month.get("evaluated"))


def is_eligible(series: List[Dict[str, Any]], min_months: int = MIN_EVALUATED_MONTHS) -> bool:
    return evaluated_months(series) >= min_months


__all__ = [
    "OVERALL_DIMENSION", "VALID_SOURCES", "DIMENSIONS_BY_SOURCE",
    "MIN_REVIEWS_PER_MONTH", "MIN_EVALUATED_MONTHS",
    "value_column", "month_key", "month_range",
    "build_monthly_series", "fetch_review_rows", "monthly_series", "monthly_series_by_dimension",
    "evaluated_months", "is_eligible",
]
