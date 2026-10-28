from __future__ import annotations

import math
from typing import Any, Callable, Dict, List, Optional, Sequence

HORIZON = 6
MIN_TRAIN = 24
MAX_ORIGINS = 36
INTERVAL_LEVEL = 0.8
MOVING_WINDOW = 6
SEASON = 12
RATING_MIN, RATING_MAX = 0.0, 5.0

Forecaster = Callable[[Sequence[float], int], Optional[List[float]]]


def _clamp(v: float) -> float:
    return max(RATING_MIN, min(RATING_MAX, float(v)))


def holt_forecast(values: Sequence[float], steps: int) -> Optional[List[float]]:
    if steps <= 0 or len(values) < 2:
        return None
    try:
        import numpy as np
        from statsmodels.tsa.holtwinters import Holt  # type: ignore[import-untyped]

        fit = Holt(np.asarray(values, dtype=float)).fit()
        preds = fit.forecast(steps=steps)
        out = [_clamp(p) for p in preds]
        if any(not math.isfinite(p) for p in out):
            return None
        return out
    except Exception:
        return None


def naive_forecast(values: Sequence[float], steps: int) -> Optional[List[float]]:
    if steps <= 0 or not values:
        return None
    return [float(values[-1])] * steps


def mean_forecast(values: Sequence[float], steps: int) -> Optional[List[float]]:
    if steps <= 0 or not values:
        return None
    return [sum(values) / len(values)] * steps


def moving_average_forecast(values: Sequence[float], steps: int, window: int = MOVING_WINDOW) -> Optional[List[float]]:
    if steps <= 0 or not values:
        return None
    tail = list(values[-window:])
    return [sum(tail) / len(tail)] * steps


def seasonal_naive_forecast(values: Sequence[float], steps: int, season: int = SEASON) -> Optional[List[float]]:
    if steps <= 0 or len(values) < season:
        return None
    return [float(values[len(values) - season + (h % season)]) for h in range(steps)]


METHODS: Dict[str, Forecaster] = {
    "holt": holt_forecast,
    "naive": naive_forecast,
    "mean": mean_forecast,
    "ma6": moving_average_forecast,
    "snaive12": seasonal_naive_forecast,
}

METHOD_LABELS = {
    "holt": "Holt (exponentielle Glättung mit Trend)",
    "naive": "letzter Wert",
    "mean": "Mittel aller Monate",
    "ma6": "Mittel der letzten 6 Monate",
    "snaive12": "Wert 12 Monate zuvor",
}


def _summary(errors: List[float]) -> Dict[str, Optional[float]]:
    if not errors:
        return {"mae": None, "rmse": None, "n": 0}
    return {
        "mae": round(sum(abs(e) for e in errors) / len(errors), 4),
        "rmse": round(math.sqrt(sum(e * e for e in errors) / len(errors)), 4),
        "n": len(errors),
    }


def rolling_origin_backtest(
    values: Sequence[float],
    horizon: int = HORIZON,
    min_train: int = MIN_TRAIN,
    max_origins: int = MAX_ORIGINS,
    methods: Optional[Dict[str, Forecaster]] = None,
) -> Optional[Dict[str, Any]]:
    methods = methods or METHODS
    n = len(values)
    if horizon <= 0 or n < min_train + 1:
        return None
    origins = list(range(min_train, n))[-max_origins:]
    errors: Dict[str, List[float]] = {name: [] for name in methods}
    by_h: Dict[str, Dict[int, List[float]]] = {name: {h: [] for h in range(1, horizon + 1)} for name in methods}
    for t in origins:
        train = list(values[:t])
        for name, fn in methods.items():
            preds = fn(train, horizon)
            if not preds:
                continue
            for h in range(1, horizon + 1):
                idx = t + h - 1
                if idx >= n:
                    break
                err = float(values[idx]) - float(preds[h - 1])
                errors[name].append(err)
                by_h[name][h].append(err)
    result_methods: Dict[str, Any] = {}
    for name in methods:
        summary = _summary(errors[name])
        summary["mae_by_horizon"] = [
            round(sum(abs(e) for e in by_h[name][h]) / len(by_h[name][h]), 4) if by_h[name][h] else None
            for h in range(1, horizon + 1)
        ]
        summary["label"] = METHOD_LABELS.get(name, name)
        result_methods[name] = summary
    scored = [(result_methods[m]["mae"], m) for m in methods if result_methods[m]["mae"] is not None]
    best = min(scored)[1] if scored else None
    return {
        "origins": len(origins),
        "first_origin": origins[0],
        "horizon": horizon,
        "min_train": min_train,
        "methods": result_methods,
        "best_method": best,
        "residuals": {name: {h: list(v) for h, v in by_h[name].items()} for name in methods},
    }


def _quantile(sorted_values: List[float], q: float) -> float:
    if not sorted_values:
        raise ValueError("leer")
    pos = (len(sorted_values) - 1) * q
    lo, hi = int(math.floor(pos)), int(math.ceil(pos))
    if lo == hi:
        return sorted_values[lo]
    return sorted_values[lo] + (sorted_values[hi] - sorted_values[lo]) * (pos - lo)


def interval_offsets(
    backtest: Optional[Dict[str, Any]],
    method: str = "holt",
    level: float = INTERVAL_LEVEL,
    min_errors: int = 8,
) -> Dict[int, Dict[str, float]]:
    if not backtest:
        return {}
    residuals = backtest.get("residuals", {}).get(method, {})
    alpha = (1 - level) / 2
    out: Dict[int, Dict[str, float]] = {}
    low_so_far, high_so_far = None, None
    for h in sorted(int(k) for k in residuals):
        errs = residuals[h] if h in residuals else residuals[str(h)]
        if len(errs) < min_errors:
            continue
        s = sorted(float(e) for e in errs)
        raw_low, raw_high = _quantile(s, alpha), _quantile(s, 1 - alpha)
        low_so_far = raw_low if low_so_far is None else min(low_so_far, raw_low)
        high_so_far = raw_high if high_so_far is None else max(high_so_far, raw_high)
        out[h] = {
            "low": round(low_so_far, 4), "high": round(high_so_far, 4), "n": len(s),
            "raw_low": round(raw_low, 4), "raw_high": round(raw_high, 4),
        }
    return out


def public_backtest(backtest: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    if not backtest:
        return None
    return {k: v for k, v in backtest.items() if k != "residuals"}


__all__ = [
    "HORIZON", "MIN_TRAIN", "MAX_ORIGINS", "INTERVAL_LEVEL", "METHODS", "METHOD_LABELS",
    "holt_forecast", "naive_forecast", "mean_forecast", "moving_average_forecast", "seasonal_naive_forecast",
    "rolling_origin_backtest", "interval_offsets", "public_backtest",
]
