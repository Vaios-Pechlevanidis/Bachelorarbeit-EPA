# Hinweis: Teile dieser Datei wurden mit Claude Code (Anthropic) erstellt.
# Unterstützung bei der Implementierung des Prototyps im zweiten Zyklus
# (Frontend, Tests, Auswertungsskripte); Vorschlag der Referenzzeiträume
# nach dem Annotationsprotokoll (Abschnitt 3.6.1)

import math
import os
import sys

import numpy as np
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from models.changepoint_detector import (  # noqa: E402
    DEFAULT_REVIEW_SD,
    WEIGHTING_COUNT,
    WEIGHTING_NONE,
    PeltDetector,
    between_month_sd,
    check_weighting,
    detect_changepoints,
    level_shifts,
    month_weights,
    weighted_l2_cost,
)
from services.anomaly_service import detect_anomalies, detection_params  # noqa: E402
from services.rating_series_service import review_sd  # noqa: E402


def _months(n: int, start_year: int = 2015):
    return [f"{start_year + i // 12:04d}-{i % 12 + 1:02d}" for i in range(n)]


def _series(means, counts):
    return [{"period": p, "mean": round(float(m), 3), "count": int(c), "n_values": int(c), "evaluated": c >= 5}
            for p, m, c in zip(_months(len(means)), means, counts)]


def _sampled(levels, counts, sd=1.0, tau=0.0, seed=0):
    rng = np.random.default_rng(seed)
    return [lvl + rng.normal(0, tau) + rng.normal(0, sd / math.sqrt(n)) for lvl, n in zip(levels, counts)]


def test_check_weighting_rejects_unknown():
    assert check_weighting(WEIGHTING_COUNT) == WEIGHTING_COUNT
    with pytest.raises(ValueError):
        check_weighting("bewertungen")
    with pytest.raises(ValueError):
        PeltDetector(weighting="x")


def test_month_weights_formula():
    w = month_weights([5, 20], review_sd=1.0, between_sd=0.2)
    assert w[0] == pytest.approx(1 / (0.04 + 1 / 5))
    assert w[1] == pytest.approx(1 / (0.04 + 1 / 20))
    assert w[1] > w[0]


def test_between_month_sd_zero_for_pure_sampling_noise():
    counts = [5, 40, 8, 60, 12, 6, 30, 9, 50, 7] * 8
    values = _sampled([3.5] * len(counts), counts, sd=1.0, tau=0.0, seed=1)
    assert between_month_sd(values, counts, 1.0) < 0.12


def test_between_month_sd_recovers_extra_noise():
    counts = [40] * 200
    values = _sampled([3.5] * 200, counts, sd=1.0, tau=0.3, seed=2)
    assert between_month_sd(values, counts, 1.0) == pytest.approx(0.3, abs=0.08)


def test_weighted_cost_equals_l2_with_equal_weights():
    x = np.array([3.0, 3.2, 2.9, 4.1, 4.0, 3.8])
    cost = weighted_l2_cost([2.0] * 6).fit(x.reshape(-1, 1))
    seg = x[1:5]
    assert cost.error(1, 5) == pytest.approx(2.0 * float(((seg - seg.mean()) ** 2).sum()))
    assert cost.signal.shape == (6, 1)


def test_weighted_needs_counts():
    with pytest.raises(ValueError):
        PeltDetector(weighting=WEIGHTING_COUNT).detect([3.0] * 12)
    with pytest.raises(ValueError):
        PeltDetector(weighting=WEIGHTING_COUNT).detect([3.0] * 12, counts=[5] * 11)


def test_default_params_unchanged():
    det = PeltDetector().for_series([3.0, 3.1, 2.9, 3.0, 3.2, 3.1, 3.0])
    assert "weighting" not in det.params()
    assert det.weighting == WEIGHTING_NONE


def test_weighted_params_and_penalty():
    values = [3.0, 3.1, 2.9, 3.0, 3.2, 3.1, 3.0, 2.95]
    det = PeltDetector(weighting=WEIGHTING_COUNT).for_series(values, [10] * 8)
    p = det.params()
    assert p["weighting"] == WEIGHTING_COUNT
    assert p["review_sd"] == pytest.approx(DEFAULT_REVIEW_SD)
    assert p["penalty"] == pytest.approx(2.0 * math.log(8), abs=1e-6)
    assert p["penalty_mode"] == "scaled"
    fixed = PeltDetector(weighting=WEIGHTING_COUNT, penalty=4.0).for_series(values, [10] * 8)
    assert fixed.params()["penalty_mode"] == "fixed"
    assert fixed.weights is not None


def test_weighted_finds_clear_shift():
    counts = [20] * 30
    levels = [3.2] * 15 + [4.0] * 15
    values = _sampled(levels, counts, sd=1.0, tau=0.05, seed=3)
    res = detect_changepoints(values, PeltDetector(weighting=WEIGHTING_COUNT), counts=counts)
    assert res.weights is not None and len(res.weights) == 30
    assert any(abs(i - 15) <= 1 for i in res.indices)


def test_weighted_ignores_thin_month_noise():
    counts = [6, 60] * 20
    values = [3.5 + (0.9 if n == 6 and i % 4 == 0 else 0.0) for i, n in enumerate(counts)]
    found = detect_anomalies(_series(values, counts), company_id=1, source="employee",
                             weighting=WEIGHTING_COUNT, review_sd=1.0)
    assert found == []


def test_level_shifts_weighted_means():
    values = [3.0, 4.0, 5.0, 5.0]
    shifts = level_shifts(values, [2], weights=[1.0, 3.0, 1.0, 1.0])
    assert shifts[0]["before_mean"] == pytest.approx(3.75)
    assert shifts[0]["after_mean"] == pytest.approx(5.0)
    with pytest.raises(ValueError):
        level_shifts(values, [2], weights=[1.0])


def test_detect_anomalies_default_equals_explicit_none():
    counts = [8, 12, 30, 6, 9, 15] * 4
    values = _sampled([3.2] * 12 + [3.9] * 12, counts, seed=4)
    series = _series(values, counts)
    a = detect_anomalies(series, company_id=1, source="employee")
    b = detect_anomalies(series, company_id=1, source="employee", weighting=WEIGHTING_NONE)
    assert a == b


def test_detection_params_weighted():
    counts = [8, 12, 30, 6, 9, 15] * 4
    series = _series(_sampled([3.5] * 24, counts, seed=5), counts)
    p = detection_params(series, weighting=WEIGHTING_COUNT, review_sd=0.9)
    assert p["weighting"] == WEIGHTING_COUNT and p["review_sd"] == pytest.approx(0.9)
    assert "weighting" not in detection_params(series)


def test_review_sd_pooled_within_months():
    rows = [{"datum": "2020-01-05", "x": v} for v in (1, 3, 1, 3, 2)] + \
           [{"datum": "2020-02-05", "x": v} for v in (4, 4, 4, 4, 4)] + \
           [{"datum": "2020-03-05", "x": v} for v in (1, 5)]
    m1 = np.array([1, 3, 1, 3, 2], dtype=float)
    expected = math.sqrt(((m1 - m1.mean()) ** 2).sum() / 8)
    assert review_sd(rows, "x") == pytest.approx(expected)
    assert review_sd([], "x") is None
