import time

import pytest

from utils.retries import retry_with_backoff


def test_retry_with_full_jitter(monkeypatch):
    attempts = {"count": 0}
    sleeps = []

    def fake_sleep(duration):
        sleeps.append(duration)

    monkeypatch.setattr(time, "sleep", fake_sleep)
    monkeypatch.setattr("utils.retries.random.random", lambda: 0.5)

    def flaky():
        attempts["count"] += 1
        if attempts["count"] < 4:
            raise RuntimeError("temporary")
        return "ok"

    result = retry_with_backoff(flaky, retries=5, base=1, max_backoff=30, jitter="full")

    assert result == "ok"
    assert sleeps == [0.5, 1.0, 2.0]


def test_retry_with_backoff_raises_after_max_retries(monkeypatch):
    monkeypatch.setattr(time, "sleep", lambda _duration: None)

    def always_fail():
        raise ValueError("nope")

    with pytest.raises(ValueError):
        retry_with_backoff(always_fail, retries=2, base=0.1, jitter="none")
