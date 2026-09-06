import os
import sys
from types import SimpleNamespace

import pytest

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from pesaguard_backend_pipeline.shared.airtel.auth_client import AirtelAuthClient
from pesaguard_backend_pipeline.shared.airtel.config import AirtelConfig


class DummyResponse:
    def __init__(self, status_code=200, json_data=None, text=""):
        self.status_code = status_code
        self._json_data = json_data or {}
        self.text = text or ""

    def json(self):
        return self._json_data


def test_airtel_token_is_cached_and_refreshed(monkeypatch):
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
        return {"access_token": "airtel-token-1", "expires_in": 3600}

    client = AirtelAuthClient(
        tenant_id="tenant-airtel",
        credentials={"api_key": "k", "api_secret": "s"},
        cache=DummyCache(),
    )
    monkeypatch.setattr(client, "_fetch_access_token", fake_fetch)

    first = client.get_access_token()
    second = client.get_access_token()

    assert first == "airtel-token-1"
    assert second == "airtel-token-1"
    assert len(calls) == 1


def test_airtel_401_triggers_refresh(monkeypatch):
    responses = iter([
        DummyResponse(status_code=401, json_data={"error": "expired"}, text="expired"),
        DummyResponse(status_code=200, json_data={"access_token": "airtel-token-2", "expires_in": 3600}),
    ])

    class DummySession:
        def post(self, url, auth=None, timeout=None, headers=None):
            return next(responses)

        def request(self, method, url, headers=None, **kwargs):
            return DummyResponse(status_code=200, json_data={"ok": True})

    client = AirtelAuthClient(
        tenant_id="tenant-airtel",
        credentials={"api_key": "k", "api_secret": "s"},
        session=DummySession(),
        cache=SimpleNamespace(get=lambda key: None, set=lambda key, value, ttl: None),
    )

    token = client.get_access_token()
    assert token == "airtel-token-2"


def test_airtel_config_reads_tenant_environment(monkeypatch):
    monkeypatch.setenv("TENANT_ID", "acme")
    monkeypatch.setenv("ACME_AIRTEL_API_KEY", "key-123")
    monkeypatch.setenv("ACME_AIRTEL_API_SECRET", "secret-456")
    monkeypatch.setenv("ACME_AIRTEL_BASE_URL", "https://sandbox.example.com")

    config = AirtelConfig(tenant_id="acme")
    creds = config.get_credentials()

    assert creds["api_key"] == "key-123"
    assert creds["api_secret"] == "secret-456"
    assert creds["base_url"] == "https://sandbox.example.com"
    assert config.is_configured is True
