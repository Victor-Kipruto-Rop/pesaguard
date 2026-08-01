from types import SimpleNamespace

import rate_limiter


def test_rate_limiter_uses_memory_when_redis_disabled(monkeypatch):
    monkeypatch.setattr(rate_limiter, "ENABLE_REDIS_RATE_LIMITING", False)
    limiter = rate_limiter.RateLimiter(default_max_per_minute=2)

    allowed_1, _ = limiter.is_allowed("client", "/webhook")
    allowed_2, _ = limiter.is_allowed("client", "/webhook")
    allowed_3, status_3 = limiter.is_allowed("client", "/webhook")

    assert allowed_1 is True
    assert allowed_2 is True
    assert allowed_3 is False
    assert status_3["retry_after"] >= 1


def test_rate_limiter_uses_redis_when_enabled(monkeypatch):
    monkeypatch.setattr(rate_limiter, "ENABLE_REDIS_RATE_LIMITING", True)

    class FakeRedisLimiter:
        def is_allowed(self, client_id, endpoint, max_per_minute, tokens_required=1):
            return True, {"remaining": 9, "limit": 10, "reset_in": 0, "retry_after": 0}

    monkeypatch.setattr(rate_limiter, "RedisRateLimiter", lambda: FakeRedisLimiter())

    limiter = rate_limiter.RateLimiter(default_max_per_minute=10)
    allowed, status = limiter.is_allowed("client", "/webhook")

    assert allowed is True
    assert status["limit"] == 10


def test_redis_rate_limiter_script_round_trip(monkeypatch):
    calls = {}

    class FakeScript:
        def __call__(self, keys, args, client=None):
            calls["keys"] = keys
            calls["args"] = args
            return [1, 5, 10, 0]

    class FakeClient:
        def register_script(self, _lua):
            return FakeScript()

    monkeypatch.setattr("redis.from_url", lambda *args, **kwargs: FakeClient())

    limiter = rate_limiter.RedisRateLimiter(redis_url="redis://example")
    allowed, status = limiter.is_allowed("a", "b", max_per_minute=10)

    assert allowed is True
    assert status["remaining"] == 5
    assert calls["keys"][0].startswith("pesaguard:ratelimit:")
