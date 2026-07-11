import importlib
import os
import tempfile

import pytest

from auth_rbac import AuthRBAC


@pytest.fixture()
def webhook_client(monkeypatch):
    with tempfile.TemporaryDirectory() as tmpdir:
        monkeypatch.setenv("DATABASE_URL", f"sqlite:///{os.path.join(tmpdir, 'pesaguard_test.db')}")
        monkeypatch.setenv("DARAJA_ALLOWED_IPS", "127.0.0.1")
        monkeypatch.setenv("DARAJA_SHARED_SECRET", "test-secret")
        monkeypatch.setenv("PESAGUARD_WEBHOOK_MAX_BODY_BYTES", "256")
        import app as webhook_app

        webhook_app = importlib.reload(webhook_app)
        webhook_app.app.config.update(TESTING=True)
        with webhook_app.app.test_client() as client:
            yield client


@pytest.fixture()
def dashboard_client(monkeypatch):
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "dashboard_test.db")
        monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path}")
        monkeypatch.setenv("PESAGUARD_API_AUTH_REQUIRED", "1")
        import app_2

        app_2 = importlib.reload(app_2)
        app_2.Base.metadata.create_all(app_2.engine)
        app_2.app.config.update(TESTING=False)
        with app_2.app.test_client() as client:
            yield client, app_2


def test_webhook_rejects_oversized_payload_and_bad_source(webhook_client):
    response = webhook_client.post(
        "/webhook/mpesa/confirmation",
        data=b"{" + b"a" * 300 + b"}",
        content_type="application/json",
    )
    assert response.status_code == 413

    response = webhook_client.post(
        "/webhook/mpesa/confirmation",
        json={"TransactionType": "Pay Bill", "TransID": "abc", "TransTime": "20240101120000", "TransAmount": "10", "BusinessShortCode": "123456", "MSISDN": "254700000000"},
        headers={"X-Daraja-Shared-Secret": "wrong-secret"},
    )
    assert response.status_code == 403


def test_dashboard_api_requires_valid_bearer_token(dashboard_client):
    client, _ = dashboard_client

    unauthorized = client.get("/discrepancies")
    assert unauthorized.status_code == 401

    token = AuthRBAC.generate_token(
        user_id="ops-1",
        username="ops",
        tenant_id="tenant-a",
        roles=["operator"],
    )
    authorized = client.get("/discrepancies", headers={"Authorization": f"Bearer {token}"})
    assert authorized.status_code == 200
