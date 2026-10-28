# Hinweis: Teile dieser Datei wurden mit Claude Code (Anthropic) erstellt.
# Unterstützung bei der Implementierung des Prototyps im zweiten Zyklus
# (Frontend, Tests, Auswertungsskripte); Vorschlag der Referenzzeiträume
# nach dem Annotationsprotokoll (Abschnitt 3.6.1)

import pytest

from _helpers import REVIEWS_BASE, response_hash, store_rows

URL = "/api/analytics/company/{}/reviews"
DEMO_3 = 3


def _day(row):
    return str(row["datum"])[:10]


def _get(api, company_id=DEMO_3, **params):
    res = api.get(URL.format(company_id), params=params)
    assert res.status_code == 200, res.text
    return res.json()


class TestUnchanged:

    @pytest.mark.parametrize("key", sorted(REVIEWS_BASE, key=str))
    def test_response_identical_to_base_commit(self, api, key):
        company_id, source, limit = key
        params = {k: v for k, v in {"source": source, "limit": limit}.items() if v is not None}
        assert response_hash(_get(api, company_id, **params)) == REVIEWS_BASE[key]

    def test_old_shape(self, api):
        body = _get(api, source="employee", limit=3)
        assert set(body) == {"reviews", "total"}
        assert set(body["reviews"][0]) == {
            "id", "type", "date", "score", "title", "job_description", "positive", "negative", "improvements",
        }


class TestDateRange:

    def test_bounds_are_inclusive(self, api):
        rows = store_rows("employee", DEMO_3)
        days = sorted({_day(r) for r in rows})
        start, end = days[10], days[20]
        expected = {r["id"] for r in rows if start <= _day(r) <= end}
        body = _get(api, source="employee", start=start, end=end, limit=1000)
        got = {r["id"] for r in body["reviews"]}
        assert got == expected and body["total"] == len(expected)
        assert {_day(r) for r in rows if r["id"] in got} >= {start, end}

    def test_single_day(self, api):
        rows = store_rows("employee", DEMO_3)
        day = _day(rows[0])
        body = _get(api, source="employee", start=day, end=day, limit=1000)
        assert body["total"] == sum(1 for r in rows if _day(r) == day) >= 1

    def test_sorted_newest_first(self, api):
        dates = [r["date"] for r in _get(api, source="employee", start="2023-01-01", end="2023-12-31", limit=200)["reviews"]]
        assert dates == sorted(dates, reverse=True)

    def test_both_sources_without_source(self, api):
        n_emp = _get(api, source="employee", start="2023-01-01", end="2023-03-31")["total"]
        n_cand = _get(api, source="candidates", start="2023-01-01", end="2023-03-31")["total"]
        body = _get(api, start="2023-01-01", end="2023-03-31", limit=1000)
        assert body["total"] == n_emp + n_cand
        assert {r["type"] for r in body["reviews"]} == {"employee", "candidate"}

    @pytest.mark.parametrize("params", [
        {"start": "2023-13-01"},
        {"end": "01.02.2023"},
        {"start": "2023-06-01", "end": "2023-01-01"},
        {"source": "foo", "start": "2023-01-01"},
    ])
    def test_invalid_parameters_give_400(self, api, params):
        res = api.get(URL.format(DEMO_3), params=params)
        assert res.status_code == 400 and isinstance(res.json()["detail"], str)


class TestStatusOffsetFormat:

    @pytest.mark.parametrize("status, raw", [("angestellt", "Angestellt"), ("ex-angestellt", "Ex-Angestellt")])
    def test_status_filters_reviews(self, api, status, raw):
        rows = store_rows("employee", DEMO_3)
        body = _get(api, source="employee", status=status, format="full", limit=1000)
        assert body["total"] == sum(1 for r in rows if r["status"] == raw)
        assert {r["fullReview"]["status"] for r in body["reviews"]} == {raw}

    def test_status_unknown_is_empty_for_demo(self, api):
        assert _get(api, source="employee", status="unbekannt")["total"] == 0

    @pytest.mark.parametrize("params", [{"status": "angestellt"}, {"source": "employee", "status": "eingestellt"}])
    def test_invalid_status_gives_400(self, api, params):
        assert api.get(URL.format(DEMO_3), params=params).status_code == 400

    def test_offset_pages_do_not_overlap(self, api):
        params = {"source": "employee", "start": "2022-01-01", "end": "2025-12-31"}
        whole = [r["id"] for r in _get(api, **params, limit=60)["reviews"]]
        pages = [r["id"] for off in (0, 20, 40) for r in _get(api, **params, offset=off, limit=20)["reviews"]]
        assert pages == whole and len(set(pages)) == 60

    def test_offset_beyond_total(self, api):
        body = _get(api, source="employee", offset=100000)
        assert body["reviews"] == [] and body["total"] == len(store_rows("employee", DEMO_3))

    def test_format_full_items(self, api):
        from services.review_service import build_full_review

        body = _get(api, source="employee", start="2023-01-01", end="2023-01-31", format="full", limit=5)
        by_id = {r["id"]: r for r in store_rows("employee", DEMO_3)}
        for item in body["reviews"]:
            assert set(item) == {"id", "preview", "fullReview", "topics"}
            assert item["fullReview"] == build_full_review(by_id[item["id"]])
            assert item["fullReview"]["sourceType"] == "Mitarbeiter"
            assert 0 < len(item["preview"]) <= 240

    def test_format_full_candidates(self, api):
        item = _get(api, source="candidates", format="full", limit=1)["reviews"][0]
        assert item["fullReview"]["sourceType"] == "Bewerber" and item["preview"]

    def test_invalid_format_rejected(self, api):
        res = api.get(URL.format(DEMO_3), params={"format": "kurz"})
        assert res.status_code == 422 and "detail" in res.json()


class TestPagination:

    def test_all_rows_over_several_pages(self, api, monkeypatch):
        import services.review_service as rv

        monkeypatch.setattr(rv, "PAGE_SIZE", 37)
        n = len(store_rows("employee", DEMO_3))
        body = _get(api, source="employee", start="2000-01-01", end="2030-12-31", limit=n)
        assert body["total"] == n > 37 * 10
        assert len({r["id"] for r in body["reviews"]}) == n
