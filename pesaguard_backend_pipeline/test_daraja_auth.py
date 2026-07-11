import os
import sys
from types import SimpleNamespace

import pytest

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from shared.daraja.auth_client import DarajaAuthClient


class DummyResponse:
    def __init__(self, status_code=200, json_data=None):
        self.status_code = status_code
        self._json_data = json_data or {}

    def json(self):
        return self._json_data


def test_token_is_cached_and_refreshed(monkeypatch):
    calls = []

    class DummyCache:
        def __init__(self):
            self.store = {}

        def get(self, key):
            return self.store.get(key)

        def set(self, key, value, ttl):
            self.store[key] = {"value": value, "ttl": ttl}

    def fake_fetch(*args, **kwargs):
        client = args[1] if len(args) > 1 else None
        if client is not None:
            calls.append(client.tenant_id)
        return {"access_token": "token-1", "expires_in": 3600}

    client = DarajaAuthClient(tenant_id="tenant-a", credentials={"consumer_key": "k", "consumer_secret": "s"}, cache=DummyCache())
    monkeypatch.setattr(client, "_fetch_access_token", fake_fetch)

    first = client.get_access_token()
    second = client.get_access_token()

    assert first == "token-1"
    assert second == "token-1"
    assert len(calls) == 1


def test_401_triggers_refresh(monkeypatch):
    responses = iter([
        DummyResponse(status_code=401, json_data={"error": "expired"}),
        DummyResponse(status_code=200, json_data={"access_token": "token-2", "expires_in": 3600}),
    ])

    class DummySession:
        def post(self, url, auth=None, timeout=None):
            return next(responses)

    client = DarajaAuthClient(tenant_id="tenant-b", credentials={"consumer_key": "k", "consumer_secret": "s"}, session=DummySession(), cache=SimpleNamespace(get=lambda key: None, set=lambda key, value, ttl: None))

    token = client.get_access_token()

    assert token == "token-2"
