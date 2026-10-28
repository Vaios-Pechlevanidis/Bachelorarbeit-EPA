# Hinweis: Teile dieser Datei wurden mit Claude Code (Anthropic) erstellt.
# Unterstützung bei der Implementierung des Prototyps im zweiten Zyklus
# (Frontend, Tests, Auswertungsskripte); Vorschlag der Referenzzeiträume
# nach dem Annotationsprotokoll (Abschnitt 3.6.1)

import pathlib
from collections import Counter

import pytest

from _helpers import TOPIC_OVERVIEW_BASE, TOPIC_OVERVIEW_CALC_BASE, response_hash, store_rows, without_quotes
from services.keyword_topic_service import (
    CANDIDATE_TOPIC_DEFINITIONS,
    EMPLOYEE_TOPIC_DEFINITIONS,
    topic_definitions_for,
    topics_in_review,
)

URL = "/api/analytics/company/{}/topic-overview"
BACKEND = pathlib.Path(__file__).resolve().parents[2]


def _get(api, company_id, **params):
    res = api.get(URL.format(company_id), params={k: v for k, v in params.items() if v is not None})
    assert res.status_code == 200, res.text
    return res.json()


class TestTopicOverviewUnchanged:

    @pytest.mark.parametrize("key", sorted(TOPIC_OVERVIEW_BASE, key=str))
    def test_identical_to_base_commit(self, api, key):
        company_id, source, start_date = key
        body = _get(api, company_id, source=source, start_date=start_date)
        assert response_hash(without_quotes(body)) == TOPIC_OVERVIEW_CALC_BASE[key]

    @pytest.mark.parametrize("key", sorted(TOPIC_OVERVIEW_BASE, key=str))
    def test_quotes_not_from_description_fields(self, api, key):
        company_id, source, start_date = key
        for topic in _get(api, company_id, source=source, start_date=start_date)["topics"]:
            for detail in topic.get("reviewDetails") or []:
                fr = detail.get("fullReview") or {}
                preview = (detail.get("preview") or "").strip()
                own = " ".join(fr.get(k) or "" for k in ("titel", "gut_am_arbeitgeber", "schlecht_am_arbeitgeber", "verbesserungsvorschlaege"))
                if preview and preview not in own:
                    for field in ("jobbeschreibung", "stellenbeschreibung"):
                        assert preview not in (fr.get(field) or ""), (topic["topic"], field)

    def test_route_uses_service(self):
        import routes.analytics as analytics
        import services.keyword_topic_service as kts

        assert analytics.analyze_topic is kts.analyze_topic

    def test_no_service_imports_a_route(self):
        offenders = [
            p.name for p in (BACKEND / "services").glob("*.py")
            if "from routes" in p.read_text(encoding="utf-8") or "import routes" in p.read_text(encoding="utf-8")
        ]
        assert offenders == []


class TestEndDate:

    @pytest.mark.parametrize("source", ["employee", "candidates"])
    def test_end_date_limits_reviews_inclusive(self, api, source):
        rows = store_rows(source, 3)
        end = sorted(str(r["datum"]) for r in rows)[len(rows) // 2]
        body = _get(api, 3, source=source, end_date=end)
        assert body["total_reviews"] == sum(1 for r in rows if str(r["datum"]) <= end)
        assert body["total_reviews"] < len(rows)

    def test_start_and_end_date_together(self, api):
        rows = store_rows("employee", 3)
        body = _get(api, 3, source="employee", start_date="2023-01-01", end_date="2023-06-30")
        assert body["total_reviews"] == sum(1 for r in rows if "2023-01-01" <= str(r["datum"]) <= "2023-06-30")

    def test_timeline_ends_at_end_date(self, api):
        body = _get(api, 3, source="employee", end_date="2023-06-30")
        for topic in body["topics"]:
            assert all((p["year"], p["monthNum"]) <= (2023, 6) for p in topic["timelineData"])

    def test_reads_all_rows_over_several_pages(self, api, monkeypatch):
        import services.review_service as rv

        full = _get(api, 3, source="employee")
        monkeypatch.setattr(rv, "PAGE_SIZE", 37)
        paged = _get(api, 3, source="employee")
        assert paged["total_reviews"] == len(store_rows("employee", 3)) > 37 * 10
        assert response_hash(paged) == response_hash(full)

    def test_invalid_end_date_gives_400(self, api):
        res = api.get(URL.format(3), params={"end_date": "30.06.2023"})
        assert res.status_code == 400 and "end_date" in res.json()["detail"]


class TestTopicsInReview:

    @pytest.mark.parametrize("company_id", [1, 2, 3])
    @pytest.mark.parametrize("source", ["employee", "candidates"])
    def test_counts_match_topic_overview(self, api, company_id, source):
        body = _get(api, company_id, source=source)
        expected = {t["topic"]: t["frequency"] for t in body["topics"]}
        counted = Counter(t for r in store_rows(source, company_id) for t in topics_in_review(r, source))
        assert dict(counted) == expected

    def test_definitions_per_source(self):
        assert topic_definitions_for("employee") is EMPLOYEE_TOPIC_DEFINITIONS
        assert topic_definitions_for("candidates") is CANDIDATE_TOPIC_DEFINITIONS
        assert len(EMPLOYEE_TOPIC_DEFINITIONS) == 13 and len(CANDIDATE_TOPIC_DEFINITIONS) == 10
        assert set(topic_definitions_for(None)) == set(EMPLOYEE_TOPIC_DEFINITIONS) | set(CANDIDATE_TOPIC_DEFINITIONS)

    def test_pure_function_examples(self):
        row = {"gut_am_arbeitgeber_finde_ich": "Das GEHALT ist fair.", "schlecht_am_arbeitgeber_finde_ich": "Zu viele Überstunden."}
        assert topics_in_review(row, "employee") == ["Work-Life Balance", "Gehalt & Sozialleistungen"]

    def test_no_text_no_topic(self):
        assert topics_in_review({"titel": None, "gut_am_arbeitgeber_finde_ich": 5}, "employee") == []

    def test_english_text_is_not_matched(self):
        row = {"gut_am_arbeitgeber_finde_ich": "Great salary, flexible working hours and a supportive manager."}
        assert topics_in_review(row, "employee") == []
