# Hinweis: Teile dieser Datei wurden mit Claude Code (Anthropic) erstellt.
# Unterstützung bei der Implementierung des Prototyps im zweiten Zyklus
# (Frontend, Tests, Auswertungsskripte); Vorschlag der Referenzzeiträume
# nach dem Annotationsprotokoll (Abschnitt 3.6.1)

import importlib
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

_ENV_KEYS = ("SUPABASE_URL", "SUPABASE_KEY", "SUPABASE_SERVICE_KEY")


@pytest.fixture(scope="module")
def in_memory_db():
    import database.supabase_client as supabase_client
    from database.in_memory_store import InMemoryClient

    with pytest.MonkeyPatch.context() as mp:
        for key in _ENV_KEYS:
            mp.setenv(key, "")
        importlib.reload(supabase_client)
        client = supabase_client.get_supabase_client()
        assert isinstance(client, InMemoryClient), "Fallback nicht aktiv; Test würde die echte DB abfragen"
        yield client
    importlib.reload(supabase_client)


@pytest.fixture(autouse=True)
def _no_macro_data(tmp_path_factory, monkeypatch):
    from services import macro_events

    def no_network(url):
        raise RuntimeError("Kein Netzabruf in Tests")

    monkeypatch.setattr(macro_events, "CACHE_PATH", tmp_path_factory.mktemp("macro") / "eurostat_de.json")
    monkeypatch.setattr(macro_events, "fetch_json", no_network)
    macro_events._failed_fetch.clear()
