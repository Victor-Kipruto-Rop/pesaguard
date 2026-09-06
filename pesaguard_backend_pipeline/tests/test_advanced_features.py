"""Test suite for advanced features: webhooks, auth, email, escalations, on-call, search, rate limiting."""

import os
import pytest
import json
from datetime import datetime, timezone, timedelta

from test_config import configure_test_database

configure_test_database()

from pesaguard_backend_pipeline import app_4_advanced_features
from pesaguard_backend_pipeline.app_4_advanced_features import app
from pesaguard_backend_pipeline.models import Base, Discrepancy, EscalationRule, OnCallRotation, WebhookConfig
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from pesaguard_backend_pipeline.auth_rbac import AuthRBAC


@pytest.fixture
def client():
    """Create test client with test database and tables."""
    app.config["TESTING"] = True
    
    # Create all tables for the test
    Base.metadata.create_all(app_4_advanced_features.engine)
    
    with app.test_client() as client:
        yield client


@pytest.fixture
def admin_token():
    """Generate admin JWT token."""
    return AuthRBAC.generate_token(
        user_id="user_admin",
        username="admin",
        tenant_id="test-tenant",
        roles=["admin"],
    )


@pytest.fixture
def operator_token():
    """Generate operator JWT token."""
    return AuthRBAC.generate_token(
        user_id="user_operator",
        username="operator1",
        tenant_id="test-tenant",
        roles=["operator"],
    )


class TestAuthentication:
    """Test authentication and RBAC."""

    def test_login(self, client):
        """Test user login."""
        response = client.post("/auth/login", json={
            "username": "testuser",
            "password": "password",
            "tenant_id": "test-tenant",
        })
        assert response.status_code == 200
        data = response.get_json()
        assert data["status"] == "success"
        assert "token" in data["data"]
        assert data["data"]["username"] == "testuser"

    def test_verify_token_valid(self, client, admin_token):
        """Test token verification with valid token."""
        response = client.get(
            "/auth/verify",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data["status"] == "success"
        assert data["data"]["username"] == "admin"

    def test_verify_token_missing(self, client):
        """Test token verification without token."""
        response = client.get("/auth/verify")
        assert response.status_code == 401

    def test_protected_endpoint_requires_permission(self, client, operator_token):
        """Test operator cannot access admin endpoints."""
        response = client.get(
            "/webhooks?tenant_id=test-tenant",
            headers={"Authorization": f"Bearer {operator_token}"},
        )
        # Operator doesn't have manage:webhooks permission
        assert response.status_code in [403, 404]

    def test_login_returns_refresh_token_and_allows_rotation(self, client):
        response = client.post(
            "/auth/login",
            json={
                "username": "testuser",
                "password": "password",
                "tenant_id": "test-tenant",
                "device_id": "device-abc",
            },
        )
        assert response.status_code == 200
        body = response.get_json()
        assert body["status"] == "success"
        assert "refresh_token" in body["data"]

        refresh = body["data"]["refresh_token"]
        rotated = client.post("/auth/refresh", json={"refresh_token": refresh})
        assert rotated.status_code == 200
        rotated_body = rotated.get_json()
        assert rotated_body["status"] == "success"
        assert rotated_body["data"]["token"]
        assert rotated_body["data"]["refresh_token"] != refresh

    def test_mfa_and_passwordless_verification_routes(self, client, admin_token):
        challenge = client.post(
            "/auth/mfa/challenge",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"user_id": "user_admin"},
        )
        challenge_data = challenge.get_json()["data"]
        verify = client.post(
            "/auth/mfa/verify",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"user_id": "user_admin", "challenge_id": challenge_data["challenge_id"], "code": "123456"},
        )
        assert verify.status_code == 200
        assert verify.get_json()["data"]["verified"] is True

        pw = client.post(
            "/auth/passwordless/challenge",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"user_id": "user_admin"},
        )
        pw_data = pw.get_json()["data"]
        pw_verify = client.post(
            "/auth/passwordless/verify",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"user_id": "user_admin", "challenge_id": pw_data["challenge_id"], "token": "otp-123456"},
        )
        assert pw_verify.status_code == 200
        assert pw_verify.get_json()["data"]["verified"] is True

    def test_api_key_auth_is_accepted_for_protected_routes(self, client, admin_token):
        session = app_4_advanced_features.SessionLocal()
        try:
            key = app_4_advanced_features.ApiKeyRecord(
                id="key_admin_test_1",
                tenant_id="test-tenant",
                key_value="test-api-key-123",
                role="admin",
                api_metadata={"scope": "webhook"},
                active=True,
            )
            session.add(key)
            session.commit()
        finally:
            session.close()

        response = client.get(
            "/webhooks?tenant_id=test-tenant",
            headers={"X-API-Key": "test-api-key-123"},
        )
        assert response.status_code == 200

    def test_admin_user_list_route(self, client, admin_token):
        response = client.get(
            "/auth/users",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200
        body = response.get_json()
        assert body["status"] == "success"
        assert "users" in body["data"]

    def test_oidc_config_and_session_revocation(self, client):
        login = client.post(
            "/auth/login",
            json={
                "username": "testuser",
                "password": "password",
                "tenant_id": "test-tenant",
                "device_id": "device-xyz",
            },
        )
        session_id = login.get_json()["data"]["session_id"]
        assert session_id

        oidc = client.get("/auth/sso/oidc/config")
        assert oidc.status_code == 200
        assert oidc.get_json()["status"] == "success"

        admin_token = AuthRBAC.generate_token(
            user_id="user_admin",
            username="admin",
            tenant_id="test-tenant",
            roles=["admin"],
        )
        revoke = client.post(
            f"/auth/sessions/{session_id}/revoke",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert revoke.status_code == 200
        assert revoke.get_json()["data"]["status"] == "revoked"

    def test_device_directory_and_oidc_code_flow(self, client):
        admin_token = AuthRBAC.generate_token(
            user_id="user_admin",
            username="admin",
            tenant_id="test-tenant",
            roles=["admin"],
        )

        device_response = client.get(
            "/auth/devices",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert device_response.status_code == 200
        assert "devices" in device_response.get_json()["data"]

        auth_response = client.get(
            "/auth/sso/oidc/authorize",
            query_string={
                "client_id": "demo-client",
                "redirect_uri": "https://example.com/callback",
                "response_type": "code",
                "scope": "openid profile email",
                "state": "abc123",
            },
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert auth_response.status_code == 302
        assert "code=" in auth_response.headers["Location"]
        assert "state=abc123" in auth_response.headers["Location"]

        auth_code = auth_response.headers["Location"].split("code=")[1].split("&")[0]
        token_response = client.post(
            "/auth/sso/oidc/token",
            json={
                "grant_type": "authorization_code",
                "client_id": "demo-client",
                "code": auth_code,
                "redirect_uri": "https://example.com/callback",
            },
        )
        assert token_response.status_code == 200
        token_body = token_response.get_json()
        assert token_body["status"] == "success"
        assert "access_token" in token_body["data"]
        assert "id_token" in token_body["data"]

    def test_oidc_provider_registry_validates_real_issuer_and_authorize_uses_it(self, client, admin_token, monkeypatch):
        metadata = {
            "issuer": "https://id.example.com",
            "authorization_endpoint": "https://id.example.com/oauth/authorize",
            "token_endpoint": "https://id.example.com/oauth/token",
            "userinfo_endpoint": "https://id.example.com/oauth/userinfo",
            "jwks_uri": "https://id.example.com/oauth/jwks",
            "scopes_supported": ["openid", "profile", "email"],
        }
        monkeypatch.setattr(app_4_advanced_features, "_fetch_oidc_metadata", lambda issuer: metadata)

        provider = client.post(
            "/auth/sso/providers",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "tenant_id": "tenant-a",
                "provider_name": "okta",
                "issuer": "https://id.example.com",
                "client_id": "client-123",
            },
        )
        assert provider.status_code == 201
        assert provider.get_json()["data"]["issuer"] == "https://id.example.com"

        validation = client.post(
            "/auth/sso/oidc/validate",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"issuer": "https://id.example.com"},
        )
        assert validation.status_code == 200
        assert validation.get_json()["data"]["valid"] is True

        authorize = client.get(
            "/auth/sso/oidc/authorize",
            query_string={
                "issuer": "https://id.example.com",
                "tenant_id": "tenant-a",
                "client_id": "demo-client",
                "redirect_uri": "https://example.com/callback",
                "response_type": "code",
                "state": "abc123",
            },
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert authorize.status_code == 302
        assert "code=" in authorize.headers["Location"]

    def test_provider_scoped_oidc_policy_enforces_roles_and_provisions_user(self, client, admin_token, monkeypatch):
        monkeypatch.setattr(
            app_4_advanced_features,
            "_fetch_oidc_metadata",
            lambda issuer: {
                "issuer": issuer,
                "authorization_endpoint": f"{issuer}/authorize",
                "token_endpoint": f"{issuer}/token",
                "jwks_uri": f"{issuer}/jwks",
                "scopes_supported": ["openid", "profile", "email"],
            },
        )

        provider = client.post(
            "/auth/sso/providers",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "tenant_id": "tenant-policy",
                "provider_name": "provider-scoped",
                "issuer": "https://id.policy.example.com",
                "client_id": "policy-client",
                "allowed_roles": ["admin"],
                "auto_provision": True,
                "claim_mapping": {"groups": "groups", "role": "role"},
            },
        )
        assert provider.status_code == 201

        callback = client.get(
            "/auth/sso/oidc/callback",
            query_string={
                "code": "demo-code-456",
                "state": "demo-state-2",
                "email": "new-op@example.com",
                "groups": "developer",
                "tenant_id": "tenant-policy",
                "issuer": "https://id.policy.example.com",
            },
        )
        assert callback.status_code == 403
        assert callback.get_json()["error"]["code"] == "policy_denied"

        accepted = client.get(
            "/auth/sso/oidc/callback",
            query_string={
                "code": "demo-code-457",
                "state": "demo-state-3",
                "email": "admin-op@example.com",
                "groups": "admin",
                "tenant_id": "tenant-policy",
                "issuer": "https://id.policy.example.com",
            },
        )
        assert accepted.status_code == 200
        body = accepted.get_json()
        assert body["data"]["tenant_id"] == "tenant-policy"
        assert "admin" in body["data"]["roles"]

        session = app_4_advanced_features.SessionLocal()
        try:
            user_record = session.query(app_4_advanced_features.UserAccount).filter_by(
                tenant_id="tenant-policy",
                email="admin-op@example.com",
            ).first()
            assert user_record is not None
            assert "admin" in user_record.roles
        finally:
            session.close()

    def test_oidc_callback_enforces_allowed_groups_and_provisions_user(self, client, monkeypatch):
        monkeypatch.setenv("OIDC_ALLOWED_GROUPS", "admin,developer")
        monkeypatch.setenv("OIDC_AUTO_PROVISION", "1")

        callback = client.get(
            "/auth/sso/oidc/callback",
            query_string={
                "code": "demo-code-456",
                "state": "demo-state-2",
                "email": "new-op@example.com",
                "groups": "admin,developer",
                "tenant_id": "tenant-provisioned",
            },
        )
        assert callback.status_code == 200
        body = callback.get_json()
        assert "admin" in body["data"]["roles"]
        assert "developer" in body["data"]["roles"]

        session = app_4_advanced_features.SessionLocal()
        try:
            user_record = session.query(app_4_advanced_features.UserAccount).filter_by(
                tenant_id="tenant-provisioned",
                email="new-op@example.com",
            ).first()
            assert user_record is not None
            assert "admin" in user_record.roles
        finally:
            session.close()

    def test_oidc_callback_rejects_claims_outside_allowed_policy(self, client, monkeypatch):
        monkeypatch.setenv("OIDC_ALLOWED_GROUPS", "admin")
        response = client.get(
            "/auth/sso/oidc/callback",
            query_string={
                "code": "demo-code-789",
                "state": "demo-state-3",
                "email": "outsider@example.com",
                "groups": "developer",
                "tenant_id": "tenant-restricted",
            },
        )
        assert response.status_code == 403
        assert response.get_json()["error"]["code"] == "policy_denied"

    def test_oidc_provider_config_and_callback_claims_map_to_roles(self, client):
        original_issuer = os.environ.get("OIDC_ISSUER")
        os.environ["OIDC_ISSUER"] = "https://id.example.com"
        try:
            config = client.get("/auth/sso/oidc/config")
            assert config.status_code == 200
            assert config.get_json()["data"]["issuer"] == "https://id.example.com"

            callback = client.get(
                "/auth/sso/oidc/callback",
                query_string={
                    "code": "demo-code-123",
                    "state": "demo-state",
                    "email": "ops@example.com",
                    "groups": "admin,developer",
                    "tenant_id": "tenant-a",
                },
            )
            body = callback.get_json()
            assert callback.status_code == 200
            assert body["status"] == "success"
            assert "roles" in body["data"]
            assert "admin" in body["data"]["roles"]
            assert "developer" in body["data"]["roles"]
            assert body["data"]["tenant_id"] == "tenant-a"
        finally:
            if original_issuer is None:
                os.environ.pop("OIDC_ISSUER", None)
            else:
                os.environ["OIDC_ISSUER"] = original_issuer


class TestWebhooks:
    """Test webhook functionality."""

    def test_create_webhook(self, client, admin_token):
        """Test webhook creation."""
        response = client.post(
            "/webhooks",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "tenant_id": "test-tenant",
                "url": "https://example.com/webhooks",
                "event_types": ["escalation", "resolution"],
                "retry_attempts": 3,
                "timeout_seconds": 10,
            },
        )
        assert response.status_code == 201
        data = response.get_json()
        assert data["status"] == "success"
        assert "id" in data["data"]
        assert data["data"]["url"] == "https://example.com/webhooks"

    def test_list_webhooks(self, client, admin_token):
        """Test listing webhooks."""
        # First create a webhook
        client.post(
            "/webhooks",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "tenant_id": "test-tenant",
                "url": "https://example.com/hook1",
                "event_types": ["escalation"],
            },
        )

        # Then list
        response = client.get(
            "/webhooks?tenant_id=test-tenant",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data["status"] == "success"
        assert "webhooks" in data["data"]


class TestEscalationRules:
    """Test escalation rules."""

    def test_create_escalation_rule(self, client, admin_token):
        """Test creating an escalation rule."""
        response = client.post(
            "/escalation-rules",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "tenant_id": "test-tenant",
                "name": "Critical Severity Escalation",
                "description": "Escalate critical severity incidents",
                "condition_field": "severity",
                "condition_operator": "equals",
                "condition_value": "critical",
                "action": "escalate",
                "target": "senior_operator",
                "priority": 1,
            },
        )
        assert response.status_code == 201
        data = response.get_json()
        assert data["status"] == "success"
        assert data["data"]["name"] == "Critical Severity Escalation"

    def test_list_escalation_rules(self, client, admin_token):
        """Test listing escalation rules."""
        # Create a rule
        client.post(
            "/escalation-rules",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "tenant_id": "test-tenant",
                "name": "Test Rule",
                "condition_field": "severity",
                "condition_operator": "equals",
                "condition_value": "critical",
                "action": "escalate",
            },
        )

        # List rules
        response = client.get(
            "/escalation-rules?tenant_id=test-tenant",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data["status"] == "success"
        assert "rules" in data["data"]


class TestOnCallRotations:
    """Test on-call rotation tracking."""

    def test_create_on_call_rotation(self, client, admin_token):
        """Test creating an on-call rotation."""
        now = datetime.now(timezone.utc)
        shift_start = now.isoformat()
        shift_end = (now + timedelta(hours=8)).isoformat()

        response = client.post(
            "/on-call/rotations",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "tenant_id": "test-tenant",
                "operator_id": "op_001",
                "operator_name": "John Operator",
                "operator_email": "john@example.com",
                "operator_phone": "+254712345678",
                "shift_start": shift_start,
                "shift_end": shift_end,
                "escalation_level": 1,
            },
        )
        assert response.status_code == 201
        data = response.get_json()
        assert data["status"] == "success"
        assert data["data"]["operator_id"] == "op_001"

    def test_get_active_on_call(self, client, admin_token):
        """Test getting active on-call operators."""
        now = datetime.now(timezone.utc)
        
        # Create active rotation
        client.post(
            "/on-call/rotations",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "tenant_id": "test-tenant",
                "operator_id": "op_001",
                "operator_name": "Active Operator",
                "operator_email": "active@example.com",
                "operator_phone": "+254712345678",
                "shift_start": now.isoformat(),
                "shift_end": (now + timedelta(hours=8)).isoformat(),
                "escalation_level": 1,
            },
        )

        # Get active
        response = client.get(
            "/on-call/rotations/active?tenant_id=test-tenant",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data["status"] == "success"
        assert "coverage" in data["data"]
        assert "active_rotations" in data["data"]

    def test_bulk_create_on_call(self, client, admin_token):
        """Test bulk creating on-call rotations."""
        now = datetime.now(timezone.utc)
        rotations_data = [
            {
                "operator_id": "op_001",
                "operator_name": "Operator 1",
                "operator_email": "op1@example.com",
                "operator_phone": "+254712345678",
                "shift_start": now.isoformat(),
                "shift_end": (now + timedelta(hours=8)).isoformat(),
                "escalation_level": 1,
            },
            {
                "operator_id": "op_002",
                "operator_name": "Operator 2",
                "operator_email": "op2@example.com",
                "operator_phone": "+254712345679",
                "shift_start": (now + timedelta(hours=8)).isoformat(),
                "shift_end": (now + timedelta(hours=16)).isoformat(),
                "escalation_level": 1,
            },
        ]

        response = client.post(
            "/on-call/bulk",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "tenant_id": "test-tenant",
                "rotations": rotations_data,
            },
        )
        assert response.status_code == 201
        data = response.get_json()
        assert data["status"] == "success"
        assert data["data"]["created"] == 2


class TestEmailNotifications:
    """Test email notification endpoints."""

    def test_send_reconciliation_email(self, client, operator_token):
        """Test sending reconciliation report email."""
        response = client.post(
            "/emails/reconciliation",
            headers={"Authorization": f"Bearer {operator_token}"},
            json={
                "tenant_id": "test-tenant",
                "recipient_email": "manager@example.com",
                "report_data": {
                    "total_discrepancies": 42,
                    "resolved": 38,
                    "pending": 4,
                    "sla_compliance": 95,
                    "avg_resolution_time": 15,
                },
            },
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data["status"] == "success"
        assert data["data"]["status"] in ["sent", "pending", "failed"]

    def test_send_escalation_email(self, client, operator_token):
        """Test sending escalation notification."""
        response = client.post(
            "/emails/escalation",
            headers={"Authorization": f"Bearer {operator_token}"},
            json={
                "tenant_id": "test-tenant",
                "recipient_email": "senior@example.com",
                "incident_data": {
                    "anomaly_type": "double_charge",
                    "severity": "critical",
                    "amount": 5000,
                    "trans_id": "TX123456",
                    "detected_at": datetime.now(timezone.utc).isoformat(),
                },
            },
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data["status"] == "success"
        assert "id" in data["data"]


class TestAdvancedSearch:
    """Test advanced search with boolean operators."""

    def test_search_with_query(self, client, operator_token):
        """Test search with boolean query."""
        response = client.get(
            "/search?tenant_id=test-tenant&q=severity:critical%20AND%20status:open",
            headers={"Authorization": f"Bearer {operator_token}"},
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data["status"] == "success"
        assert "results" in data["data"]
        assert "parsed" in data["data"]

    def test_structured_search(self, client, operator_token):
        """Test structured search with filters."""
        response = client.get(
            "/search/structured?tenant_id=test-tenant&severity=critical&status=open",
            headers={"Authorization": f"Bearer {operator_token}"},
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data["status"] == "success"
        assert "results" in data["data"]
        assert "filters" in data["data"]

    def test_get_search_filters(self, client, operator_token):
        """Test getting available search filters."""
        response = client.get(
            "/search/filters?tenant_id=test-tenant",
            headers={"Authorization": f"Bearer {operator_token}"},
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data["status"] == "success"
        assert "available_filters" in data["data"]


class TestRateLimiting:
    """Test rate limiting on bulk operations."""

    def test_bulk_assign_rate_limit(self, client, admin_token):
        """Test rate limiting on bulk assign."""
        # First request should succeed
        response1 = client.post(
            "/bulk/assign",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "tenant_id": "test-tenant",
                "incident_ids": ["inc_001", "inc_002"],
                "assignee": "operator1",
            },
        )
        assert response1.status_code == 200

        data = response1.get_json()
        assert data["status"] == "success"
        assert "rate_limit" in data["data"]

    def test_bulk_escalate_rate_limit(self, client, admin_token):
        """Test rate limiting on bulk escalate."""
        response = client.post(
            "/bulk/escalate",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "tenant_id": "test-tenant",
                "incident_ids": ["inc_001"],
            },
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data["status"] == "success"
        assert "rate_limit" in data["data"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
