# Hinweis: Teile dieser Datei wurden mit Claude Code (Anthropic) erstellt.
# Unterstützung bei der Implementierung des Prototyps im zweiten Zyklus
# (Frontend, Tests, Auswertungsskripte); Vorschlag der Referenzzeiträume
# nach dem Annotationsprotokoll (Abschnitt 3.6.1)

import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import database.supabase_client as supabase_client  # noqa: E402
from services import context_service  # noqa: E402

sys.path.insert(0, os.path.dirname(__file__))
from _market_helpers import COMPANIES, FakeCompaniesClient, FakeFetcher  # noqa: E402


@pytest.fixture
def fake_db(monkeypatch):
    client = FakeCompaniesClient([dict(r) for r in COMPANIES])
    monkeypatch.setattr(supabase_client, "get_supabase_client", lambda: client)
    return client


@pytest.fixture
def market(monkeypatch, tmp_path):
    fetcher = FakeFetcher()
    monkeypatch.setattr(context_service, "CACHE_DIR", tmp_path)
    monkeypatch.setattr(context_service, "fetch_raw", fetcher)
    monkeypatch.setattr(context_service, "_failed_fetches", {})
    monkeypatch.delenv(context_service.LIVE_FETCH_ENV, raising=False)
    return type("Market", (), {"fetcher": fetcher, "cache_dir": tmp_path})()
