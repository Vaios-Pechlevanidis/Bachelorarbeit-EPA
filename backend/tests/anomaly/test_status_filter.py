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
import services.anomaly_service as svc  # noqa: E402
import services.rating_series_service as rs  # noqa: E402
from routes.anomalies import router  # noqa: E402
from services.review_service import STATUS_LABELS, normalize_status  # noqa: E402

URL = "/api/analytics/company/{}/anomalies"
DEMO_3 = 3
ALL_STATUS = [(source, status) for source, labels in STATUS_LABELS.items() for status in labels]


@pytest.fixture(scope="module")
def client(in_memory_db):
    app = FastAPI()
    app.include_router(router)
    return TestClient(app)


class TestNormalizeStatus:

    @pytest.mark.parametrize("source, raw, key", [
        ("employee", "1.0", "angestellt"), ("employee", "1", "angestellt"), ("employee", "True", "angestellt"),
        ("employee", "Angestellt", "angestellt"), ("employee", "0.0", "ex-angestellt"),
        ("employee", "False", "ex-angestellt"), ("employee", "Ex-Angestellt", "ex-angestellt"),
        ("employee", "ex angestellt", "ex-angestellt"), ("employee", None, "unbekannt"), ("employee", "  ", "unbekannt"),
        ("candidates", "hired", "eingestellt"), ("candidates", "offerDeclined", "angebot-abgelehnt"),
        ("candidates", "rejected", "abgelehnt"), ("candidates", "deferred", "zurueckgestellt"),
        ("candidates", "Bewerber", "unbekannt"), ("candidates", None, "unbekannt"),
    ])
    def test_raw_values(self, source, raw, key):
        assert normalize_status(source, raw) == key


class TestDecisionD1:
    def test_keys_unchanged(self):
        assert list(STATUS_LABELS["employee"]) == ["angestellt", "ex-angestellt", "unbekannt"]
        assert list(STATUS_LABELS["candidates"]) == [
            "eingestellt", "angebot-abgelehnt", "abgelehnt", "zurueckgestellt", "unbekannt",
        ]

    def test_label_names_the_ambiguity_of_deferred(self):
        assert STATUS_LABELS["candidates"]["zurueckgestellt"] == "Zurückgestellt oder Absage"
        assert STATUS_LABELS["candidates"]["unbekannt"] == "ohne Angabe"

    @pytest.mark.parametrize("raw, key", [
        ("True", "angestellt"), ("TRUE", "angestellt"), (" true ", "angestellt"),
        ("False", "ex-angestellt"), ("FALSE", "ex-angestellt"),
    ])
    def test_boolean_export_values_confirmed(self, raw, key):
        assert normalize_status("employee", raw) == key

    def test_deferred_and_rejected_stay_separate(self):
        assert normalize_status("candidates", "deferred") == "zurueckgestellt"
        assert normalize_status("candidates", "rejected") == "abgelehnt"

    def test_frontend_options_match_backend(self):
        path = os.path.join(os.path.dirname(__file__), "..", "..", "..", "frontend", "src", "lib", "reviewerStatus.js")
        text = open(path, encoding="utf-8").read()
        for labels in STATUS_LABELS.values():
            for key, label in labels.items():
                assert f'{{ key: "{key}", label: "{label}" }}' in text, (key, label)


class TestSeries:

    @pytest.mark.parametrize("status, raw", [("angestellt", "Angestellt"), ("ex-angestellt", "Ex-Angestellt")])
    def test_series_counts_only_group(self, in_memory_db, status, raw):
        from database.in_memory_store import _TABLES

        data = rs.monthly_series(DEMO_3, "employee", status=status)
        expected = sum(1 for r in _TABLES["employee"] if r["company_id"] == DEMO_3 and r["status"] == raw)
        assert data["status"] == status
        assert sum(m["count"] for m in data["series"]) == expected

    def test_groups_add_up(self, in_memory_db):
        total = sum(m["count"] for m in rs.monthly_series(DEMO_3, "employee")["series"])
        parts = sum(
            sum(m["count"] for m in rs.monthly_series(DEMO_3, "employee", status=s)["series"])
            for s in STATUS_LABELS["employee"]
        )
        assert parts == total

    def test_invalid_status_raises(self, in_memory_db):
        with pytest.raises(ValueError):
            rs.monthly_series(DEMO_3, "employee", status="eingestellt")


class TestDetectionPerStatus:

    @pytest.mark.parametrize("source, status", ALL_STATUS)
    def test_demo3_valid_response_per_status(self, client, source, status):
        res = client.get(URL.format(DEMO_3), params={"source": source, "status": status})
        assert res.status_code == 200
        body = res.json()
        assert body["status"] == status and body["source"] == source
        elig = body["eligibility"]
        if elig["eligible"]:
            assert body["params"]["penalty_mode"] == "scaled" and body["params"]["penalty"] > 0
            for a in body["anomalies"]:
                assert a["direction"] in ("fall", "rise") and abs(a["delta"]) >= 0.3
        else:
            assert body["anomalies"] == [] and elig["reason"]

    @pytest.mark.parametrize("source, status", ALL_STATUS)
    def test_demo3_dimension_all_per_status(self, client, source, status):
        body = client.get(URL.format(DEMO_3), params={"source": source, "status": status, "dimension": "all"}).json()
        assert body["status"] == status
        assert [d["dimension"] for d in body["dimensions"]] == rs.DIMENSIONS_BY_SOURCE[source]

    def test_detection_differs_per_group(self, in_memory_db):
        all_ = svc.company_anomalies(DEMO_3, "employee")
        cur = svc.company_anomalies(DEMO_3, "employee", status="angestellt")
        ex = svc.company_anomalies(DEMO_3, "employee", status="ex-angestellt")
        assert len({all_["params"]["penalty"], cur["params"]["penalty"], ex["params"]["penalty"]}) == 3
        assert all_["eligibility"]["evaluated_months"] >= cur["eligibility"]["evaluated_months"]
        assert cur["status"] == "angestellt" and "status" not in all_

    def test_demo3_fall_visible_in_both_employee_groups(self, in_memory_db):
        for status in ("angestellt", "ex-angestellt"):
            falls = [a for a in svc.company_anomalies(DEMO_3, "employee", status=status)["anomalies"] if a["direction"] == "fall"]
            assert any(a["date"] in ("2022-12", "2023-01", "2023-02") for a in falls), status

    def test_without_status_unchanged_shape(self, client):
        body = client.get(URL.format(DEMO_3)).json()
        assert set(body) == {"company_id", "source", "dimension", "series", "anomalies", "outlier_months", "params", "eligibility"}

    @pytest.mark.parametrize("params", [
        {"status": "eingestellt"},
        {"source": "candidates", "status": "angestellt"},
        {"status": "x", "dimension": "all"},
    ])
    def test_invalid_status_gives_400(self, client, params):
        res = client.get(URL.format(DEMO_3), params=params)
        assert res.status_code == 400 and "status" in res.json()["detail"]
