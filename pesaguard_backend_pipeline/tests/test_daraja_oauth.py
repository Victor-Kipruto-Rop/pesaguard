import json
import time

from shared.daraja.oauth import DarajaOAuth


class DummyResponse:
    def __init__(self, status_code=200, payload=None, text=""):
        self.status_code = status_code
        self._payload = payload or {}
        self.text = text

    def json(self):
        return self._payload


class DummySession:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = 0

    def get(self, url, auth=None, timeout=None):
        self.calls += 1
        return self.responses.pop(0)


def test_get_access_token_caches_until_expired(monkeypatch):
    session = DummySession([
        DummyResponse(200, {"access_token": "t1", "expires_in": 3600}),
    ])
    oauth = DarajaOAuth("id", "secret", "https://sandbox.safaricom.co.ke", session=session)

    first = oauth.get_access_token()
    second = oauth.get_access_token()

    assert first == "t1"
    assert second == "t1"
    assert session.calls == 1


def test_force_refresh_fetches_new_token(monkeypatch):
    session = DummySession([
        DummyResponse(200, {"access_token": "t1", "expires_in": 3600}),
        DummyResponse(200, {"access_token": "t2", "expires_in": 3600}),
    ])
    oauth = DarajaOAuth("id", "secret", "https://sandbox.safaricom.co.ke", session=session)

    first = oauth.get_access_token()
    second = oauth.force_refresh()

    assert first == "t1"
    assert second == "t2"
    assert session.calls == 2


def test_redis_cache_is_used_when_configured(monkeypatch):
    store = {}

    class FakeRedis:
        def get(self, key):
            return store.get(key)

        def setex(self, key, ttl, value):
            store[key] = value

    monkeypatch.setenv("REDIS_URL", "redis://example")
    monkeypatch.setattr("redis.from_url", lambda *args, **kwargs: FakeRedis())

    session = DummySession([
        DummyResponse(200, {"access_token": "redis-token", "expires_in": 3600}),
    ])
    oauth = DarajaOAuth("id", "secret", "https://sandbox.safaricom.co.ke", session=session)

    token = oauth.get_access_token()
    assert token == "redis-token"

    # New instance should hydrate from durable redis cache without HTTP call.
    session2 = DummySession([
        DummyResponse(200, {"access_token": "unexpected", "expires_in": 3600}),
    ])
    oauth2 = DarajaOAuth("id", "secret", "https://sandbox.safaricom.co.ke", session=session2)
    token2 = oauth2.get_access_token()

    assert token2 == "redis-token"
    assert session2.calls == 0
