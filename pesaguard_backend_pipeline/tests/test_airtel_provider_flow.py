import importlib
import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from pesaguard_backend_pipeline.reconciliation_engine import evaluate_transaction, resolve_payment_context, resolve_provider
from pesaguard_backend_pipeline.shared.airtel.payment_client import AirtelPaymentClient
from pesaguard_backend_pipeline.shared.bank.payment_client import BankPaymentClient


class DummySession:
    def __init__(self, access_token: str = "test-access-token"):
        self.calls = []
        self.auth_calls = []
        self._access_token = access_token

    def post(self, url, auth=None, timeout=None, headers=None, **kwargs):
        """Serve the OAuth2 token endpoint used by AirtelAuthClient."""
        self.auth_calls.append({"url": url, "auth": auth, "timeout": timeout, "headers": headers})
        return type(
            "AuthResp",
            (),
            {"status_code": 200, "text": "OK", "json": lambda self: {"access_token": "test-access-token", "expires_in": 3600}},
        )()

    def request(self, method, url, json=None, headers=None, timeout=None):
        self.calls.append({"method": method, "url": url, "json": json, "headers": headers, "timeout": timeout})
        return type("Resp", (), {"status_code": 200, "text": "OK", "json": lambda self: {"status": "accepted", "transactionId": "AIR-123"}})()


def test_provider_resolution_detects_airtel_and_daraja_events():
    airtel_event = {"transactionId": "AIR-100", "amount": 100, "currency": "UGX", "status": "success"}
    daraja_event = {"TransID": "M-100", "TransAmount": 100, "TransactionType": "STK_PUSH", "MSISDN": "254712345678"}

    assert resolve_payment_context(airtel_event) == {"payment_channel": "MOBILE_MONEY", "provider": "AIRTEL_MONEY"}
    assert resolve_payment_context(daraja_event) == {"payment_channel": "MOBILE_MONEY", "provider": "MPESA"}
    assert resolve_provider(airtel_event) == "AIRTEL_MONEY"
    assert resolve_provider(daraja_event) == "MPESA"


def test_evaluate_transaction_includes_provider_metadata():
    event = {"transactionId": "AIR-200", "amount": 200, "currency": "UGX", "status": "success"}
    result = evaluate_transaction(event, [{"internal_ref": "INV-1", "amount": 200.0, "phone_number": "+256700000001", "timestamp": "2026-09-06T00:00:00Z", "status": "paid"}], set(), window_minutes=60)

    assert result["payment_channel"] == "MOBILE_MONEY"
    assert result["provider"] == "AIRTEL_MONEY"
    assert result["status"] in {"matched", "needs_review"}


def test_airtel_payment_client_builds_payload_and_posts_it():
    session = DummySession()
    client = AirtelPaymentClient(tenant_id="tenant-airtel", credentials={"api_key": "key", "api_secret": "secret", "base_url": "https://sandbox.example.com"}, session=session)

    payload = client.build_disbursement_payload(
        amount=2500,
        currency="UGX",
        reference="INV-777",
        msisdn="256700000001",
        description="Loan repayment",
    )

    assert payload["amount"] == 2500
    assert payload["reference"] == "INV-777"

    resp = client.request_payment(
        amount=2500,
        currency="UGX",
        reference="INV-777",
        msisdn="256700000001",
        description="Loan repayment",
    )

    assert resp["status"] == "accepted"
    assert len(session.calls) == 1

    # The disbursement must be OAuth2 authenticated — Airtel rejects payouts
    # without a Bearer token, so verify the token handshake and header both happened.
    assert len(session.auth_calls) == 1
    assert session.auth_calls[0]["auth"] == ("key", "secret")
    assert session.calls[0]["headers"]["Authorization"] == "Bearer test-access-token"
    assert session.calls[0]["url"] == "https://sandbox.example.com/merchant/v1/payments"


def test_airtel_payment_client_refuses_to_send_without_credentials():
    """A payout with no tenant credentials must fail fast, never go out unauthenticated."""
    session = DummySession()
    client = AirtelPaymentClient(tenant_id="tenant-airtel", credentials={}, session=session)

    try:
        client.request_payment(
            amount=100,
            currency="UGX",
            reference="INV-NOAUTH",
            msisdn="256700000002",
        )
    except ValueError as exc:
        assert "Missing Airtel API key or secret" in str(exc)
    else:  # pragma: no cover - the guard above must raise
        raise AssertionError("expected ValueError when Airtel credentials are missing")

    assert session.calls == []
    assert session.auth_calls == []


def test_airtel_admin_payment_route_calls_client(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "sqlite:///:memory:")
    monkeypatch.setenv("PESAGUARD_ADMIN_API_TOKEN", "admin-secret")
    monkeypatch.setenv("AIRTEL_API_KEY", "key")
    monkeypatch.setenv("AIRTEL_API_SECRET", "secret")

    import app as webhook_app
    app_module = importlib.reload(webhook_app)
    app_module.app.config.update(TESTING=True)

    calls = []

    def fake_request_payment(self, amount, currency, reference, msisdn, description="", **extra):
        calls.append({
            "amount": amount,
            "currency": currency,
            "reference": reference,
            "msisdn": msisdn,
            "description": description,
            **extra,
        })
        return {"status": "accepted", "transactionId": "AIR-ROUTE-1"}

    monkeypatch.setattr(app_module.AirtelPaymentClient, "request_payment", fake_request_payment)

    with app_module.app.test_client() as client:
        response = client.post(
            "/admin/airtel/payments",
            json={
                "amount": 2500,
                "currency": "UGX",
                "reference": "INV-ROUTE-99",
                "msisdn": "256700000001",
                "description": "Loan repayment",
            },
            headers={"X-Admin-Token": "admin-secret"},
        )

    assert response.status_code == 200
    assert response.get_json()["status"] == "accepted"
    assert calls[0]["reference"] == "INV-ROUTE-99"


def test_provider_resolution_detects_bank_events_and_bank_client_builds_payload():
    bank_event = {
        "transactionId": "BANK-400",
        "amount": 400,
        "currency": "KES",
        "status": "posted",
        "bankName": "KCB",
        "accountNumber": "1234567890",
    }

    assert resolve_payment_context(bank_event) == {"payment_channel": "BANK", "provider": "KCB"}
    assert resolve_provider(bank_event) == "KCB"

    client = BankPaymentClient(
        tenant_id="tenant-bank",
        credentials={"api_key": "bank-key", "api_secret": "bank-secret", "base_url": "https://api.bank.example"},
        session=DummySession(),
    )
    payload = client.build_transfer_payload(
        amount=400,
        currency="KES",
        reference="INV-BANK-400",
        account_number="1234567890",
        bank_name="KCB",
        narration="Salary disbursement",
    )

    assert payload["amount"] == 400
    assert payload["bank_name"] == "KCB"


def test_bank_admin_payment_route_calls_client(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "sqlite:///:memory:")
    monkeypatch.setenv("PESAGUARD_ADMIN_API_TOKEN", "admin-secret")
    monkeypatch.setenv("BANK_API_KEY", "key")
    monkeypatch.setenv("BANK_API_SECRET", "secret")

    import app as webhook_app
    app_module = importlib.reload(webhook_app)
    app_module.app.config.update(TESTING=True)

    calls = []

    def fake_request_payment(self, amount, currency, reference, account_number, bank_name, narration="", **extra):
        calls.append({
            "amount": amount,
            "currency": currency,
            "reference": reference,
            "account_number": account_number,
            "bank_name": bank_name,
            "narration": narration,
            **extra,
        })
        return {"status": "processed", "transactionId": "BANK-ROUTE-1"}

    monkeypatch.setattr(app_module.BankPaymentClient, "request_payment", fake_request_payment)

    with app_module.app.test_client() as client:
        response = client.post(
            "/admin/bank/payments",
            json={
                "amount": 400,
                "currency": "KES",
                "reference": "INV-BANK-ROUTE-99",
                "account_number": "1234567890",
                "bank_name": "KCB",
                "narration": "Invoice settlement",
            },
            headers={"X-Admin-Token": "admin-secret"},
        )

    assert response.status_code == 200
    assert response.get_json()["status"] == "processed"
    assert calls[0]["reference"] == "INV-BANK-ROUTE-99"


def test_bank_ingestion_contracts_route_exposes_example_payloads(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "sqlite:///:memory:")
    monkeypatch.setenv("PESAGUARD_ADMIN_API_TOKEN", "admin-secret")

    import app as webhook_app
    app_module = importlib.reload(webhook_app)
    app_module.app.config.update(TESTING=True)

    with app_module.app.test_client() as client:
        response = client.get(
            "/admin/bank/ingest/contracts",
            headers={"X-Admin-Token": "admin-secret"},
        )

    assert response.status_code == 200
    body = response.get_json()
    assert "csv" in body["source_types"]
    assert "excel" in body["source_types"]
    assert "sftp" in body["source_types"]
    assert "webhook" in body["source_types"]
    assert body["source_types"]["csv"]["example"]["source_type"] == "csv"


def test_payment_contracts_route_exposes_example_payloads(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "sqlite:///:memory:")
    monkeypatch.setenv("PESAGUARD_ADMIN_API_TOKEN", "admin-secret")

    import app as webhook_app
    app_module = importlib.reload(webhook_app)
    app_module.app.config.update(TESTING=True)

    with app_module.app.test_client() as client:
        airtel_response = client.get(
            "/admin/airtel/payments/contracts",
            headers={"X-Admin-Token": "admin-secret"},
        )
        bank_response = client.get(
            "/admin/bank/payments/contracts",
            headers={"X-Admin-Token": "admin-secret"},
        )

    assert airtel_response.status_code == 200
    assert bank_response.status_code == 200
    assert airtel_response.get_json()["payment_channel"] == "MOBILE_MONEY"
    assert bank_response.get_json()["payment_channel"] == "BANK"
    assert airtel_response.get_json()["provider"] == "AIRTEL_MONEY"
    assert bank_response.get_json()["provider"] == "KCB"
    assert airtel_response.get_json()["request_example"]["currency"] == "UGX"
    assert bank_response.get_json()["request_example"]["currency"] == "KES"
