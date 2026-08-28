"""
Advanced Features API for PesaGuard - Webhooks, Auth, Email, Escalations, On-Call, Search, Rate Limiting.
Integrates webhook notifications, email distribution, custom escalation rules, on-call rotation tracking,
historical trends, advanced boolean search, rate limiting, and API authentication/RBAC.

NOTE ON CONSOLIDATION: this file replaces the old separate `features.py`
(create_features_app). That file only duplicated routes already implemented
correctly (with auth + tenant scoping) in dashboard.py:
/discrepancies/export/csv, /analytics/incident-trends, /incidents/filters/presets,
/incidents/auto-escalate, /analytics/reconciliation-report, /incidents/bulk-assign,
/incidents/search. Delete features.py and its registration call — nothing in
it is unique. Everything below is functionality that exists ONLY here
(auth/tokens, webhooks, escalation rules, on-call, email, advanced search,
public customer endpoints, rate-limited bulk ops).
"""

import hashlib
import hmac
import json
import logging
import os
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from flask import Flask, jsonify, request, g
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from pesaguard_backend_pipeline.webhook_manager import WebhookManager
from pesaguard_backend_pipeline.auth_rbac import AuthRBAC, require_auth, require_tenant_access, get_current_user
from pesaguard_backend_pipeline.rate_limiter import rate_limit, get_rate_limit_status
from pesaguard_backend_pipeline.email_service import EmailService
from pesaguard_backend_pipeline.escalation_engine import EscalationEngine
from pesaguard_backend_pipeline.on_call_service import OnCallService
from pesaguard_backend_pipeline.search_engine import AdvancedSearchEngine
from pesaguard_backend_pipeline.action_audit import ActionAuditEntry
from pesaguard_backend_pipeline.models import Base, Discrepancy, Report, DeadLetter
from pesaguard_backend_pipeline.tenant_settings import TenantSettingsStore

configure_logging = lambda: None  # Import from logging_utils if available
logger = logging.getLogger("pesaguard.advanced_features")

from pesaguard_backend_pipeline.app import app
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://pesaguard:pesaguard@localhost:5432/pesaguard")
REPORTS_DATABASE_URL = os.getenv("REPORTS_DATABASE_URL", DATABASE_URL)
AUDIT_DATABASE_URL = os.getenv("AUDIT_DATABASE_URL", DATABASE_URL)


def create_db_engine(url: str):
    if url.startswith("sqlite:///:memory:"):
        return create_engine(
            url,
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )

    return create_engine(url, pool_pre_ping=True)


engine = create_db_engine(DATABASE_URL)
reports_engine = create_db_engine(REPORTS_DATABASE_URL)
audit_engine = create_db_engine(AUDIT_DATABASE_URL)

SessionFactory = sessionmaker(bind=engine, expire_on_commit=False)
ReportsSessionFactory = sessionmaker(bind=reports_engine, expire_on_commit=False)
AuditSessionFactory = sessionmaker(bind=audit_engine, expire_on_commit=False)

# Initialize the shared schema on the primary engine early so SQLite-backed tests
# and lightweight local runs can persist webhook and audit records without a manual setup step.
# In non-test environments with a reachable Postgres instance this will succeed. When the
# database is unavailable or credentials are wrong, we degrade gracefully so app import
# and request handling continue to work for the rest of the stack.
try:
    Base.metadata.create_all(engine)
    Base.metadata.create_all(reports_engine)
    Base.metadata.create_all(audit_engine)
except Exception as exc:
    logger.warning("Advanced features database initialization skipped: %s", exc)


def _reports_url() -> str:
    return os.getenv("REPORTS_DATABASE_URL") or os.getenv("DATABASE_URL") or DATABASE_URL


def _audit_url() -> str:
    return os.getenv("AUDIT_DATABASE_URL") or os.getenv("DATABASE_URL") or DATABASE_URL


def SessionLocal(read_only: bool | None = None):
    """Create a session. Respects read_only parameter for compatibility with read replicas."""
    # app_4_advanced_features doesn't use replica engines, so read_only is ignored
    return SessionFactory()


def ReportsSessionLocal():
    return ReportsSessionFactory()


def AuditSessionLocal():
    return AuditSessionFactory()

email_service = EmailService(
    smtp_server=os.getenv("SMTP_SERVER", "localhost"),
    smtp_port=int(os.getenv("SMTP_PORT", 587)),
    from_email=os.getenv("SMTP_FROM_EMAIL", "noreply@pesaguard.local"),
)
settings_store = TenantSettingsStore()

ERROR_CODE_TAXONOMY = {
    "missing_credentials": {"status_code": 400, "description": "Request is missing username or password."},
    "invalid_credentials": {"status_code": 401, "description": "Authentication failed for the supplied credentials."},
    "not_authenticated": {"status_code": 401, "description": "Authentication token is missing or expired."},
    "missing_token": {"status_code": 400, "description": "A token value is required for this action."},
    "invalid_request": {"status_code": 400, "description": "Request payload is malformed or missing required fields."},
    "tenant_access_denied": {"status_code": 403, "description": "The caller does not have access to the requested tenant."},
    "resource_not_found": {"status_code": 404, "description": "The requested resource does not exist."},
    "rate_limit_exceeded": {"status_code": 429, "description": "The client exceeded the allowed request rate."},
    "internal_server_error": {"status_code": 500, "description": "The server encountered an unexpected error."},
}


def _request_id_value() -> str:
    return request.headers.get("X-Request-ID") or request.headers.get("X-Correlation-ID") or str(uuid.uuid4())


def _api_success(payload: Any, status_code: int = 200, meta: Optional[Dict[str, Any]] = None):
    body = {
        "status": "success",
        "data": payload,
        "request_id": _request_id_value(),
        "tenant_id": request.headers.get("X-Tenant-ID") or os.getenv("TENANT_ID", "default"),
    }
    if isinstance(payload, dict):
        for key, value in payload.items():
            if key not in body and key not in {"status", "error", "data", "request_id", "tenant_id", "meta", "ResultCode", "ResultDesc"}:
                body[key] = value
    if meta is not None:
        body["meta"] = meta
    return jsonify(body), status_code


def _api_error(code: str, message: str, status_code: int = 400, details: Optional[Dict[str, Any]] = None):
    body = {
        "status": "error",
        "error": {"code": code, "message": message},
        "request_id": _request_id_value(),
        "tenant_id": request.headers.get("X-Tenant-ID") or os.getenv("TENANT_ID", "default"),
        "ResultCode": 1,
        "ResultDesc": message,
    }
    if details:
        body["error"]["details"] = details
    return jsonify(body), status_code


def resolve_email_locale(tenant_id: str | None, user_id: str | None = None, settings_path=None) -> str:
    """Resolve the locale to use for email notifications based on tenant settings."""
    if not tenant_id:
        tenant_id = "default"
    if settings_path is not None:
        store = TenantSettingsStore(str(settings_path))
    else:
        store = settings_store

    tenant_settings = store.get(str(tenant_id))
    if not isinstance(tenant_settings, dict):
        return "en"

    if user_id:
        user_overrides = tenant_settings.get("user_locale_overrides") or {}
        if isinstance(user_overrides, dict):
            override = user_overrides.get(str(user_id)) or user_overrides.get(user_id)
            if override:
                return str(override)

        user_locales = tenant_settings.get("user_locales") or {}
        if isinstance(user_locales, dict):
            override = user_locales.get(str(user_id)) or user_locales.get(user_id)
            if override:
                return str(override)

    locale = tenant_settings.get("preferred_locale") or tenant_settings.get("locale")
    if locale:
        return str(locale)

    return "en"


def _record_action_audit(session, tenant_id: str, actor: str, action: str, details: dict | None = None) -> None:
    audit_session = None
    try:
        if AUDIT_DATABASE_URL != DATABASE_URL:
            audit_session = AuditSessionLocal()
            session = audit_session

        # FIXED: `uuid` was used here but never imported anywhere in the file.
        # Every call to this function raised NameError, which was silently
        # swallowed by the except below — meaning NO action audit entries
        # were ever actually being recorded, for any action, in the entire
        # advanced-features API. Audit logging was completely non-functional.
        entry = ActionAuditEntry(
            id=f"audit_{uuid.uuid4().hex[:12]}",
            tenant_id=tenant_id,
            actor=actor,
            action=action,
            details=details or {},
        )
        session.add(entry)
        session.commit()
    except Exception:
        logger.exception("Failed to persist audit entry")
    finally:
        if audit_session is not None:
            try:
                audit_session.close()
            except Exception:
                pass


def _incident_belongs_to_tenant(session, incident_id: str, tenant_id: str) -> Optional[Discrepancy]:
    """Fetch a Discrepancy by ID, but only if it belongs to tenant_id.

    Replaces the previous pattern of `session.query(Discrepancy).filter(Discrepancy.id == incident_id).first()`
    with no tenant filter — @require_tenant_access() only confirms the caller
    is allowed to act on the tenant_id THEY PASSED IN; it never confirms the
    fetched record actually belongs to that tenant. Without this check, a
    valid token for tenant A could bulk-assign or bulk-escalate tenant B's
    incidents just by supplying tenant B's incident IDs.
    """
    return (
        session.query(Discrepancy)
        .filter(Discrepancy.id == incident_id, Discrepancy.tenant_id == tenant_id)
        .first()
    )


@app.before_request
def _ensure_tables():
    if os.getenv("USE_IN_MEMORY_TEST_DB") == "true":
        return None
    try:
        Base.metadata.create_all(engine)
        Base.metadata.create_all(reports_engine)
        Base.metadata.create_all(audit_engine)
    except Exception:
        pass


@app.before_request
def _set_request_contract_context():
    request_id = (
        request.headers.get("X-Trace-Id")
        or request.headers.get("X-Request-ID")
        or request.headers.get("X-Correlation-ID")
        or str(uuid.uuid4())
    )
    request.environ["pesaguard.request_id"] = request_id
    request.environ["pesaguard.correlation_id"] = request_id


@app.after_request
def _after_request(response):
    request_id = request.environ.get("pesaguard.request_id") or request.headers.get("X-Request-ID") or str(uuid.uuid4())
    tenant_id = request.headers.get("X-Tenant-ID") or os.getenv("TENANT_ID", "default")
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Correlation-ID"] = request_id
    response.headers["X-Trace-Id"] = request_id
    response.headers["X-Tenant-ID"] = tenant_id
    return response


@app.route("/status", methods=["GET"])
def advanced_status():
    """Standard status payload for advanced service health and operations."""
    from pesaguard_backend_pipeline.health import build_health_payload
    payload = build_health_payload()
    payload["service"] = "pesaguard-advanced"
    payload["request_id"] = request.environ.get("pesaguard.request_id") or request.headers.get("X-Request-ID") or request.headers.get("X-Trace-Id") or _request_id_value()
    payload["tenant_id"] = request.headers.get("X-Tenant-ID") or os.getenv("TENANT_ID", "default")
    payload["trace_id"] = payload["request_id"]
    payload["generated_at"] = datetime.now(timezone.utc).isoformat()
    payload["ux"] = {
        "theme": "premium",
        "status_label": {
            "ok": "Healthy",
            "degraded": "Degraded",
            "failed": "Critical",
        }.get(payload.get("status", "unknown"), "Unknown"),
        "tone": {
            "ok": "success",
            "degraded": "warning",
            "failed": "danger",
        }.get(payload.get("status", "unknown"), "neutral"),
    }
    status_code = 503 if payload.get("status") == "failed" else 200
    return jsonify(payload), status_code


@app.route("/openapi.json", methods=["GET"])
def advanced_openapi_spec():
    spec = {
        "openapi": "3.0.3",
        "info": {
            "title": "PesaGuard Advanced Features API",
            "version": "1.0.0",
            "description": "Advanced tenant, webhooks, notifications, and escalation API.",
        },
        "components": {
            "schemas": {
                "ApiSuccess": {
                    "type": "object",
                    "example": {
                        "status": "success",
                        "data": {"tenant_id": "tenant-a", "webhooks": []},
                        "request_id": "req_123",
                        "tenant_id": "tenant-a",
                    },
                    "properties": {
                        "status": {"type": "string", "example": "success"},
                        "data": {"type": "object"},
                        "request_id": {"type": "string"},
                        "tenant_id": {"type": "string"},
                        "meta": {"type": "object", "nullable": True},
                    },
                },
                "ApiError": {
                    "type": "object",
                    "example": {
                        "status": "error",
                        "error": {"code": "invalid_credentials", "message": "Authentication failed."},
                        "request_id": "req_123",
                        "tenant_id": "tenant-a",
                        "ResultCode": 1,
                        "ResultDesc": "Authentication failed.",
                    },
                    "properties": {
                        "status": {"type": "string", "example": "error"},
                        "error": {
                            "type": "object",
                            "properties": {
                                "code": {"type": "string", "enum": list(ERROR_CODE_TAXONOMY.keys())},
                                "message": {"type": "string"},
                                "details": {"type": "object", "nullable": True},
                            },
                        },
                        "request_id": {"type": "string"},
                        "tenant_id": {"type": "string"},
                        "ResultCode": {"type": "integer", "example": 1},
                        "ResultDesc": {"type": "string"},
                    },
                },
            }
        },
        "paths": {
            "/status": {
                "get": {
                    "summary": "Status summary",
                    "responses": {
                        "200": {
                            "description": "Status output",
                            "content": {
                                "application/json": {
                                    "example": {
                                        "status": "ok",
                                        "service": "pesaguard-advanced",
                                        "dependencies": {"database": "healthy"},
                                    }
                                }
                            },
                        }
                    },
                }
            },
            "/auth/login": {
                "post": {
                    "summary": "Login and issue JWT token",
                    "responses": {
                        "200": {
                            "description": "Token response",
                            "content": {
                                "application/json": {
                                    "example": {
                                        "status": "success",
                                        "data": {"token": "jwt_token", "tenant_id": "tenant-a"},
                                        "request_id": "req_123",
                                        "tenant_id": "tenant-a",
                                    }
                                }
                            },
                        },
                        "401": {
                            "description": "Authentication failed",
                            "content": {
                                "application/json": {
                                    "example": {
                                        "status": "error",
                                        "error": {"code": "invalid_credentials", "message": "Authentication failed."},
                                        "request_id": "req_123",
                                        "tenant_id": "tenant-a",
                                    }
                                }
                            },
                        },
                    },
                }
            },
            "/webhooks": {
                "post": {
                    "summary": "Register webhook endpoint",
                    "responses": {
                        "201": {
                            "description": "Webhook created",
                            "content": {
                                "application/json": {
                                    "example": {
                                        "status": "success",
                                        "data": {"tenant_id": "tenant-a", "id": "wh_123", "url": "https://example.com/webhook"},
                                        "request_id": "req_123",
                                        "tenant_id": "tenant-a",
                                    }
                                }
                            },
                        }
                    },
                }
            },
            "/escalation-rules": {
                "get": {
                    "summary": "List escalation rules",
                    "responses": {
                        "200": {
                            "description": "Rules",
                            "content": {
                                "application/json": {
                                    "example": {
                                        "status": "success",
                                        "data": {"tenant_id": "tenant-a", "rules": []},
                                        "request_id": "req_123",
                                        "tenant_id": "tenant-a",
                                    }
                                }
                            },
                        }
                    },
                }
            },
            "/on-call/rotations": {
                "get": {
                    "summary": "List on-call rotations",
                    "responses": {
                        "200": {
                            "description": "Rotations",
                            "content": {
                                "application/json": {
                                    "example": {
                                        "status": "success",
                                        "data": {"tenant_id": "tenant-a", "active_rotations": []},
                                        "request_id": "req_123",
                                        "tenant_id": "tenant-a",
                                    }
                                }
                            },
                        }
                    },
                }
            },
        },
    }
    return jsonify(spec), 200


# ============================================================================
# AUTHENTICATION & TOKENS
# ============================================================================

# ----------------------------------------------------------------------------
# INTERIM credential store. There is no User table in models.py yet, so this
# is a real but temporary fix: credentials live in an environment variable as
# JSON, passwords are checked with a proper salted hash (stdlib hashlib,
# pbkdf2_hmac — no new dependency needed), and comparison is constant-time.
# This replaces the previous code, which accepted ANY non-empty password for
# ANY username and handed out a real signed token for whatever tenant_id the
# caller supplied in the request body — i.e. no authentication at all.
#
# This is NOT a long-term solution. Before onboarding more than a couple of
# pilot customers, replace this with a real `User` table (hashed passwords,
# one row per user, proper account management, password reset flow, etc.)
# and swap out `_verify_credentials` for a DB lookup. Keeping this as an env
# var is fine for a single pilot customer; it does not scale to self-serve
# signup.
#
# Expected env var PESAGUARD_AUTH_USERS_JSON, a JSON array like:
# [
#   {
#     "username": "admin",
#     "tenant_id": "pilot_customer_1",
#     "roles": ["admin"],
#     "salt_hex": "<hex salt, generate with os.urandom(16).hex()>",
#     "password_hash_hex": "<pbkdf2_hmac('sha256', password.encode(), salt, 200000).hex()>"
#   }
# ]
# ----------------------------------------------------------------------------

_PBKDF2_ITERATIONS = 200_000


def _hash_password(password: str, salt_hex: str) -> str:
    salt = bytes.fromhex(salt_hex)
    return hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, _PBKDF2_ITERATIONS).hex()


def _load_auth_users() -> Dict[str, Dict[str, Any]]:
    raw = os.getenv("PESAGUARD_AUTH_USERS_JSON", "")
    if not raw:
        logger.error(
            "PESAGUARD_AUTH_USERS_JSON is not set — no users can log in. "
            "This is intentional: without it, login must fail closed, not "
            "fall back to accepting anything."
        )
        return {}
    try:
        users = json.loads(raw)
        return {u["username"]: u for u in users if "username" in u}
    except (json.JSONDecodeError, TypeError, KeyError):
        logger.exception("PESAGUARD_AUTH_USERS_JSON is malformed — no users can log in")
        return {}


def _verify_credentials(username: str, password: str) -> Optional[Dict[str, Any]]:
    """Returns the matching user record if username/password are correct, else None.

    Fails closed: any missing config, malformed record, or mismatch returns
    None. Uses hmac.compare_digest for constant-time comparison so response
    timing doesn't leak whether a partial hash matched.
    """
    users = _load_auth_users()
    user = users.get(username)
    if not user:
        return None
    try:
        computed = _hash_password(password, user["salt_hex"])
    except (KeyError, ValueError):
        logger.exception("Malformed auth record for username=%s", username)
        return None
    if not hmac.compare_digest(computed, user.get("password_hash_hex", "")):
        return None
    return user


@app.route("/auth/login", methods=["POST"])
def login():
    """Generate authentication token.

    FIXED: previously accepted ANY non-empty password for ANY username, and
    trusted a tenant_id supplied directly in the request body with no check
    that the credentials actually belonged to that tenant. That meant anyone
    could obtain a valid, signed token for any tenant/role by guessing a
    username. Now requires a real password match against the interim
    credential store above.
    """
    data = request.json or {}
    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return _api_error("missing_credentials", "Username and password are required.", 400)

    user = _verify_credentials(username, password)
    if not user:
        logger.warning("Failed login attempt for username=%s", username)
        return _api_error("invalid_credentials", "Authentication failed.", 401)

    token = AuthRBAC.generate_token(
        user_id=f"user_{username}",
        username=username,
        tenant_id=user["tenant_id"],  # from the verified record, never from the request body
        roles=user.get("roles", ["operator"]),
    )

    return _api_success({
        "token": token,
        "user_id": f"user_{username}",
        "username": username,
        "tenant_id": user["tenant_id"],
        "roles": user.get("roles", ["operator"]),
        "expires_in": 86400,
    }, 200)


@app.route("/auth/verify", methods=["GET"])
@require_auth()
def verify_token():
    """Verify current authentication token."""
    user = get_current_user()
    if not user:
        return _api_error("not_authenticated", "Authentication token is missing or invalid.", 401)

    return _api_success({
        "user_id": user.user_id,
        "username": user.username,
        "tenant_id": user.tenant_id,
        "roles": user.roles,
        "permissions": user.permissions,
    }, 200)


@app.route("/auth/revoke", methods=["POST"])
@require_auth("manage:users")
def revoke_token():
    """Revoke an active authentication token."""
    payload = request.json or {}
    token = payload.get("token")
    if not token:
        return _api_error("missing_token", "A token value is required to revoke a session.", 400)

    AuthRBAC.revoke_token(token)
    return _api_success({"status": "revoked"}, 200)


# ============================================================================
# WEBHOOK MANAGEMENT
# ============================================================================

@app.route("/webhooks", methods=["POST"])
@require_auth("manage:webhooks")
@require_tenant_access()
def create_webhook():
    """Register a new webhook for a tenant."""
    data = request.json or {}
    tenant_id = data.get("tenant_id")
    session = AuditSessionLocal()

    try:
        webhook_mgr = WebhookManager(session)
        result = webhook_mgr.register_webhook(
            tenant_id=tenant_id,
            url=data.get("url"),
            event_types=data.get("event_types", ["escalation"]),
            retry_attempts=data.get("retry_attempts", 3),
            timeout_seconds=data.get("timeout_seconds", 10),
        )
        _record_action_audit(
            session,
            tenant_id=tenant_id,
            actor=get_current_user().user_id if get_current_user() else "system",
            action="create_webhook",
            details={"webhook_id": result.get("id"), "url": data.get("url"), "event_types": result.get("event_types")},
        )
        return _api_success(result, 201, meta={"operation": "create_webhook"})
    finally:
        session.close()


@app.route("/webhooks", methods=["GET"])
@require_auth("manage:webhooks")
@require_tenant_access()
def list_webhooks():
    """List all webhooks for a tenant."""
    tenant_id = request.args.get("tenant_id")
    session = AuditSessionLocal()

    try:
        webhook_mgr = WebhookManager(session)
        webhooks = webhook_mgr.get_webhooks(tenant_id)
        return _api_success({
            "tenant_id": tenant_id,
            "webhooks": [
                {
                    "id": w.id,
                    "url": w.url,
                    "event_types": w.event_types,
                    "active": w.active,
                    "created_at": w.created_at.isoformat(),
                }
                for w in webhooks
            ],
        }, 200, meta={"count": len(webhooks)})
    finally:
        session.close()


@app.route("/webhooks/<webhook_id>", methods=["PUT"])
@require_auth("manage:webhooks")
def update_webhook(webhook_id):
    """Update webhook configuration."""
    data = request.json or {}
    session = AuditSessionLocal()

    try:
        webhook_mgr = WebhookManager(session)
        result = webhook_mgr.update_webhook(webhook_id, **data)
        _record_action_audit(
            session,
            tenant_id=data.get("tenant_id", get_current_user().tenant_id if get_current_user() else "default"),
            actor=get_current_user().user_id if get_current_user() else "system",
            action="update_webhook",
            details={"webhook_id": webhook_id, **data},
        )
        return _api_success(result, 200, meta={"operation": "update_webhook"})
    finally:
        session.close()


@app.route("/webhooks/<webhook_id>/deliveries", methods=["GET"])
@require_auth("manage:webhooks")
def get_webhook_deliveries(webhook_id):
    """Get delivery history for a webhook."""
    limit = request.args.get("limit", 50, type=int)
    session = ReportsSessionLocal()

    try:
        webhook_mgr = WebhookManager(session)
        deliveries = webhook_mgr.get_delivery_history(webhook_id, limit=limit)
        return _api_success({
            "webhook_id": webhook_id,
            "deliveries": deliveries,
        }, 200, meta={"limit": limit})
    finally:
        session.close()


# ============================================================================
# ESCALATION RULES
# ============================================================================

@app.route("/escalation-rules", methods=["POST"])
@require_auth("write:escalation_rules")
@require_tenant_access()
def create_escalation_rule():
    """Create a custom escalation rule for a tenant."""
    data = request.json or {}
    tenant_id = data.get("tenant_id")
    session = SessionLocal()

    try:
        engine = EscalationEngine(session)
        result = engine.create_rule(
            tenant_id=tenant_id,
            name=data.get("name"),
            description=data.get("description"),
            condition_field=data.get("condition_field"),
            condition_operator=data.get("condition_operator"),
            condition_value=data.get("condition_value"),
            action=data.get("action"),
            target=data.get("target"),
            webhook_url=data.get("webhook_url"),
            priority=data.get("priority", 0),
        )
        _record_action_audit(
            session,
            tenant_id=tenant_id,
            actor=get_current_user().user_id if get_current_user() else "system",
            action="create_escalation_rule",
            details={"rule_id": result.get("id"), "name": data.get("name")},
        )
        return _api_success(result, 201, meta={"operation": "create_escalation_rule"})
    finally:
        session.close()


@app.route("/escalation-rules", methods=["GET"])
@require_auth("read:discrepancies")
@require_tenant_access()
def list_escalation_rules():
    """List escalation rules for a tenant."""
    tenant_id = request.args.get("tenant_id")
    session = SessionLocal()

    try:
        engine = EscalationEngine(session)
        rules = engine.get_rules(tenant_id)
        return _api_success({
            "tenant_id": tenant_id,
            "rules": rules,
        }, 200, meta={"count": len(rules)})
    finally:
        session.close()


@app.route("/escalation-rules/<rule_id>", methods=["PUT"])
@require_auth("write:escalation_rules")
def update_escalation_rule(rule_id):
    """Update an escalation rule."""
    data = request.json or {}
    session = SessionLocal()

    try:
        engine = EscalationEngine(session)
        result = engine.update_rule(rule_id, **data)
        return _api_success(result, 200, meta={"operation": "update_escalation_rule"})
    finally:
        session.close()


# ============================================================================
# ON-CALL ROTATIONS
# ============================================================================

@app.route("/on-call/rotations", methods=["POST"])
@require_auth("manage:on_call")
@require_tenant_access()
def create_on_call_rotation():
    """Create an on-call rotation."""
    data = request.json or {}
    tenant_id = data.get("tenant_id")
    session = SessionLocal()

    try:
        service = OnCallService(session)
        shift_start = datetime.fromisoformat(data.get("shift_start"))
        shift_end = datetime.fromisoformat(data.get("shift_end"))

        result = service.create_rotation(
            tenant_id=tenant_id,
            operator_id=data.get("operator_id"),
            operator_name=data.get("operator_name"),
            operator_email=data.get("operator_email"),
            operator_phone=data.get("operator_phone"),
            shift_start=shift_start,
            shift_end=shift_end,
            escalation_level=data.get("escalation_level", 1),
        )
        _record_action_audit(
            session,
            tenant_id=tenant_id,
            actor=get_current_user().user_id if get_current_user() else "system",
            action="create_on_call_rotation",
            details={"operator_id": data.get("operator_id"), "shift_start": shift_start.isoformat(), "shift_end": shift_end.isoformat()},
        )
        return _api_success(result, 201, meta={"operation": "create_on_call_rotation"})
    finally:
        session.close()


@app.route("/on-call/rotations/active", methods=["GET"])
@require_auth("read:discrepancies")
@require_tenant_access()
def get_active_on_call():
    """Get active on-call operators for a tenant."""
    tenant_id = request.args.get("tenant_id")
    session = SessionLocal()

    try:
        service = OnCallService(session)
        rotations = service.get_active_rotations(tenant_id)
        coverage = service.get_coverage_status(tenant_id)

        return _api_success({
            "tenant_id": tenant_id,
            "coverage": coverage,
            "active_rotations": rotations,
        }, 200, meta={"count": len(rotations)})
    finally:
        session.close()


@app.route("/on-call/schedule/<operator_id>", methods=["GET"])
@require_auth("read:discrepancies")
def get_operator_schedule(operator_id):
    """Get operator's on-call schedule."""
    tenant_id = request.args.get("tenant_id")
    days = request.args.get("days", 30, type=int)
    session = SessionLocal()

    try:
        service = OnCallService(session)
        schedule = service.get_operator_schedule(tenant_id, operator_id, days)
        return _api_success({
            "operator_id": operator_id,
            "tenant_id": tenant_id,
            "days": days,
            "schedule": schedule,
        }, 200, meta={"days": days})
    finally:
        session.close()


@app.route("/on-call/bulk", methods=["POST"])
@require_auth("manage:on_call")
@require_tenant_access()
def bulk_create_on_call():
    """Bulk create on-call rotations."""
    data = request.json or {}
    tenant_id = data.get("tenant_id")
    rotations_data = data.get("rotations", [])
    session = SessionLocal()

    try:
        service = OnCallService(session)
        result = service.bulk_create_rotations(tenant_id, rotations_data)
        _record_action_audit(
            session,
            tenant_id=tenant_id,
            actor=get_current_user().user_id if get_current_user() else "system",
            action="bulk_create_on_call_rotations",
            details={"created": result.get("created", 0)},
        )
        return _api_success(result, 201, meta={"operation": "bulk_create_on_call_rotations"})
    finally:
        session.close()


# ============================================================================
# EMAIL NOTIFICATIONS
# ============================================================================

@app.route("/emails/reconciliation", methods=["POST"])
@require_auth("write:discrepancies")
@require_tenant_access()
def send_reconciliation_email():
    """Send reconciliation report via email."""
    data = request.json or {}
    tenant_id = data.get("tenant_id")
    recipient = data.get("recipient_email")
    report_data = data.get("report_data", {})
    session = AuditSessionLocal()

    try:
        current_user = get_current_user()
        locale = resolve_email_locale(
            tenant_id,
            user_id=current_user.user_id if current_user else data.get("user_id") or request.args.get("user_id"),
        )
        result = email_service.send_reconciliation_report(
            session, tenant_id, recipient, report_data, locale=locale
        )
        _record_action_audit(
            session,
            tenant_id=tenant_id,
            actor=get_current_user().user_id if get_current_user() else "system",
            action="send_reconciliation_email",
            details={"recipient": recipient, "report_data": report_data},
        )
        return _api_success(result, 200, meta={"operation": "send_reconciliation_email"})
    finally:
        session.close()


@app.route("/emails/escalation", methods=["POST"])
@require_auth("write:discrepancies")
@require_tenant_access()
def send_escalation_email():
    """Send escalation notification."""
    data = request.json or {}
    tenant_id = data.get("tenant_id")
    recipient = data.get("recipient_email")
    incident = data.get("incident_data", {})
    session = AuditSessionLocal()

    try:
        current_user = get_current_user()
        locale = resolve_email_locale(
            tenant_id,
            user_id=current_user.user_id if current_user else data.get("user_id") or request.args.get("user_id"),
        )
        result = email_service.send_escalation_notification(
            session, tenant_id, recipient, incident, locale=locale
        )
        _record_action_audit(
            session,
            tenant_id=tenant_id,
            actor=get_current_user().user_id if get_current_user() else "system",
            action="send_escalation_email",
            details={"recipient": recipient, "incident": incident},
        )
        return _api_success(result, 200, meta={"operation": "send_escalation_email"})
    finally:
        session.close()


@app.route("/emails/history", methods=["GET"])
@require_auth("read:discrepancies")
@require_tenant_access()
def get_email_history():
    """Get email notification history for a tenant."""
    tenant_id = request.args.get("tenant_id")
    limit = request.args.get("limit", 50, type=int)
    session = AuditSessionLocal()

    try:
        history = email_service.get_email_history(session, tenant_id, limit)
        return _api_success({
            "tenant_id": tenant_id,
            "emails": history,
        }, 200, meta={"count": len(history)})
    finally:
        session.close()


# ============================================================================
# ADVANCED SEARCH
# ============================================================================

@app.route("/search", methods=["GET"])
@require_auth("read:discrepancies")
@require_tenant_access()
def advanced_search():
    """Execute advanced search with boolean operators."""
    tenant_id = request.args.get("tenant_id")
    query = request.args.get("q", "")
    limit = request.args.get("limit", 50, type=int)
    offset = request.args.get("offset", 0, type=int)
    session = SessionLocal()

    try:
        search = AdvancedSearchEngine(session)
        result = search.search(tenant_id, query, limit=limit, offset=offset)
        return _api_success(result, 200, meta={"query": query, "limit": limit, "offset": offset})
    finally:
        session.close()


@app.route("/search/filters", methods=["GET"])
@require_auth("read:discrepancies")
@require_tenant_access()
def search_filters():
    """Get available filter values for search."""
    tenant_id = request.args.get("tenant_id")
    session = SessionLocal()

    try:
        search = AdvancedSearchEngine(session)
        filters = search.suggest_filters(tenant_id)
        return _api_success({
            "tenant_id": tenant_id,
            "available_filters": filters,
        }, 200, meta={"tenant_id": tenant_id})
    finally:
        session.close()


@app.route("/search/structured", methods=["GET"])
@require_auth("read:discrepancies")
@require_tenant_access()
def structured_search():
    """Search using structured filters."""
    tenant_id = request.args.get("tenant_id")
    session = SessionLocal()

    try:
        search = AdvancedSearchEngine(session)
        result = search.search_by_filters(
            tenant_id=tenant_id,
            severity=request.args.get("severity"),
            status=request.args.get("status"),
            anomaly_type=request.args.get("anomaly_type"),
            resolved=request.args.get("resolved", type=lambda x: x.lower() == "true"),
            assignee=request.args.get("assignee"),
            days_back=request.args.get("days_back", 30, type=int),
            limit=request.args.get("limit", 50, type=int),
            offset=request.args.get("offset", 0, type=int),
        )
        return _api_success(result, 200, meta={"filters": {
            "severity": request.args.get("severity"),
            "status": request.args.get("status"),
            "anomaly_type": request.args.get("anomaly_type"),
            "resolved": request.args.get("resolved"),
            "assignee": request.args.get("assignee"),
            "days_back": request.args.get("days_back", 30, type=int),
        }})
    finally:
        session.close()


# Public/customer-facing endpoints for tenants to pull their own data
@app.route("/public/customers/<tenant_id>/reconciliations", methods=["GET"])
@require_auth("read:discrepancies")
@require_tenant_access()
def public_get_reconciliations(tenant_id: str):
    """Return recent reconciliation outcomes for the tenant."""
    limit = request.args.get("limit", 50, type=int)
    offset = request.args.get("offset", 0, type=int)
    session = SessionLocal()

    try:
        q = (
            session.query(Discrepancy)
            .filter(Discrepancy.tenant_id == tenant_id)
            .order_by(Discrepancy.detected_at.desc())
            .limit(limit)
            .offset(offset)
        )
        rows = q.all()
        return _api_success({
            "tenant_id": tenant_id,
            "count": len(rows),
            "reconciliations": [
                {
                    "id": r.id,
                    "trans_id": r.trans_id,
                    "anomaly_type": r.anomaly_type,
                    "status": r.status,
                    "severity": r.severity,
                    "details": r.details,
                    "detected_at": r.detected_at.isoformat() if r.detected_at else None,
                    "resolved": bool(r.resolved),
                }
                for r in rows
            ],
        }, 200, meta={"limit": limit, "offset": offset})
    finally:
        session.close()


@app.route("/public/customers/<tenant_id>/reports", methods=["GET"])
@require_auth("read:analytics")
@require_tenant_access()
def public_get_reports(tenant_id: str):
    """Return generated reports for the tenant (daily/weekly)."""
    limit = request.args.get("limit", 50, type=int)
    offset = request.args.get("offset", 0, type=int)
    session = ReportsSessionLocal()

    try:
        q = (
            session.query(Report)
            .filter(Report.tenant_id == tenant_id)
            .order_by(Report.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        rows = q.all()
        return _api_success({
            "tenant_id": tenant_id,
            "count": len(rows),
            "reports": [
                {
                    "id": r.id,
                    "report_type": r.report_type,
                    "period_start": r.period_start.isoformat() if r.period_start else None,
                    "period_end": r.period_end.isoformat() if r.period_end else None,
                    "status": r.status,
                    "created_at": r.created_at.isoformat() if r.created_at else None,
                    "content": r.content,
                }
                for r in rows
            ],
        }, 200, meta={"limit": limit, "offset": offset})
    finally:
        session.close()


# ============================================================================
# RATE LIMITED BULK OPERATIONS
# ============================================================================

@app.route("/bulk/assign", methods=["POST"], endpoint="bulk_assign_incidents_advanced")
@require_auth("bulk:operations")
@rate_limit(max_requests_per_minute=5, tokens_per_request=1, endpoint_name="bulk_assign")
@require_tenant_access()
def bulk_assign_incidents():
    """Bulk assign incidents with rate limiting."""
    data = request.json or {}
    tenant_id = data.get("tenant_id")
    incident_ids = data.get("incident_ids", [])
    assignee = data.get("assignee")
    session = SessionLocal()

    try:
        updated = 0
        skipped_ids = []
        for incident_id in incident_ids[:100]:  # Cap at 100 per request
            # FIXED: previously fetched by ID with NO tenant filter — a valid
            # token for tenant A could assign tenant B's incidents just by
            # knowing/guessing their IDs. require_tenant_access() only checks
            # the tenant_id param the caller supplied, not the fetched row.
            incident = _incident_belongs_to_tenant(session, incident_id, tenant_id)
            if incident:
                incident.assignee = assignee
                updated += 1
            else:
                skipped_ids.append(incident_id)

        session.commit()
        _record_action_audit(
            session,
            tenant_id=tenant_id,
            actor=get_current_user().user_id if get_current_user() else "system",
            action="bulk_assign_incidents",
            details={"updated": updated, "skipped_ids": skipped_ids, "assignee": assignee},
        )
        return _api_success({
            "updated": updated,
            "skipped_ids": skipped_ids,
            "rate_limit": get_rate_limit_status(),
        }, 200, meta={"operation": "bulk_assign_incidents"})
    finally:
        session.close()


@app.route("/bulk/escalate", methods=["POST"], endpoint="bulk_escalate_incidents_advanced")
@require_auth("bulk:operations")
@rate_limit(max_requests_per_minute=3, tokens_per_request=2, endpoint_name="bulk_escalate")
@require_tenant_access()
def bulk_escalate_incidents():
    """Bulk escalate incidents with rate limiting."""
    data = request.json or {}
    tenant_id = data.get("tenant_id")
    incident_ids = data.get("incident_ids", [])
    session = SessionLocal()

    try:
        escalated = []
        skipped_ids = []
        engine = EscalationEngine(session)

        for incident_id in incident_ids[:50]:  # Cap at 50 per request
            # FIXED: same tenant-filter gap as bulk_assign_incidents above —
            # a valid token for tenant A could previously escalate tenant B's
            # incidents by ID.
            incident = _incident_belongs_to_tenant(session, incident_id, tenant_id)
            if incident:
                result = engine.evaluate_and_escalate(tenant_id, incident)
                escalated.append(result)
            else:
                skipped_ids.append(incident_id)

        _record_action_audit(
            session,
            tenant_id=tenant_id,
            actor=get_current_user().user_id if get_current_user() else "system",
            action="bulk_escalate_incidents",
            details={"escalated_count": len(escalated), "skipped_ids": skipped_ids},
        )
        return _api_success({
            "escalated": len(escalated),
            "details": escalated,
            "skipped_ids": skipped_ids,
            "rate_limit": get_rate_limit_status(),
        }, 200, meta={"operation": "bulk_escalate_incidents"})
    finally:
        session.close()

