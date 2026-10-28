# Hinweis: Teile dieser Datei wurden mit Claude Code (Anthropic) erstellt.
# Unterstützung bei der Implementierung des Prototyps im zweiten Zyklus
# (Frontend, Tests, Auswertungsskripte); Vorschlag der Referenzzeiträume
# nach dem Annotationsprotokoll (Abschnitt 3.6.1)

import os
import sys
import threading

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import routes.companies as companies_module  # noqa: E402
from database import in_memory_store  # noqa: E402
from database.in_memory_store import get_in_memory_client  # noqa: E402


@pytest.fixture
def in_memory(monkeypatch):
    client = get_in_memory_client()
    monkeypatch.setattr(companies_module, "get_supabase_client", lambda: client)
    return client


def _expected_counts():
    counts = {}
    for table in ("employee", "candidates"):
        for row in in_memory_store._TABLES[table]:
            counts[row["company_id"]] = counts.get(row["company_id"], 0) + 1
    return counts


def test_review_counts_match_rows_per_company(in_memory):
    expected = _expected_counts()
    data = companies_module.get_companies()
    assert len(data) == 3
    for row in data:
        assert row["review_count"] == expected[int(row["id"])]


def test_review_counts_of_unknown_company_is_zero(in_memory):
    assert companies_module._review_counts([999]) == {999: 0}


def test_counts_run_in_the_pool(monkeypatch):
    threads = set()

    def fake_count(table, company_id):
        threads.add(threading.current_thread().name)
        return 1

    monkeypatch.setattr(companies_module, "_count_reviews", fake_count)
    counts = companies_module._review_counts([1, 2, 3])
    assert counts == {1: 2, 2: 2, 3: 2}
    assert threads and all(name.startswith("review-count") for name in threads)


def test_count_error_is_raised(monkeypatch):
    def failing(table, company_id):
        raise RuntimeError("Supabase nicht erreichbar")

    monkeypatch.setattr(companies_module, "_count_reviews", failing)
    with pytest.raises(RuntimeError, match="nicht erreichbar"):
        companies_module._review_counts([1])
