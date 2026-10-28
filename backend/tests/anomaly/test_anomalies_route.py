# Hinweis: Teile dieser Datei wurden mit Claude Code (Anthropic) erstellt.
# Unterstützung bei der Implementierung des Prototyps im zweiten Zyklus
# (Frontend, Tests, Auswertungsskripte); Vorschlag der Referenzzeiträume
# nach dem Annotationsprotokoll (Abschnitt 3.6.1)

import os
import sys

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from routes.anomalies import router  # noqa: E402
from services.rating_series_service import DIMENSIONS_BY_SOURCE  # noqa: E402

URL = "/api/analytics/company/{}/anomalies"


@pytest.fixture(scope="module")
def client(in_memory_db):
    app = FastAPI()
    app.include_router(router)
    return TestClient(app)


class TestSingleDimension:

    def test_default_response_shape(self, client):
        res = client.get(URL.format(3))
        assert res.status_code == 200
        body = res.json()
        assert set(body) == {"company_id", "source", "dimension", "series", "anomalies", "outlier_months", "params", "eligibility"}
        assert body["dimension"] == "durchschnittsbewertung"
        assert body["params"]["min_reviews_per_month"] == 5

    def test_query_parameters_are_applied(self, client):
        body = client.get(URL.format(3), params={"penalty": 1.5, "min_delta": 5}).json()
        assert body["params"]["penalty"] == 1.5 and body["params"]["min_delta"] == 5
        assert body["params"]["penalty_mode"] == "fixed"
        assert body["anomalies"] == []

    def test_default_params_fields(self, client):
        params = client.get(URL.format(3)).json()["params"]
        for key in ("penalty_mode", "penalty_factor", "noise_sigma", "penalty", "n_evaluated"):
            assert key in params
        assert params["penalty_mode"] == "scaled" and params["penalty_factor"] == 2.0

    def test_penalty_factor_is_applied(self, client):
        p2 = client.get(URL.format(3), params={"penalty_factor": 2}).json()["params"]
        p4 = client.get(URL.format(3), params={"penalty_factor": 4}).json()["params"]
        assert p4["penalty_factor"] == 4
        assert p4["penalty"] == pytest.approx(2 * p2["penalty"], rel=1e-4)

    def test_penalty_has_priority_over_factor(self, client):
        params = client.get(URL.format(3), params={"penalty": 0.5, "penalty_factor": 4}).json()["params"]
        assert params["penalty_mode"] == "fixed" and params["penalty"] == 0.5

    def test_unknown_company_is_empty_and_ineligible(self, client):
        res = client.get(URL.format(999))
        assert res.status_code == 200
        body = res.json()
        assert body["series"] == [] and body["anomalies"] == []
        assert body["eligibility"]["eligible"] is False and body["eligibility"]["reason"]


class TestErrors:

    @pytest.mark.parametrize("params", [
        {"source": "bewerber"},
        {"dimension": "gibt_es_nicht"},
        {"source": "candidates", "dimension": "kommunikation"},
        {"source": "bewerber", "dimension": "all"},
    ])
    def test_invalid_source_or_dimension_400(self, client, params):
        res = client.get(URL.format(3), params=params)
        assert res.status_code == 400
        assert isinstance(res.json()["detail"], str)

    @pytest.mark.parametrize("params", [
        {"penalty": 0}, {"penalty": -1}, {"min_delta": -0.1},
        {"penalty_factor": 0}, {"penalty_factor": -2},
    ])
    def test_out_of_range_parameters_422(self, client, params):
        res = client.get(URL.format(3), params=params)
        assert res.status_code == 422
        assert "detail" in res.json()


class TestAllDimensions:

    def test_documented_shape(self, client):
        res = client.get(URL.format(3), params={"dimension": "all"})
        assert res.status_code == 200
        body = res.json()
        assert set(body) == {"company_id", "source", "dimension", "dimensions", "anomalies", "outlier_months", "params"}
        assert body["dimension"] == "all"
        assert [d["dimension"] for d in body["dimensions"]] == DIMENSIONS_BY_SOURCE["employee"]
        for entry in body["dimensions"]:
            assert set(entry) == {"dimension", "eligibility", "anomalies", "outlier_months", "params"}
        assert len(body["anomalies"]) == sum(len(d["anomalies"]) for d in body["dimensions"])

    def test_candidates_source(self, client):
        body = client.get(URL.format(3), params={"source": "candidates", "dimension": "all"}).json()
        assert [d["dimension"] for d in body["dimensions"]] == DIMENSIONS_BY_SOURCE["candidates"]

    def test_unknown_company_all_ineligible(self, client):
        body = client.get(URL.format(999), params={"dimension": "all"}).json()
        assert body["anomalies"] == []
        assert all(not d["eligibility"]["eligible"] for d in body["dimensions"])
