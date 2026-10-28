# Hinweis: Teile dieser Datei wurden mit Claude Code (Anthropic) erstellt.
# Unterstützung bei der Implementierung des Prototyps im zweiten Zyklus
# (Frontend, Tests, Auswertungsskripte); Vorschlag der Referenzzeiträume
# nach dem Annotationsprotokoll (Abschnitt 3.6.1)

import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from _helpers import analytics_client  # noqa: E402


@pytest.fixture(autouse=True)
def no_evidence_fetch(tmp_path, monkeypatch):
    import services.evidence_service as ev

    monkeypatch.setenv(ev.LIVE_FETCH_ENV, "0")
    monkeypatch.setattr(ev, "STORE_DIR", tmp_path / "belege")
    monkeypatch.setattr(ev, "GLOBAL_EVENTS_PATH", tmp_path / "keine_ereignisse.json")


@pytest.fixture(scope="module")
def api(in_memory_db):
    with pytest.MonkeyPatch.context() as mp:
        yield analytics_client(mp, in_memory_db)


@pytest.fixture(scope="module")
def lexicon_analyzer():
    from models.sentiment_analyzer import SentimentAnalyzer
    from services import explanation_service

    analyzer = SentimentAnalyzer(mode="lexicon")
    explanation_service.set_sentiment_analyzer(analyzer)
    yield analyzer
    explanation_service.set_sentiment_analyzer(None)
