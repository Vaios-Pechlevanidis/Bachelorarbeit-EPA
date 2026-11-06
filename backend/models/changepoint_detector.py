from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import Any, Dict, List, Optional, Protocol, Sequence, runtime_checkable

import numpy as np

DEFAULT_MODEL = "l2"
DEFAULT_MIN_SIZE = 3
DEFAULT_PENALTY = 0.5
DEFAULT_PENALTY_FACTOR = 2.0
MIN_NOISE_SIGMA = 0.05
DEFAULT_WINDOW = 3
DEFAULT_THRESHOLD = 0.3
WEIGHTING_NONE = "none"
WEIGHTING_COUNT = "count"
WEIGHTINGS = (WEIGHTING_NONE, WEIGHTING_COUNT)
DEFAULT_WEIGHTING = WEIGHTING_NONE
DEFAULT_REVIEW_SD = 1.0
MIN_REVIEW_SD = 0.1


@runtime_checkable
class ChangePointDetector(Protocol):
    name: str

    @property
    def min_length(self) -> int:
        ...

    def params(self) -> Dict[str, Any]:
        ...

    def detect(self, values: Sequence[float]) -> List[int]:
        ...


@dataclass(frozen=True)
class DetectionResult:
    indices: List[int]
    method: str
    params: Dict[str, Any] = field(default_factory=dict)
    weights: Optional[List[float]] = None


def noise_sigma(values: Sequence[float], floor: float = MIN_NOISE_SIGMA) -> float:
    x = np.asarray(list(values), dtype=float)
    if x.size < 2:
        return float(floor)
    d = np.diff(x)
    mad = float(np.median(np.abs(d - np.median(d))))
    return float(max(floor, 1.4826 * mad / np.sqrt(2.0)))


def scaled_penalty(values: Sequence[float], factor: float = DEFAULT_PENALTY_FACTOR) -> Dict[str, float]:
    n = len(values)
    sigma = noise_sigma(values)
    return {"penalty": float(factor * sigma ** 2 * np.log(max(n, 2))), "noise_sigma": sigma, "n": n}


def _mad_scale(x: np.ndarray) -> float:
    return float(1.4826 * np.median(np.abs(x - np.median(x))))


def check_weighting(weighting: str) -> str:
    if weighting not in WEIGHTINGS:
        raise ValueError(f"weighting muss eines von {WEIGHTINGS} sein, nicht {weighting!r}.")
    return weighting


def _counts_array(counts: Sequence[float], n: int) -> np.ndarray:
    if counts is None or len(counts) != n:
        raise ValueError("Für weighting='count' braucht jede bewertete Monatsstelle eine Anzahl (counts, gleiche Länge wie values).")
    c = np.asarray(list(counts), dtype=float)
    if np.any(~np.isfinite(c)) or np.any(c < 1):
        raise ValueError("counts müssen endliche Zahlen ≥ 1 sein.")
    return c


def between_month_sd(values: Sequence[float], counts: Sequence[float], review_sd: float) -> float:
    x = np.asarray(list(values), dtype=float)
    if x.size < 3:
        return 0.0
    n = _counts_array(counts, x.size)
    d = np.diff(x)
    h = 1.0 / n[1:] + 1.0 / n[:-1]
    s2 = float(review_sd) ** 2

    def scale(t2: float) -> float:
        return _mad_scale(d / np.sqrt(2.0 * t2 + s2 * h))

    if scale(0.0) <= 1.0:
        return 0.0
    lo, hi = 0.0, _mad_scale(d) ** 2 / 2.0
    for _ in range(60):
        mid = (lo + hi) / 2.0
        if scale(mid) > 1.0:
            lo = mid
        else:
            hi = mid
    return float(np.sqrt((lo + hi) / 2.0))


def month_weights(counts: Sequence[float], review_sd: float, between_sd: float) -> np.ndarray:
    n = np.asarray(list(counts), dtype=float)
    return 1.0 / (float(between_sd) ** 2 + float(review_sd) ** 2 / n)


def weighted_l2_cost(weights: Sequence[float]):
    from ruptures.base import BaseCost

    w = np.asarray(list(weights), dtype=float)

    class WeightedL2Cost(BaseCost):
        model = "weighted_l2"
        min_size = 1

        def fit(self, signal):
            self.signal = np.asarray(signal, dtype=float).reshape(-1, 1)
            x = self.signal.reshape(-1)
            if x.size != w.size:
                raise ValueError("Gewichte und Signal haben unterschiedliche Länge.")
            x = x - float(np.sum(w * x) / np.sum(w))
            self._cw = np.concatenate([[0.0], np.cumsum(w)])
            self._cwx = np.concatenate([[0.0], np.cumsum(w * x)])
            self._cwx2 = np.concatenate([[0.0], np.cumsum(w * x * x)])
            return self

        def error(self, start, end):
            sw = self._cw[end] - self._cw[start]
            if sw <= 0:
                return 0.0
            swx = self._cwx[end] - self._cwx[start]
            swx2 = self._cwx2[end] - self._cwx2[start]
            return float(max(swx2 - swx * swx / sw, 0.0))

    return WeightedL2Cost()


@dataclass(frozen=True)
class PeltDetector:
    model: str = DEFAULT_MODEL
    min_size: int = DEFAULT_MIN_SIZE
    penalty: Optional[float] = None
    penalty_factor: float = DEFAULT_PENALTY_FACTOR
    jump: int = 1
    noise_sigma: Optional[float] = None
    resolved: bool = False
    name: str = "pelt"
    weighting: str = DEFAULT_WEIGHTING
    review_sd: Optional[float] = None
    between_sd: Optional[float] = None
    weights: Optional[tuple] = None

    def __post_init__(self) -> None:
        check_weighting(self.weighting)

    @property
    def min_length(self) -> int:
        return 2 * self.min_size

    @property
    def penalty_mode(self) -> str:
        return "fixed" if self.penalty is not None and not self.resolved else "scaled"

    @property
    def weighted(self) -> bool:
        return self.weighting == WEIGHTING_COUNT

    def for_series(self, values: Sequence[float], counts: Optional[Sequence[float]] = None) -> "PeltDetector":
        if self.weighted:
            return self._for_series_weighted(values, counts)
        sigma = noise_sigma(values)
        if self.penalty is not None and not self.resolved:
            return replace(self, noise_sigma=sigma)
        if self.resolved:
            return self
        pen = scaled_penalty(values, self.penalty_factor)["penalty"]
        return replace(self, penalty=pen, noise_sigma=sigma, resolved=True)

    def _for_series_weighted(self, values: Sequence[float], counts: Optional[Sequence[float]]) -> "PeltDetector":
        if self.weights is not None and len(self.weights) == len(values):
            return self
        n = _counts_array(counts, len(values))
        s = max(float(self.review_sd if self.review_sd is not None else DEFAULT_REVIEW_SD), MIN_REVIEW_SD)
        tau = between_month_sd(values, n, s)
        w = tuple(float(v) for v in month_weights(n, s, tau))
        common = {"noise_sigma": noise_sigma(values), "review_sd": s, "between_sd": tau, "weights": w}
        if self.penalty is not None and not self.resolved:
            return replace(self, **common)
        pen = float(self.penalty_factor * np.log(max(len(values), 2)))
        return replace(self, penalty=pen, resolved=True, **common)

    def params(self) -> Dict[str, Any]:
        out = {
            "model": self.model,
            "min_size": self.min_size,
            "penalty": None if self.penalty is None else round(float(self.penalty), 6),
            "penalty_mode": self.penalty_mode,
            "penalty_factor": self.penalty_factor if self.penalty_mode == "scaled" else None,
            "noise_sigma": None if self.noise_sigma is None else round(float(self.noise_sigma), 6),
            "jump": self.jump,
        }
        if self.weighted:
            out.update({
                "weighting": self.weighting,
                "review_sd": None if self.review_sd is None else round(float(self.review_sd), 6),
                "between_sd": None if self.between_sd is None else round(float(self.between_sd), 6),
            })
        return out

    def detect(self, values: Sequence[float], counts: Optional[Sequence[float]] = None) -> List[int]:
        if len(values) < self.min_length:
            return []
        if self.weighted and (self.weights is None or len(self.weights) != len(values)):
            return self.for_series(values, counts).detect(values)
        if self.penalty is None:
            return self.for_series(values, counts).detect(values, counts)
        import ruptures as rpt

        signal = np.asarray(values, dtype=float).reshape(-1, 1)
        if self.weighted:
            algo = rpt.Pelt(custom_cost=weighted_l2_cost(self.weights), min_size=self.min_size, jump=self.jump)
        else:
            algo = rpt.Pelt(model=self.model, min_size=self.min_size, jump=self.jump)
        breakpoints = algo.fit(signal).predict(pen=self.penalty)
        return [int(b) for b in breakpoints if 0 < b < len(values)]


@dataclass(frozen=True)
class MovingMeanDetector:
    window: int = DEFAULT_WINDOW
    threshold: float = DEFAULT_THRESHOLD
    name: str = "moving_mean"

    @property
    def min_length(self) -> int:
        return 2 * self.window

    def params(self) -> Dict[str, Any]:
        return {"window": self.window, "threshold": self.threshold}

    def detect(self, values: Sequence[float]) -> List[int]:
        n, w = len(values), self.window
        if w < 1 or n < self.min_length:
            return []
        x = np.asarray(values, dtype=float)
        diffs = {i: float(x[i:i + w].mean() - x[i - w:i].mean()) for i in range(w, n - w + 1)}
        candidates = sorted(
            (i for i, d in diffs.items() if abs(d) >= self.threshold),
            key=lambda i: (-abs(diffs[i]), i),
        )
        chosen: List[int] = []
        for i in candidates:
            if all(abs(i - j) >= w for j in chosen):
                chosen.append(i)
        return sorted(chosen)


def detect_changepoints(
    values: Sequence[float],
    detector: Optional[ChangePointDetector] = None,
    fallback: Optional[ChangePointDetector] = None,
    counts: Optional[Sequence[float]] = None,
) -> DetectionResult:
    detector = detector or PeltDetector()
    fallback = fallback or MovingMeanDetector()
    if any(v is None for v in values):
        raise ValueError("values darf keine Lücken (None) enthalten; nur bewertete Monate übergeben.")
    chosen = detector if len(values) >= detector.min_length else fallback
    if hasattr(chosen, "for_series"):
        chosen = chosen.for_series(values) if counts is None else chosen.for_series(values, counts)
    weights = getattr(chosen, "weights", None)
    return DetectionResult(indices=chosen.detect(values), method=chosen.name, params=chosen.params(),
                           weights=list(weights) if weights is not None else None)


def _mean(values: Sequence[float], weights: Optional[Sequence[float]]) -> float:
    if weights is None:
        return float(np.mean(values))
    return float(np.average(values, weights=weights))


def level_shifts(values: Sequence[float], indices: Sequence[int],
                 weights: Optional[Sequence[float]] = None) -> List[Dict[str, Any]]:
    if weights is not None and len(weights) != len(values):
        raise ValueError("weights und values haben unterschiedliche Länge.")
    bounds = [0] + list(indices) + [len(values)]
    shifts: List[Dict[str, Any]] = []
    for k, idx in enumerate(indices, start=1):
        before = values[bounds[k - 1]:idx]
        after = values[idx:bounds[k + 1]]
        w_before = None if weights is None else weights[bounds[k - 1]:idx]
        w_after = None if weights is None else weights[idx:bounds[k + 1]]
        before_mean = _mean(before, w_before)
        after_mean = _mean(after, w_after)
        shifts.append({
            "index": int(idx),
            "before_start": bounds[k - 1],
            "after_end": bounds[k + 1],
            "before_mean": before_mean,
            "after_mean": after_mean,
            "delta": after_mean - before_mean,
        })
    return shifts


__all__ = [
    "DEFAULT_MODEL", "DEFAULT_MIN_SIZE", "DEFAULT_PENALTY", "DEFAULT_PENALTY_FACTOR", "MIN_NOISE_SIGMA",
    "DEFAULT_WINDOW", "DEFAULT_THRESHOLD", "noise_sigma", "scaled_penalty",
    "WEIGHTING_NONE", "WEIGHTING_COUNT", "WEIGHTINGS", "DEFAULT_WEIGHTING", "DEFAULT_REVIEW_SD", "MIN_REVIEW_SD",
    "check_weighting", "between_month_sd", "month_weights", "weighted_l2_cost",
    "ChangePointDetector", "DetectionResult", "PeltDetector", "MovingMeanDetector",
    "detect_changepoints", "level_shifts",
]
