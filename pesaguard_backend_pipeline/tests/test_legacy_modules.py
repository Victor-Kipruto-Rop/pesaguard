import json
import tempfile
from pathlib import Path
from types import SimpleNamespace

import pytest
import requests

from pesaguard_backend_pipeline import africas_talking
from pesaguard_backend_pipeline import background_tasks
from pesaguard_backend_pipeline import base_connector
from pesaguard_backend_pipeline import role_models
from pesaguard_backend_pipeline import tenant_settings_store
from pesaguard_backend_pipeline import webhook_manager


class FakeResponse:
    def __init__(self, status_code=200, text="", json_data=None):
        self.status_code = status_code
        self._text = text
        self._json_data = json_data or {}

    @property
    def text(self):
        return self._text

    def json(self):
        return self._json_data

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")


class FakeResult:
    def __init__(self, rows):
        self._rows = rows

    def fetchall(self):
        return self._rows


class FakeConnection:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def execute(self, query, params):
        return FakeResult([
            ("order-1", 25.5, "+254712345678", "2024-01-01T00:00:00+00:00", "paid"),
        ])


class FakeEngine:
    def connect(self):
        return FakeConnection()


class FakeQuery:
    def __init__(self, result):
        self._result = result

    def filter(self, *args, **kwargs):
        return self

    def first(self):
        return self._result

    def all(self):
        return self._result

    def order_by(self, *args, **kwargs):
        return self

    def limit(self, *args, **kwargs):
        return self


class FakeSession:
    def __init__(self, query_result=None):
        self.added = []
        self.commits = 0
        self.query_result = query_result

    def add(self, obj):
        self.added.append(obj)

    def commit(self):
        self.commits += 1

    def query(self, model):
        return FakeQuery(self.query_result)


def test_africas_talking_normalizes_number_and_retries(monkeypatch):
    client = africas_talking.AfricasTalkingClient(username="user", api_key="key", max_retries=2, timeout_seconds=1)

    calls = []

    def fake_post(*args, **kwargs):
        calls.append(kwargs)
        if len(calls) == 1:
            return FakeResponse(status_code=500, text="server error")
        return FakeResponse(status_code=200, text="ok", json_data={"smsId": "abc"})

    monkeypatch.setattr(africas_talking.requests, "post", fake_post)
    monkeypatch.setattr(africas_talking.time, "sleep", lambda _: None)

    result = client.send_sms("0712345678", "hello")

    assert result["status"] == "sent"
    assert result["attempts"] == 2
    assert calls[0]["data"]["to"] == "+254712345678"
    assert calls[1]["data"]["to"] == "+254712345678"


def test_africas_talking_normalizes_non_string_input_gracefully():
    client = africas_talking.AfricasTalkingClient(username="user", api_key="key")

    assert client._normalize_phone_number(None) == ""
    assert client._normalize_phone_number(712345678) == "+254712345678"


def test_list_tenant_ids_handles_list_returning_store(monkeypatch):
    class FakeStore:
        def get_all_tenants(self):
            return ["tenant-a", "tenant-b"]

    assert background_tasks._list_tenant_ids(FakeStore()) == ["tenant-a", "tenant-b"]


def test_base_connector_postgres_fetch_recent_records(monkeypatch):
    monkeypatch.setattr(base_connector, "create_engine", lambda *args, **kwargs: FakeEngine())

    connector = base_connector.PostgresConnector("sqlite:///:memory:", table_name="orders")
    records = connector.fetch_recent_records(since_minutes=30)

    assert records[0]["internal_ref"] == "order-1"
    assert records[0]["amount"] == 25.5
    assert records[0]["phone_number"] == "+254712345678"
    assert records[0]["status"] == "paid"


def test_base_connector_rest_fetch_recent_records(monkeypatch):
    connector = base_connector.RestConnector("https://example.com/api")

    def fake_get(self, url, headers=None, params=None, timeout=None):
        return FakeResponse(status_code=200, json_data={"items": [{"id": "x1", "amount": "10", "phone": "0712345678", "created_at": "2024-01-01T00:00:00Z", "status": "pending"}]})

    monkeypatch.setattr(connector._session, "get", fake_get)
    records = connector.fetch_recent_records(since_minutes=5)

    assert records[0]["internal_ref"] == "x1"
    assert records[0]["amount"] == 10.0
    assert records[0]["phone_number"] == "0712345678"


def test_role_models_permission_wildcards():
    assert role_models.has_permission("super_admin", "anything") is True
    assert role_models.has_permission("admin", "manage:connectors") is True
    assert role_models.has_permission("operator", "resolve:discrepancies") is True
    assert role_models.has_permission("viewer", "resolve:discrepancies") is False


def test_tenant_settings_store_persists_and_resolves_locale(tmp_path):
    settings_file = tmp_path / "tenant_settings.json"
    store = tenant_settings_store.TenantSettingsStore(str(settings_file))

    store.update("tenant-a", {"preferred_locale": "sw", "user_locale_overrides": {"user-1": "en"}})
    assert store.get("tenant-a")["preferred_locale"] == "sw"
    assert store.resolve_locale("tenant-a", "user-1") == "en"


def test_webhook_manager_delivers_payload(monkeypatch):
    session = FakeSession()
    manager = webhook_manager.WebhookManager(session)
    webhook = SimpleNamespace(
        id="wh-1",
        tenant_id="tenant-a",
        url="https://example.com/hook",
        event_types=["discrepancy.created"],
        retry_attempts=2,
        timeout_seconds=3,
        signing_secret="secret",
    )

    class FakeRequestsResponse:
        status_code = 200
        text = "ok"
        is_redirect = False

    def fake_post(url, json=None, headers=None, timeout=None, allow_redirects=False):
        return FakeRequestsResponse()

    monkeypatch.setattr(webhook_manager.requests, "post", fake_post)
    monkeypatch.setattr(webhook_manager.time, "sleep", lambda _: None)
    monkeypatch.setattr(webhook_manager, "_validate_webhook_url", lambda _: None)

    result = manager._deliver_webhook(webhook, "discrepancy.created", {"id": 1})

    assert result["status"] == "success"
    assert session.commits == 1
    assert session.added[0].status == "success"


def test_base_connector_google_sheets_returns_empty_for_missing_credentials():
    connector = base_connector.GoogleSheetsConnector(sheet_id="sheet-1", credentials_json="")

    assert connector.fetch_recent_records() == []


def test_base_connector_rest_handles_http_errors(monkeypatch):
    connector = base_connector.RestConnector("https://example.com/api")

    def fake_get(self, url, headers=None, params=None, timeout=None):
        raise requests.HTTPError("boom")

    monkeypatch.setattr(connector._session, "get", fake_get)


def test_identity_access_supports_enterprise_roles_sessions_and_abac():
    from pesaguard_backend_pipeline.auth_rbac import IdentityAccessService

    iam = IdentityAccessService()

    roles = iam.get_supported_roles()
    assert "super_admin" in roles
    assert "finance_manager" in roles
    assert "reconciliation_officer" in roles
    assert "customer" in roles

    user = iam.create_principal(
        user_id="user-101",
        username="finance.manager",
        tenant_id="tenant-a",
        roles=["Finance Manager"],
        attributes={"department": "finance", "country": "KE"},
    )
    assert "finance:approve_settlement" in user.permissions
    assert iam.can_access_resource(user, "settlement", {"tenant_id": "tenant-a", "department": "finance"}) is True
    assert iam.can_access_resource(user, "settlement", {"tenant_id": "tenant-b", "department": "finance"}) is False

    session = iam.create_session(user_id=user.user_id, tenant_id=user.tenant_id, device_id="device-1", user_agent="Safari")
    assert session["user_id"] == user.user_id
    assert iam.get_session(session["session_id"]) is not None

    api_key = iam.issue_api_key("tenant-a", "finance_manager")
    assert iam.verify_api_key(api_key)["tenant_id"] == "tenant-a"

    mfa = iam.create_mfa_challenge(user.user_id)
    assert mfa["status"] == "pending"
    assert iam.verify_mfa(user.user_id, mfa["challenge_id"], "123456")["verified"] is True

    passwordless = iam.create_passwordless_challenge(user.user_id)
    assert passwordless["status"] == "pending"
    assert iam.verify_passwordless_token(user.user_id, passwordless["challenge_id"], "otp-123456")["verified"] is True


def test_base_connector_postgres_drops_invalid_identifiers():
    connector = base_connector.PostgresConnector("sqlite:///:memory:", table_name="bad identifier")

    assert connector.fetch_recent_records() == []


def test_webhook_manager_register_rejects_invalid_urls():
    session = FakeSession()
    manager = webhook_manager.WebhookManager(session)

    result = manager.register_webhook("tenant-a", "http://example.com/hook", ["discrepancy.created"])

    assert result["error"] == "invalid_webhook_url"
    assert session.commits == 0


def test_webhook_manager_update_rejects_invalid_urls():
    session = FakeSession(query_result=SimpleNamespace(url="https://example.com/hook", active=True, event_types=["discrepancy.created"]))
    manager = webhook_manager.WebhookManager(session)

    result = manager.update_webhook("wh-1", "tenant-a", url="http://example.com/hook")

    assert result["error"] == "invalid_webhook_url"


def test_webhook_manager_retries_and_records_failures(monkeypatch):
    session = FakeSession()
    manager = webhook_manager.WebhookManager(session)
    webhook = SimpleNamespace(
        id="wh-2",
        tenant_id="tenant-a",
        url="https://example.com/hook",
        event_types=["discrepancy.created"],
        retry_attempts=2,
        timeout_seconds=1,
        signing_secret="secret",
    )

    def fake_post(url, json=None, headers=None, timeout=None, allow_redirects=False):
        raise webhook_manager.requests.Timeout("timed out")

    monkeypatch.setattr(webhook_manager.requests, "post", fake_post)
    monkeypatch.setattr(webhook_manager.time, "sleep", lambda _: None)
    monkeypatch.setattr(webhook_manager, "_validate_webhook_url", lambda _: None)

    result = manager._deliver_webhook(webhook, "discrepancy.created", {"id": 2})

    assert result["status"] == "failed"
    assert result["attempts"] == 2
    assert session.added[-1].status == "failed"
