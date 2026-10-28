# Hinweis: Teile dieser Datei wurden mit Claude Code (Anthropic) erstellt.
# Unterstützung bei der Implementierung des Prototyps im zweiten Zyklus
# (Frontend, Tests, Auswertungsskripte); Vorschlag der Referenzzeiträume
# nach dem Annotationsprotokoll (Abschnitt 3.6.1)

import math
import pytest
from datetime import datetime

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from routes.analytics import calculate_forecast, _fallback_forecast_average


def _make_historical(scores: list[float], start_year: int = 2023, start_month: int = 1) -> list[dict]:
    data = []
    for i, score in enumerate(scores):
        month_offset = start_month + i
        year = start_year + (month_offset - 1) // 12
        month = ((month_offset - 1) % 12) + 1
        date_obj = datetime(year, month, 1)
        data.append({
            "date": date_obj.strftime("%Y-%m"),
            "date_display": date_obj.strftime("%b %Y"),
            "score": round(score, 2),
            "count": 10,
            "is_forecast": False
        })
    return data


def calc_mae(actual: list[float], predicted: list[float]) -> float:
    return sum(abs(a - p) for a, p in zip(actual, predicted)) / len(actual)


FULL_SERIES = [
    3.10, 3.15, 3.20, 3.25, 3.18, 3.30, 3.35, 3.28, 3.40, 3.45, 3.50, 3.55,
    3.58, 3.60, 3.55, 3.65, 3.70, 3.68, 3.72, 3.75, 3.78, 3.80, 3.82, 3.85
]
TEST_MONTHS = 6
ACTUAL_SCORES = FULL_SERIES[-TEST_MONTHS:]


class TestMinimumDataPoints:
    def test_minimum_2_points_produces_forecast(self):
        data = _make_historical(FULL_SERIES[:2])
        result = calculate_forecast(data, 3)
        assert len(result) == 3, "2 Datenpunkte müssen eine Prognose liefern"
        print(f"\n✓ 2 Datenpunkte → Prognose möglich ({len(result)} Monate)")

    def test_1_point_returns_empty(self):
        data = _make_historical(FULL_SERIES[:1])
        result = calculate_forecast(data, 3)
        assert result == [], "1 Datenpunkt darf keine Prognose liefern"
        print(f"\n✓ 1 Datenpunkt → keine Prognose (korrekt)")

    @pytest.mark.parametrize("n_train", [2, 3, 4, 6, 8, 10, 12, 15, 18])
    def test_mae_decreases_with_more_data(self, n_train):
        train_end = len(FULL_SERIES) - TEST_MONTHS
        if n_train > train_end:
            pytest.skip(f"Nicht genug Daten für {n_train} Trainingsmonate")

        train_scores = FULL_SERIES[train_end - n_train:train_end]
        train_data = _make_historical(train_scores)
        result = calculate_forecast(train_data, TEST_MONTHS)
        predicted = [e["score"] for e in result]
        mae = calc_mae(ACTUAL_SCORES, predicted)

        assert mae < 1.0, f"MAE {mae:.4f} bei {n_train} Trainingspunkten zu hoch"
        print(f"\n✓ {n_train:2d} Monate Training → MAE: {mae:.4f}")

    def test_quality_threshold_analysis(self):
        train_end = len(FULL_SERIES) - TEST_MONTHS
        results = []

        for n_train in range(2, train_end + 1):
            train_scores = FULL_SERIES[train_end - n_train:train_end]
            train_data = _make_historical(train_scores)
            result = calculate_forecast(train_data, TEST_MONTHS)
            predicted = [e["score"] for e in result]
            mae = calc_mae(ACTUAL_SCORES, predicted)
            results.append((n_train, round(mae, 4)))

        first_under_03 = next((n for n, m in results if m < 0.3), None)
        first_under_01 = next((n for n, m in results if m < 0.1), None)

        print(f"\n✓ Qualitätsschwellen-Analyse:")
        print(f"  {'Monate':>8s} | {'MAE':>8s} | Qualität")
        print(f"  {'─' * 35}")
        for n, mae in results:
            quality = "⬛ Exzellent" if mae < 0.1 else ("🟩 Gut" if mae < 0.3 else ("🟨 Akzeptabel" if mae < 0.5 else "🟥 Ungenügend"))
            print(f"  {n:>8d} | {mae:>8.4f} | {quality}")
        print()
        if first_under_03:
            print(f"  → MAE < 0.3 ab {first_under_03} Monat(en)")
        if first_under_01:
            print(f"  → MAE < 0.1 ab {first_under_01} Monat(en)")
        print(f"  → Empfehlung: Mindestens {first_under_03 or 'N/A'} Monate für zuverlässige Prognose")


class TestDatabaseStatistics:
    def test_count_companies_with_data(self):
        from database.supabase_client import get_supabase_client
        from collections import defaultdict

        supabase = get_supabase_client()

        employee_resp = supabase.table("employee") \
            .select("company_id") \
            .execute()

        candidates_resp = supabase.table("candidates") \
            .select("company_id") \
            .execute()

        employee_companies = set(r["company_id"] for r in (employee_resp.data or []) if r.get("company_id"))
        candidate_companies = set(r["company_id"] for r in (candidates_resp.data or []) if r.get("company_id"))
        all_companies = employee_companies | candidate_companies

        assert len(all_companies) > 0, "Keine Unternehmen in der Datenbank gefunden"

        print(f"\n✓ Unternehmen in der Datenbank:")
        print(f"  Gesamt (unique):    {len(all_companies)}")
        print(f"  Mit Mitarbeiter:    {len(employee_companies)}")
        print(f"  Mit Bewerber:       {len(candidate_companies)}")
        print(f"  Beide Quellen:      {len(employee_companies & candidate_companies)}")

    def test_monthly_coverage_per_company(self):
        from database.supabase_client import get_supabase_client
        from collections import defaultdict

        supabase = get_supabase_client()

        employee_resp = supabase.table("employee") \
            .select("company_id, datum") \
            .not_.is_("datum", "null") \
            .execute()

        candidates_resp = supabase.table("candidates") \
            .select("company_id, datum") \
            .not_.is_("datum", "null") \
            .execute()

        company_months = defaultdict(set)
        for r in (employee_resp.data or []) + (candidates_resp.data or []):
            if r.get("company_id") and r.get("datum"):
                try:
                    date = datetime.fromisoformat(r["datum"].replace("Z", "+00:00"))
                    month_key = date.strftime("%Y-%m")
                    company_months[r["company_id"]].add(month_key)
                except (ValueError, TypeError):
                    pass

        if not company_months:
            pytest.skip("Keine Datumsdaten verfügbar")

        month_counts = [len(months) for months in company_months.values()]
        avg_months = sum(month_counts) / len(month_counts)
        min_months = min(month_counts)
        max_months = max(month_counts)
        median_months = sorted(month_counts)[len(month_counts) // 2]

        firms_with_forecast = sum(1 for c in month_counts if c >= 2)
        firms_with_good_forecast = sum(1 for c in month_counts if c >= 6)
        firms_with_excellent = sum(1 for c in month_counts if c >= 12)

        print(f"\n✓ Monatliche Abdeckung je Unternehmen:")
        print(f"  Unternehmen mit Daten: {len(company_months)}")
        print(f"  ∅ Monate:              {avg_months:.1f}")
        print(f"  Median Monate:         {median_months}")
        print(f"  Min Monate:            {min_months}")
        print(f"  Max Monate:            {max_months}")
        print()
        print(f"  Prognose möglich (≥2 Monate):      {firms_with_forecast}/{len(company_months)} ({firms_with_forecast/len(company_months)*100:.0f}%)")
        print(f"  Gute Prognose (≥6 Monate):         {firms_with_good_forecast}/{len(company_months)} ({firms_with_good_forecast/len(company_months)*100:.0f}%)")
        print(f"  Exzellente Prognose (≥12 Monate):  {firms_with_excellent}/{len(company_months)} ({firms_with_excellent/len(company_months)*100:.0f}%)")

    def test_total_review_count(self):
        from database.supabase_client import get_supabase_client

        supabase = get_supabase_client()

        employee_resp = supabase.table("employee") \
            .select("id", count="exact") \
            .execute()

        candidates_resp = supabase.table("candidates") \
            .select("id", count="exact") \
            .execute()

        employee_count = employee_resp.count if employee_resp.count else len(employee_resp.data or [])
        candidates_count = candidates_resp.count if candidates_resp.count else len(candidates_resp.data or [])

        assert employee_count + candidates_count > 0, "Keine Bewertungen in der Datenbank"

        print(f"\n✓ Bewertungen in der Datenbank:")
        print(f"  Mitarbeiter:  {employee_count:,}")
        print(f"  Bewerber:     {candidates_count:,}")
        print(f"  Gesamt:       {employee_count + candidates_count:,}")


def run_all_tests():
    print("=" * 75)
    print("PROGNOSE-ENGINE — DATENBASIS-ANALYSE")
    print("=" * 75)

    print(f"\n{'─' * 75}")
    print("  TEIL 1: Mindestanzahl Datenpunkte")
    print(f"{'─' * 75}")

    test = TestMinimumDataPoints()
    test.test_minimum_2_points_produces_forecast()
    test.test_1_point_returns_empty()
    test.test_quality_threshold_analysis()

    print(f"\n{'─' * 75}")
    print("  TEIL 2: Datenbasis-Statistik (Datenbank)")
    print(f"{'─' * 75}")

    try:
        db_test = TestDatabaseStatistics()
        db_test.test_count_companies_with_data()
        db_test.test_monthly_coverage_per_company()
        db_test.test_total_review_count()
    except Exception as e:
        print(f"\n⚠ Datenbankabfrage fehlgeschlagen: {e}")
        print("  (Stellen Sie sicher, dass .env konfiguriert ist)")

    print(f"\n{'=' * 75}")


if __name__ == "__main__":
    run_all_tests()
