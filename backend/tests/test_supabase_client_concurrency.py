# Hinweis: Teile dieser Datei wurden mit Claude Code (Anthropic) erstellt.
# Unterstützung bei der Implementierung des Prototyps im zweiten Zyklus
# (Frontend, Tests, Auswertungsskripte); Vorschlag der Referenzzeiträume
# nach dem Annotationsprotokoll (Abschnitt 3.6.1)

import importlib
import os
import sys
import threading
from concurrent.futures import ThreadPoolExecutor

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import supabase as supabase_pkg  # noqa: E402

import database.supabase_client as supabase_client_module  # noqa: E402
import routes.companies as companies_module  # noqa: E402
from database.in_memory_store import get_in_memory_client  # noqa: E402

N_THREADS = 8


class _ThreadAffineClient:
    def __init__(self, inner):
        self._inner = inner
        self.owner = threading.get_ident()

    def _check_thread(self):
        if threading.get_ident() != self.owner:
            raise RuntimeError("Client wird von einem fremden Thread benutzt")

    def table(self, name):
        self._check_thread()
        return self._inner.table(name)

    def rpc(self, func, params):
        self._check_thread()
        return self._inner.rpc(func, params)


@pytest.fixture
def hosted_client_module(monkeypatch):
    created = []

    def fake_create_client(url, key):
        client = _ThreadAffineClient(get_in_memory_client())
        created.append(client)
        return client

    monkeypatch.setenv("SUPABASE_URL", "http://fake.invalid")
    monkeypatch.setenv("SUPABASE_KEY", "fake-key")
    monkeypatch.setenv("SUPABASE_SERVICE_KEY", "fake-key")
    monkeypatch.setattr(supabase_pkg, "create_client", fake_create_client)
    module = importlib.reload(supabase_client_module)
    monkeypatch.setattr(companies_module, "get_supabase_client", module.get_supabase_client)
    yield module, created
    monkeypatch.undo()
    importlib.reload(supabase_client_module)


def _run_concurrently(fn, n=N_THREADS):
    barrier = threading.Barrier(n)

    def call():
        barrier.wait()
        return fn()

    with ThreadPoolExecutor(max_workers=n) as pool:
        futures = [pool.submit(call) for _ in range(n)]
        return [f.result() for f in futures]


def test_get_supabase_client_returns_one_client_per_thread(hosted_client_module):
    module, created = hosted_client_module

    clients = _run_concurrently(module.get_supabase_client)

    assert len(created) == N_THREADS
    assert len({id(c) for c in clients}) == N_THREADS
    assert module.get_supabase_client() is module.get_supabase_client()


def test_get_companies_runs_concurrently_without_errors(hosted_client_module):
    module, _ = hosted_client_module
    expected = companies_module.get_companies()

    results = _run_concurrently(companies_module.get_companies)

    assert all(r == expected for r in results)
    assert expected


def test_shared_client_reproduces_the_original_failure(monkeypatch):
    shared = _ThreadAffineClient(get_in_memory_client())
    monkeypatch.setattr(companies_module, "get_supabase_client", lambda: shared)

    with pytest.raises(RuntimeError, match="fremden Thread"):
        _run_concurrently(companies_module.get_companies)
