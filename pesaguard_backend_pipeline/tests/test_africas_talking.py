import requests
import pytest

from pesaguard_backend_pipeline.africas_talking import (
    AfricasTalkingClient,
    SmsConfigurationError,
    SmsValidationError,
)


class FakeResponse:
    def __init__(self, status_code=200, payload=None, headers=None):
        self.status_code = status_code
        self._payload = payload
        self.headers = headers or {}
        self.content = b"{}"
        self.text = "{}"

    def json(self):
        return self._payload


class FakeSession:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def post(self, *args, **kwargs):
        self.calls.append((args, kwargs))
        response = self.responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response


def sent_response():
    return FakeResponse(200, {"SMSMessageData": {"Recipients": [{"status": "Sent", "statusCode": "100"}]}})


def make_client(session, **kwargs):
    return AfricasTalkingClient(
        username="user",
        api_key="key",
        environment="sandbox",
        session=session,
        **kwargs,
    )


def test_phone_normalization_accepts_formatted_kenyan_mobile():
    client = make_client(FakeSession([]))
    assert client._normalize_phone_number(" +254 (712)-345-678 ") == "+254712345678"
    assert client._normalize_phone_number("0712345678") == "+254712345678"
    assert client._normalize_phone_number("112345678") == "+254112345678"

    for value in ("abc", "123", "+12025550123", "+254812345678"):
        with pytest.raises(SmsValidationError):
            client._normalize_phone_number(value)


def test_environment_and_retry_configuration_fail_closed():
    with pytest.raises(SmsConfigurationError):
        AfricasTalkingClient(environment="prodution")
    with pytest.raises(SmsConfigurationError):
        AfricasTalkingClient(environment="sandbox", max_retries=-1)
    with pytest.raises(SmsConfigurationError):
        AfricasTalkingClient(environment="sandbox", timeout_seconds=0)


def test_zero_retries_still_makes_one_request_and_uses_structured_result(monkeypatch):
    session = FakeSession([sent_response()])
    metrics = []
    client = make_client(session, max_retries=0, metrics_hook=metrics.append)
    result = client.send_sms("0712345678", "  hello  ", idempotency_key="sms-1")

    assert result["status"] == "sent"
    assert result["attempts"] == 1
    assert len(session.calls) == 1
    assert session.calls[0][1]["timeout"] == (5.0, 10.0)
    assert session.calls[0][1]["headers"]["X-Idempotency-Key"] == "sms-1"
    assert any(item["event"] == "sms_sent" for item in metrics)


def test_429_honors_retry_after_and_provider_failure_is_not_success(monkeypatch):
    session = FakeSession([
        FakeResponse(429, {"error": "busy"}, {"Retry-After": "2"}),
        FakeResponse(200, {"SMSMessageData": {"Recipients": [{"status": "Failed", "statusCode": "403"}]}}),
    ])
    sleeps = []
    monkeypatch.setattr("pesaguard_backend_pipeline.africas_talking.time.sleep", sleeps.append)
    client = make_client(session, max_retries=1, max_backoff_seconds=5)
    result = client.send_sms("0712345678", "hello")

    assert result["status"] == "failed"
    assert result["reason"] == "403"
    assert len(session.calls) == 2
    assert sleeps == [2.0]


def test_timeout_is_not_retried_by_default_and_phone_is_not_logged(caplog):
    session = FakeSession([requests.Timeout("sensitive upstream details")])
    client = make_client(session, max_retries=3)
    with caplog.at_level("WARNING"):
        result = client.send_sms("0712345678", "hello")

    assert result["reason"] == "timeout_ambiguous"
    assert len(session.calls) == 1
    assert "0712345678" not in caplog.text
    assert "sensitive upstream details" not in caplog.text