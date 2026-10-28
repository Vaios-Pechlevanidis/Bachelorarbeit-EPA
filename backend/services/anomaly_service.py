from __future__ import annotations

from typing import Any, Dict, List, Optional

from statistics import median

from models.changepoint_detector import (
    DEFAULT_MIN_SIZE,
    DEFAULT_MODEL,
    DEFAULT_PENALTY_FACTOR,
    PeltDetector,
    detect_changepoints,
    level_shifts,
    noise_sigma,
)
from services.rating_series_service import (
    MIN_EVALUATED_MONTHS,
    MIN_REVIEWS_PER_MONTH,
    OVERALL_DIMENSION,
    build_monthly_series,
    evaluated_months,
    is_eligible,
    monthly_series,
    monthly_series_by_dimension,
)

DEFAULT_MIN_DELTA = 0.3
SEVERITY_HIGH = 0.5
OUTLIER_SIGMA_FACTOR = 3.0
OUTLIER_MIN_DELTA = 0.5

_DIRECTION_ORDER = {"fall": 0, "rise": 1}


def _severity(delta: float) -> str:
    return "high" if abs(delta) >= SEVERITY_HIGH else "medium"


def _detector(penalty: Optional[float], penalty_factor: float,
              model: str = DEFAULT_MODEL, min_size: int = DEFAULT_MIN_SIZE) -> PeltDetector:
    return PeltDetector(model=model, min_size=min_size, penalty=penalty, penalty_factor=penalty_factor)


def detection_params(
    series: List[Dict[str, Any]],
    penalty: Optional[float] = None,
    penalty_factor: float = DEFAULT_PENALTY_FACTOR,
    min_delta: float = DEFAULT_MIN_DELTA,
) -> Dict[str, Any]:
    values = [float(m["mean"]) for m in series if m.get("evaluated") and m.get("mean") is not None]
    det = _detector(penalty, penalty_factor)
    resolved = det.for_series(values) if values else det
    return {
        "method": "pelt",
        **{k: v for k, v in resolved.params().items() if k != "jump"},
        "n_evaluated": len(values),
        "min_delta": min_delta,
        "min_reviews_per_month": MIN_REVIEWS_PER_MONTH,
        "outlier_sigma_factor": OUTLIER_SIGMA_FACTOR,
        "outlier_min_delta": OUTLIER_MIN_DELTA,
        "outlier_neighbours": OUTLIER_NEIGHBOURS,
    }


def _months_between(a: str, b: str) -> int:
    ya, ma = (int(x) for x in a.split("-"))
    yb, mb = (int(x) for x in b.split("-"))
    return (yb * 12 + mb) - (ya * 12 + ma)


def _n_values(months: List[Dict[str, Any]]) -> int:
    return sum(int(m.get("n_values", m.get("count", 0))) for m in months)


def eligibility(series: List[Dict[str, Any]]) -> Dict[str, Any]:
    n = evaluated_months(series)
    eligible = is_eligible(series)
    reason = None
    if not eligible:
        reason = (
            f"Nur {n} bewertete Monate (mindestens {MIN_EVALUATED_MONTHS} nötig, "
            f"je Monat mindestens {MIN_REVIEWS_PER_MONTH} Bewertungen)."
            if series else "Keine datierten Bewertungen in dieser Quelle."
        )
    return {
        "eligible": eligible,
        "evaluated_months": n,
        "min_evaluated_months": MIN_EVALUATED_MONTHS,
        "reason": reason,
    }


def sort_anomalies(anomalies: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return sorted(anomalies, key=lambda a: (_DIRECTION_ORDER[a["direction"]], -abs(a["delta"]), a["date"]))


def detect_anomalies(
    series: List[Dict[str, Any]],
    *,
    company_id: int,
    source: str,
    dimension: str = OVERALL_DIMENSION,
    penalty: Optional[float] = None,
    min_delta: float = DEFAULT_MIN_DELTA,
    penalty_factor: float = DEFAULT_PENALTY_FACTOR,
    model: str = DEFAULT_MODEL,
    min_size: int = DEFAULT_MIN_SIZE,
) -> List[Dict[str, Any]]:
    evaluated = [m for m in series if m.get("evaluated") and m.get("mean") is not None]
    values = [float(m["mean"]) for m in evaluated]
    result = detect_changepoints(values, _detector(penalty, penalty_factor, model, min_size))
    params = {**result.params, "min_delta": min_delta}

    anomalies: List[Dict[str, Any]] = []
    for shift in level_shifts(values, result.indices):
        delta = shift["delta"]
        if abs(delta) < min_delta:
            continue
        idx = shift["index"]
        period = evaluated[idx]["period"]
        previous = evaluated[idx - 1]["period"]
        month_mean = float(evaluated[idx]["mean"])
        n_before = _n_values(evaluated[shift["before_start"]:shift["index"]])
        n_after = _n_values(evaluated[shift["index"]:shift["after_end"]])
        anomalies.append({
            "id": f"{source}:{dimension}:{period}",
            "company_id": company_id,
            "source": source,
            "dimension": dimension,
            "date": period,
            "direction": "fall" if delta < 0 else "rise",
            "delta": round(delta, 3),
            "before_mean": round(shift["before_mean"], 3),
            "after_mean": round(shift["after_mean"], 3),
            "n_reviews_before": n_before,
            "n_reviews_after": n_after,
            "n_reviews": n_before + n_after,
            "before_from": evaluated[shift["before_start"]]["period"],
            "after_to": evaluated[shift["after_end"] - 1]["period"],
            "previous_period": previous,
            "gap_months": _months_between(previous, period) - 1,
            "month_mean": round(month_mean, 3),
            "month_near_previous_level": abs(month_mean - shift["before_mean"]) < abs(month_mean - shift["after_mean"]),
            "severity": _severity(delta),
            "method": result.method,
            "params": params,
        })
    return sort_anomalies(anomalies)


OUTLIER_NEIGHBOURS = 3

STABILITY_GRID: Dict[str, tuple] = {
    "penalty_factor": (1.0, 2.0, 3.0, 4.0),
    "min_size": (2, 3, 4, 6),
    "min_reviews_per_month": (3, 5, 8),
}
STABILITY_TOLERANCE_MONTHS = 3


def _same_change(a: Dict[str, Any], b: Dict[str, Any], tolerance: int) -> bool:
    return a["direction"] == b["direction"] and abs(_months_between(a["date"], b["date"])) <= tolerance


def stability_of_anomalies(
    anomalies: List[Dict[str, Any]],
    rows: List[Dict[str, Any]],
    column: str,
    *,
    company_id: int,
    source: str,
    dimension: str,
    min_delta: float = DEFAULT_MIN_DELTA,
    grid: Optional[Dict[str, tuple]] = None,
    tolerance: int = STABILITY_TOLERANCE_MONTHS,
) -> List[Dict[str, Any]]:
    grid = grid or STABILITY_GRID
    if not anomalies:
        return []
    series_by_min: Dict[int, List[Dict[str, Any]]] = {}
    variants: List[List[Dict[str, Any]]] = []
    for min_reviews in grid["min_reviews_per_month"]:
        series = series_by_min.setdefault(min_reviews, build_monthly_series(rows, column, min_reviews))
        if not is_eligible(series):
            continue
        for factor in grid["penalty_factor"]:
            for min_size in grid["min_size"]:
                variants.append(detect_anomalies(
                    series, company_id=company_id, source=source, dimension=dimension,
                    min_delta=min_delta, penalty_factor=factor, min_size=min_size,
                ))
    out: List[Dict[str, Any]] = []
    for a in anomalies:
        matches = sum(1 for found in variants if any(_same_change(a, b, tolerance) for b in found))
        out.append({
            **a,
            "stability": {
                "variants": len(variants),
                "matches": matches,
                "share": round(matches / len(variants), 2) if variants else None,
                "tolerance_months": tolerance,
                "grid": {k: list(v) for k, v in grid.items()},
            },
        })
    return out


def detect_outlier_months(
    series: List[Dict[str, Any]],
    *,
    company_id: int,
    source: str,
    dimension: str = OVERALL_DIMENSION,
    sigma_factor: float = OUTLIER_SIGMA_FACTOR,
    min_deviation: float = OUTLIER_MIN_DELTA,
    neighbours: int = OUTLIER_NEIGHBOURS,
) -> List[Dict[str, Any]]:
    evaluated = [m for m in series if m.get("evaluated") and m.get("mean") is not None]
    values = [float(m["mean"]) for m in evaluated]
    if len(values) < 5:
        return []
    sigma = noise_sigma(values)
    threshold = max(sigma_factor * sigma, min_deviation)
    found: List[Dict[str, Any]] = []
    for i, value in enumerate(values):
        left = values[max(0, i - neighbours):i]
        right = values[i + 1:i + 1 + neighbours]
        if len(left) < 2 or len(right) < 2:
            continue
        dev_left, dev_right = value - median(left), value - median(right)
        if min(abs(dev_left), abs(dev_right)) < threshold or (dev_left > 0) != (dev_right > 0):
            continue
        level = float(median(left + right))
        deviation = value - level
        sign = 1 if deviation > 0 else -1
        if any(sign * (values[j] - level) >= threshold for j in (i - 1, i + 1)):
            continue
        period = evaluated[i]["period"]
        found.append({
            "id": f"{source}:{dimension}:{period}:einzelmonat",
            "company_id": company_id,
            "source": source,
            "dimension": dimension,
            "date": period,
            "direction": "fall" if deviation < 0 else "rise",
            "month_mean": round(value, 3),
            "level": round(level, 3),
            "deviation": round(deviation, 3),
            "n_values": int(evaluated[i].get("n_values", evaluated[i].get("count", 0))),
            "neighbours_from": evaluated[i - len(left)]["period"],
            "neighbours_to": evaluated[i + len(right)]["period"],
            "noise_sigma": round(sigma, 6),
            "threshold": round(threshold, 6),
        })
    return sorted(found, key=lambda o: (-abs(o["deviation"]), o["date"]))


def company_anomalies(
    company_id: int,
    source: str = "employee",
    dimension: str = OVERALL_DIMENSION,
    penalty: Optional[float] = None,
    min_delta: float = DEFAULT_MIN_DELTA,
    penalty_factor: float = DEFAULT_PENALTY_FACTOR,
    status: Optional[str] = None,
) -> Dict[str, Any]:
    from services.rating_series_service import _fetch_group_rows, validate_status, value_column

    column = value_column(source, dimension)
    validate_status(source, status)
    rows = _fetch_group_rows(source, company_id, column, status)
    series = build_monthly_series(rows, column, MIN_REVIEWS_PER_MONTH)
    data = {"min_reviews": MIN_REVIEWS_PER_MONTH}
    elig = eligibility(series)
    anomalies = (
        detect_anomalies(
            series, company_id=company_id, source=source, dimension=dimension,
            penalty=penalty, min_delta=min_delta, penalty_factor=penalty_factor,
        )
        if elig["eligible"] else []
    )
    if anomalies and penalty is None:
        anomalies = stability_of_anomalies(
            anomalies, rows, column, company_id=company_id, source=source, dimension=dimension, min_delta=min_delta,
        )
    outliers = (
        detect_outlier_months(series, company_id=company_id, source=source, dimension=dimension)
        if elig["eligible"] else []
    )
    result = {
        "company_id": company_id,
        "source": source,
        "dimension": dimension,
        "series": [
            {
                "period": m["period"], "mean": m["mean"], "count": m["count"],
                "n_values": m["n_values"], "evaluated": m["evaluated"],
            }
            for m in series
        ],
        "anomalies": anomalies,
        "outlier_months": outliers,
        "params": {
            **detection_params(series, penalty, penalty_factor, min_delta),
            "min_reviews_per_month": data["min_reviews"],
        },
        "eligibility": elig,
    }
    if status is not None:
        result["status"] = status
    return result


def company_anomalies_all(
    company_id: int,
    source: str = "employee",
    penalty: Optional[float] = None,
    min_delta: float = DEFAULT_MIN_DELTA,
    penalty_factor: float = DEFAULT_PENALTY_FACTOR,
    status: Optional[str] = None,
) -> Dict[str, Any]:
    series_by_dimension = monthly_series_by_dimension(company_id, source, status=status)
    dimensions: List[Dict[str, Any]] = []
    combined: List[Dict[str, Any]] = []
    combined_outliers: List[Dict[str, Any]] = []
    for dimension, series in series_by_dimension.items():
        elig = eligibility(series)
        found = (
            detect_anomalies(
                series, company_id=company_id, source=source, dimension=dimension,
                penalty=penalty, min_delta=min_delta, penalty_factor=penalty_factor,
            )
            if elig["eligible"] else []
        )
        outliers = (
            detect_outlier_months(series, company_id=company_id, source=source, dimension=dimension)
            if elig["eligible"] else []
        )
        dimensions.append({
            "dimension": dimension, "eligibility": elig, "anomalies": found, "outlier_months": outliers,
            "params": detection_params(series, penalty, penalty_factor, min_delta),
        })
        combined.extend(found)
        combined_outliers.extend(outliers)
    result = {
        "company_id": company_id,
        "source": source,
        "dimension": "all",
        "dimensions": dimensions,
        "anomalies": sort_anomalies(combined),
        "outlier_months": sorted(combined_outliers, key=lambda o: (-abs(o["deviation"]), o["date"])),
        "params": {
            "method": "pelt",
            "model": DEFAULT_MODEL,
            "min_size": DEFAULT_MIN_SIZE,
            "penalty_mode": "fixed" if penalty is not None else "scaled",
            "penalty_factor": None if penalty is not None else penalty_factor,
            "penalty": penalty,
            "min_delta": min_delta,
            "min_reviews_per_month": MIN_REVIEWS_PER_MONTH,
            "outlier_sigma_factor": OUTLIER_SIGMA_FACTOR,
            "outlier_min_delta": OUTLIER_MIN_DELTA,
            "outlier_neighbours": OUTLIER_NEIGHBOURS,
        },
    }
    if status is not None:
        result["status"] = status
    return result


__all__ = [
    "DEFAULT_MIN_DELTA", "SEVERITY_HIGH", "OUTLIER_SIGMA_FACTOR", "OUTLIER_MIN_DELTA", "OUTLIER_NEIGHBOURS", "detect_outlier_months",
    "STABILITY_GRID", "STABILITY_TOLERANCE_MONTHS", "stability_of_anomalies",
    "eligibility", "detection_params", "sort_anomalies", "detect_anomalies", "company_anomalies",
    "company_anomalies_all",
]
