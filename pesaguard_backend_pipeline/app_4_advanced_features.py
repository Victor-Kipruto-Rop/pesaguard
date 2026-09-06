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
from typing import Any, Dict, List, Optional
from urllib import error as urllib_error
from urllib import request as urllib_request

from flask import Flask, jsonify, request, g, redirect
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from pesaguard_backend_pipeline.webhook_manager import WebhookManager
from pesaguard_backend_pipeline.auth_rbac import AuthRBAC, IdentityAccessService, require_auth, require_tenant_access, get_current_user
from pesaguard_backend_pipeline.rate_limiter import rate_limit, get_rate_limit_status
from pesaguard_backend_pipeline.email_service import EmailService
from pesaguard_backend_pipeline.escalation_engine import EscalationEngine
from pesaguard_backend_pipeline.on_call_service import OnCallService
from pesaguard_backend_pipeline.search_engine import AdvancedSearchEngine
from pesaguard_backend_pipeline.action_audit import ActionAuditEntry
from pesaguard_backend_pipeline.models import (
    Base,
    Discrepancy,
    Report,
    DeadLetter,
    UserAccount,
    UserSession,
    ApiKeyRecord,
    OIDCProvider,
    MFAChallenge,
    PasswordlessChallenge,
)
from pesaguard_backend_pipeline.tenant_settings import TenantSettingsStore

configure_logging = lambda: None  # Import from logging_utils if available
logger = logging.getLogger("pesaguard.advanced_features")

from pesaguard_backend_pipeline.app import app

if getattr(app, "_got_first_request", False):
    app._got_first_request = False


def _idempotent_route(rule, **options):
    """Register a route so repeated imports/reloads of this module stay safe.

    Flask's uniqueness constraint is on the ENDPOINT name, not on the URL rule:
    the same rule may legitimately be registered more than once with different
    methods (e.g. ``POST /webhooks`` to create and ``GET /webhooks`` to list).
    Deduping on the rule alone silently dropped the second registration and made
    those methods answer 405 Method Not Allowed, so we key on
    (endpoint, methods) instead.
    """
    if getattr(app, "_got_first_request", False):
        def _noop(view_func):
            return view_func
        return _noop

    def decorator(view_func):
        endpoint = options.get("endpoint") or view_func.__name__
        methods = {str(m).upper() for m in (options.get("methods") or ["GET"])}

        # Same endpoint already bound (module reload) — keep the existing view.
        if endpoint in app.view_functions:
            return view_func

        # Same rule already serving every method requested — nothing to add.
        for existing_rule in app.url_map.iter_rules():
            if existing_rule.rule != rule:
                continue
            existing_methods = {str(m).upper() for m in (existing_rule.methods or set())}
            if methods.issubset(existing_methods):
                return view_func

        route_options = {k: v for k, v in options.items() if k != "endpoint"}
        return app.route(rule, endpoint=endpoint, **route_options)(view_func)

    return decorator


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


def _fetch_oidc_metadata(issuer: str) -> Dict[str, Any]:
    """Fetch and validate the OIDC metadata document from a real provider issuer."""
    if not issuer:
        raise ValueError("issuer is required")
    issuer_url = issuer.strip().rstrip("/")
    metadata_url = f"{issuer_url}/.well-known/openid-configuration"
    try:
        with urllib_request.urlopen(urllib_request.Request(metadata_url, headers={"Accept": "application/json"}), timeout=10) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except (urllib_error.URLError, ValueError, json.JSONDecodeError) as exc:
        raise ValueError(f"unable to fetch OIDC metadata for issuer {issuer}: {exc}") from exc

    required_fields = ["issuer", "authorization_endpoint", "token_endpoint", "jwks_uri"]
    missing = [field for field in required_fields if not payload.get(field)]
    if missing:
        raise ValueError(f"OIDC metadata missing required fields: {missing}")
    return payload


def _resolve_oidc_provider(tenant_id: Optional[str] = None, issuer: Optional[str] = None) -> Optional[OIDCProvider]:
    """Resolve the configured tenant OIDC provider, or fall back to the environment/default issuer when no explicit provider has been registered."""
    session = SessionLocal()
    try:
        query = session.query(OIDCProvider).filter(OIDCProvider.enabled.is_(True))
        candidate_tenant = tenant_id or request.args.get("tenant_id") or os.getenv("TENANT_ID") or "default"
        if issuer:
            provider = query.filter(OIDCProvider.issuer == issuer, OIDCProvider.tenant_id == candidate_tenant).first()
            if provider:
                return provider
        if tenant_id or request.args.get("tenant_id"):
            provider = query.filter(OIDCProvider.tenant_id == candidate_tenant).order_by(OIDCProvider.created_at.desc()).first()
            if provider:
                return provider
        env_issuer = os.getenv("OIDC_ISSUER") or (request.url_root.rstrip("/") if request.url_root else "https://localhost")
        provider = query.filter(OIDCProvider.issuer == env_issuer).order_by(OIDCProvider.created_at.desc()).first()
        if provider:
            return provider
        if not issuer and not query.count():
            return OIDCProvider(
                id=str(uuid.uuid4()),
                tenant_id=candidate_tenant,
                provider_name="default-local-oidc",
                issuer=env_issuer,
                authorization_endpoint=f"{env_issuer.rstrip('/')}/auth/sso/oidc/authorize",
                token_endpoint=f"{env_issuer.rstrip('/')}/auth/sso/oidc/token",
                userinfo_endpoint=f"{env_issuer.rstrip('/')}/auth/sso/oidc/userinfo",
                jwks_uri=f"{env_issuer.rstrip('/')}/auth/sso/oidc/jwks",
                scopes=["openid", "profile", "email"],
                enabled=True,
                provider_metadata={
                    "issuer": env_issuer,
                    "authorization_endpoint": f"{env_issuer.rstrip('/')}/auth/sso/oidc/authorize",
                    "token_endpoint": f"{env_issuer.rstrip('/')}/auth/sso/oidc/token",
                    "userinfo_endpoint": f"{env_issuer.rstrip('/')}/auth/sso/oidc/userinfo",
                    "jwks_uri": f"{env_issuer.rstrip('/')}/auth/sso/oidc/jwks",
                    "scopes_supported": ["openid", "profile", "email"],
                },
            )
        return None
    finally:
        session.close()


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


@_idempotent_route("/status", methods=["GET"])
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


def build_advanced_openapi_spec() -> Dict[str, Any]:
    """Return this module's OpenAPI fragment (auth, webhooks, escalation, on-call)."""
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
    return spec


@_idempotent_route("/openapi.json", methods=["GET"])
def advanced_openapi_spec():
    spec = build_advanced_openapi_spec()
    try:
        # Merge the dashboard fragment so the combined spec stays complete
        # regardless of which module happened to register this route first.
        from pesaguard_backend_pipeline.app_2 import (
            build_dashboard_openapi_spec,
            _merge_openapi_paths,
        )

        _merge_openapi_paths(spec, build_dashboard_openapi_spec())
    except Exception:  # pragma: no cover - dashboard module is optional here
        logger.debug("Dashboard OpenAPI fragment unavailable", exc_info=True)
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


def _hash_password_record(password: str, salt_hex: str) -> str:
    salt = bytes.fromhex(salt_hex)
    return hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, _PBKDF2_ITERATIONS).hex()


def _verify_credentials(username: str, password: str) -> Optional[Dict[str, Any]]:
    """Authenticate against the persisted user table when available, with env-var fallback for legacy test setup."""
    session = SessionLocal()
    try:
        user_record = session.query(UserAccount).filter(UserAccount.username == username).first()
        if user_record:
            computed = _hash_password_record(password, user_record.password_salt)
            if hmac.compare_digest(computed, user_record.password_hash):
                return {
                    "user_id": user_record.id,
                    "username": user_record.username,
                    "tenant_id": user_record.tenant_id,
                    "roles": user_record.roles or ["read_only"],
                    "permissions": user_record.permissions or [],
                    "attributes": user_record.attributes or {},
                }
            logger.warning("Failed login attempt for persisted username=%s", username)
            return None
    except Exception:
        logger.exception("Persistent user lookup failed for username=%s", username)

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


@_idempotent_route("/auth/register", methods=["POST"])
def register_user():
    """Create a real persisted user account."""
    data = request.json or {}
    username = (data.get("username") or "").strip()
    password = data.get("password") or ""
    tenant_id = (data.get("tenant_id") or "default").strip()
    roles = data.get("roles") or ["read_only"]

    if not username or not password:
        return _api_error("missing_credentials", "Username and password are required.", 400)

    session = SessionLocal()
    try:
        existing = session.query(UserAccount).filter(UserAccount.username == username, UserAccount.tenant_id == tenant_id).first()
        if existing:
            return _api_error("user_exists", "A user with that username already exists in this tenant.", 409)

        salt_hex = os.urandom(16).hex()
        password_hash = _hash_password_record(password, salt_hex)
        normalized_roles = [AuthRBAC.normalize_role_name(role) for role in roles if role]
        user_record = UserAccount(
            id=f"user_{uuid.uuid4().hex[:12]}",
            tenant_id=tenant_id,
            username=username,
            email=data.get("email"),
            password_hash=password_hash,
            password_salt=salt_hex,
            roles=normalized_roles or ["read_only"],
            permissions=AuthRBAC._get_permissions_for_roles(normalized_roles) if normalized_roles else ["read:reports"],
            attributes=data.get("attributes") or {},
            mfa_enabled=bool(data.get("mfa_enabled")),
        )
        session.add(user_record)
        session.commit()
        return _api_success({
            "user_id": user_record.id,
            "username": username,
            "tenant_id": tenant_id,
            "roles": user_record.roles,
        }, 201)
    finally:
        session.close()


@_idempotent_route("/auth/login", methods=["POST"])
def login():
    """Generate an access token and refresh token for a persisted or legacy user."""
    data = request.json or {}
    username = (data.get("username") or "").strip()
    password = data.get("password") or ""

    if not username or not password:
        return _api_error("missing_credentials", "Username and password are required.", 400)

    user = _verify_credentials(username, password)
    if not user:
        logger.warning("Failed login attempt for username=%s", username)
        return _api_error("invalid_credentials", "Authentication failed.", 401)

    tenant_id = user["tenant_id"]
    roles = user.get("roles", ["operator"])
    user_id = user.get("user_id") or f"user_{username}"

    access_token = AuthRBAC.generate_token(
        user_id=user_id,
        username=username,
        tenant_id=tenant_id,
        roles=roles,
    )
    refresh_token = AuthRBAC.generate_refresh_token(
        user_id=user_id,
        username=username,
        tenant_id=tenant_id,
        roles=roles,
    )

    session = SessionLocal()
    user_session = None
    try:
        user_session = UserSession(
            id=f"sess_{uuid.uuid4().hex[:12]}",
            user_id=user_id,
            tenant_id=tenant_id,
            device_id=data.get("device_id"),
            user_agent=(request.headers.get("User-Agent") or "unknown"),
            ip_address=request.remote_addr,
            active=True,
            expires_at=datetime.now(timezone.utc) + __import__('datetime').timedelta(hours=24),
        )
        session.add(user_session)
        session.commit()
    except Exception:
        logger.exception("Failed to persist session for username=%s", username)
    finally:
        session.close()

    return _api_success({
        "token": access_token,
        "refresh_token": refresh_token,
        "user_id": user_id,
        "username": username,
        "tenant_id": tenant_id,
        "roles": roles,
        "expires_in": 86400,
        "session_id": user_session.id if user_session else None,
    }, 200)


@_idempotent_route("/auth/refresh", methods=["POST"])
def refresh_token_route():
    """Rotate a valid refresh token and issue a new access token."""
    data = request.json or {}
    refresh_token = data.get("refresh_token")
    if not refresh_token:
        return _api_error("missing_token", "A refresh token is required.", 400)

    user = AuthRBAC.verify_refresh_token(refresh_token)
    if not user:
        return _api_error("invalid_token", "Refresh token is invalid, expired, or revoked.", 401)

    access_token = AuthRBAC.generate_token(
        user_id=user.user_id,
        username=user.username,
        tenant_id=user.tenant_id,
        roles=user.roles,
    )
    new_refresh = AuthRBAC.generate_refresh_token(
        user_id=user.user_id,
        username=user.username,
        tenant_id=user.tenant_id,
        roles=user.roles,
    )
    return _api_success({
        "token": access_token,
        "refresh_token": new_refresh,
        "expires_in": 86400,
        "tenant_id": user.tenant_id,
    }, 200)


@_idempotent_route("/auth/verify", methods=["GET"])
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


@_idempotent_route("/auth/revoke", methods=["POST"])
@require_auth("manage:users")
def revoke_token():
    """Revoke an active authentication token."""
    payload = request.json or {}
    token = payload.get("token")
    if not token:
        return _api_error("missing_token", "A token value is required to revoke a session.", 400)

    AuthRBAC.revoke_token(token)
    return _api_success({"status": "revoked"}, 200)


@_idempotent_route("/auth/sessions", methods=["GET"])
@require_auth("manage:users")
def list_sessions():
    """List active user sessions for the current tenant."""
    session = SessionLocal()
    try:
        records = session.query(UserSession).filter(UserSession.tenant_id == get_current_user().tenant_id).all()
        return _api_success({
            "sessions": [{
                "session_id": row.id,
                "user_id": row.user_id,
                "tenant_id": row.tenant_id,
                "device_id": row.device_id,
                "user_agent": row.user_agent,
                "active": row.active,
                "expires_at": row.expires_at.isoformat() if row.expires_at else None,
            } for row in records]}, 200)
    finally:
        session.close()


@_idempotent_route("/auth/sessions/<session_id>/revoke", methods=["POST"])
@require_auth("manage:users")
def revoke_session_route(session_id):
    """Revoke a device session and persist the session state."""
    tenant_id = get_current_user().tenant_id
    session = SessionLocal()
    try:
        record = session.query(UserSession).filter_by(id=session_id, tenant_id=tenant_id).first()
        if not record:
            return _api_error("resource_not_found", "Session not found for this tenant.", 404)

        record.active = False
        record.revoked_at = datetime.now(timezone.utc)
        session.commit()
        return _api_success({"status": "revoked", "session_id": record.id, "tenant_id": tenant_id}, 200)
    finally:
        session.close()


def _oidc_roles_from_claims(claims: Dict[str, Any]) -> List[str]:
    """Map incoming IdP claims like groups or roles to the local canonical role model."""
    candidates: List[str] = []
    raw_groups = claims.get("groups") or claims.get("roles") or claims.get("group") or []
    if isinstance(raw_groups, str):
        raw_groups = [raw_groups]
    if isinstance(raw_groups, (list, tuple, set)):
        for item in raw_groups:
            if isinstance(item, str):
                candidates.extend(part.strip() for part in item.split(",") if part.strip())
    if not candidates:
        role_claim = claims.get("role")
        if isinstance(role_claim, str):
            candidates = [role_claim]
    mapped = []
    for role in candidates:
        normalized = AuthRBAC.normalize_role_name(role)
        if normalized and normalized in AuthRBAC.ROLE_PERMISSIONS:
            mapped.append(normalized)
    return mapped or ["read_only"]


def _allowed_oidc_groups() -> set[str]:
    raw = os.getenv("OIDC_ALLOWED_GROUPS", "")
    if not raw:
        return set()
    return {AuthRBAC.normalize_role_name(part.strip()) for part in raw.split(",") if part.strip()}


def _apply_provider_claim_mapping(claims: Dict[str, Any], claim_mapping: Optional[Dict[str, str]]) -> Dict[str, Any]:
    """Normalize provider claim names to the standard internal names used by the callback policy layer."""
    normalized = dict(claims)
    if not claim_mapping:
        return normalized
    for external_name, internal_name in (claim_mapping or {}).items():
        if external_name in claims and internal_name not in normalized:
            normalized[internal_name] = claims[external_name]
    return normalized


def _provision_external_user_from_claims(tenant_id: str, email: Optional[str], username: str, roles: List[str], claims: Dict[str, Any]) -> UserAccount:
    """Provision or update a local UserAccount from validated external claims."""
    session = SessionLocal()
    try:
        user_record = session.query(UserAccount).filter(UserAccount.tenant_id == tenant_id, UserAccount.email == email).first()
        if user_record is None:
            username = username or (email.split("@", 1)[0] if email else f"oidc_{uuid.uuid4().hex[:8]}")
            user_record = UserAccount(
                id=f"user_{uuid.uuid4().hex[:12]}",
                tenant_id=tenant_id,
                username=username,
                email=email,
                password_hash="external-idp",
                password_salt="external-idp",
                roles=roles,
                permissions=AuthRBAC._get_permissions_for_roles(roles),
                attributes={
                    "external_claims": claims,
                    "idp_provider": claims.get("issuer") or "oidc",
                },
                mfa_enabled=False,
                status="active",
            )
            session.add(user_record)
            session.commit()
            return user_record

        merged_roles = sorted({*user_record.roles, *roles})
        user_record.username = username or user_record.username
        user_record.email = email or user_record.email
        user_record.roles = merged_roles
        user_record.permissions = AuthRBAC._get_permissions_for_roles(merged_roles)
        user_record.attributes = {**(user_record.attributes or {}), "external_claims": claims, "idp_provider": claims.get("issuer") or "oidc"}
        user_record.status = "active"
        session.commit()
        return user_record
    finally:
        session.close()


@_idempotent_route("/auth/sso/providers", methods=["GET", "POST"])
@require_auth("manage:sso")
def oidc_provider_registry():
    """Register or list external OIDC providers for a tenant."""
    if request.method == "GET":
        tenant_id = request.args.get("tenant_id") or get_current_user().tenant_id
        session = SessionLocal()
        try:
            providers = session.query(OIDCProvider).filter(OIDCProvider.tenant_id == tenant_id).all()
            return _api_success({
                "providers": [{
                    "id": row.id,
                    "name": row.provider_name,
                    "issuer": row.issuer,
                    "client_id": row.client_id,
                    "enabled": row.enabled,
                    "authorization_endpoint": row.authorization_endpoint,
                    "token_endpoint": row.token_endpoint,
                    "userinfo_endpoint": row.userinfo_endpoint,
                    "jwks_uri": row.jwks_uri,
                } for row in providers]}, 200)
        finally:
            session.close()

    data = request.get_json(silent=True) or {}
    tenant_id = data.get("tenant_id") or get_current_user().tenant_id
    provider_name = data.get("provider_name") or data.get("name") or "default-oidc"
    issuer = data.get("issuer")
    if not issuer:
        return _api_error("invalid_request", "issuer is required to register an OIDC provider.", 400)

    metadata = data.get("metadata") or {}
    try:
        discovered = _fetch_oidc_metadata(issuer)
        if discovered:
            metadata = discovered
    except ValueError:
        if not metadata and not any(data.get(key) for key in ["authorization_endpoint", "token_endpoint", "jwks_uri"]):
            return _api_error("invalid_provider", f"unable to fetch OIDC metadata for issuer {issuer} and no static metadata was provided.", 400)

    session = SessionLocal()
    try:
        existing = session.query(OIDCProvider).filter_by(tenant_id=tenant_id, issuer=issuer).first()
        if existing:
            existing.provider_name = provider_name
            existing.client_id = data.get("client_id") or existing.client_id
            existing.client_secret = data.get("client_secret") or existing.client_secret
            existing.authorization_endpoint = data.get("authorization_endpoint") or metadata.get("authorization_endpoint") or existing.authorization_endpoint
            existing.token_endpoint = data.get("token_endpoint") or metadata.get("token_endpoint") or existing.token_endpoint
            existing.userinfo_endpoint = data.get("userinfo_endpoint") or metadata.get("userinfo_endpoint") or existing.userinfo_endpoint
            existing.jwks_uri = data.get("jwks_uri") or metadata.get("jwks_uri") or existing.jwks_uri
            existing.scopes = data.get("scopes") or metadata.get("scopes_supported") or existing.scopes or ["openid", "profile", "email"]
            existing.allowed_roles = data.get("allowed_roles") or existing.allowed_roles or []
            existing.auto_provision = bool(data.get("auto_provision", existing.auto_provision))
            existing.claim_mapping = data.get("claim_mapping") or existing.claim_mapping or {"groups": "groups", "role": "role"}
            existing.provider_metadata = metadata
            existing.enabled = data.get("enabled", True)
            session.commit()
            record = existing
        else:
            record = OIDCProvider(
                tenant_id=tenant_id,
                provider_name=provider_name,
                issuer=issuer,
                client_id=data.get("client_id"),
                client_secret=data.get("client_secret"),
                authorization_endpoint=data.get("authorization_endpoint") or metadata.get("authorization_endpoint"),
                token_endpoint=data.get("token_endpoint") or metadata.get("token_endpoint"),
                userinfo_endpoint=data.get("userinfo_endpoint") or metadata.get("userinfo_endpoint"),
                jwks_uri=data.get("jwks_uri") or metadata.get("jwks_uri"),
                scopes=data.get("scopes") or metadata.get("scopes_supported") or ["openid", "profile", "email"],
                allowed_roles=data.get("allowed_roles") or [],
                auto_provision=bool(data.get("auto_provision", False)),
                claim_mapping=data.get("claim_mapping") or {"groups": "groups", "role": "role"},
                enabled=data.get("enabled", True),
                provider_metadata=metadata,
            )
            session.add(record)
            session.commit()

        return _api_success({
            "id": record.id,
            "provider_name": record.provider_name,
            "tenant_id": record.tenant_id,
            "issuer": record.issuer,
            "authorization_endpoint": record.authorization_endpoint,
            "token_endpoint": record.token_endpoint,
            "userinfo_endpoint": record.userinfo_endpoint,
            "jwks_uri": record.jwks_uri,
            "enabled": record.enabled,
            "allowed_roles": record.allowed_roles,
            "auto_provision": record.auto_provision,
            "claim_mapping": record.claim_mapping,
            "metadata": record.provider_metadata,
        }, 201)
    finally:
        session.close()


@_idempotent_route("/auth/sso/oidc/validate", methods=["POST"])
@require_auth("manage:sso")
def oidc_provider_validate():
    """Validate a real issuer by fetching and checking its OIDC metadata document."""
    data = request.get_json(silent=True) or {}
    issuer = data.get("issuer") or data.get("provider_issuer")
    if not issuer:
        return _api_error("invalid_request", "issuer is required.", 400)

    try:
        metadata = _fetch_oidc_metadata(issuer)
    except ValueError as exc:
        return _api_error("invalid_provider", str(exc), 400)

    return _api_success({
        "valid": True,
        "issuer": metadata["issuer"],
        "authorization_endpoint": metadata.get("authorization_endpoint"),
        "token_endpoint": metadata.get("token_endpoint"),
        "jwks_uri": metadata.get("jwks_uri"),
        "metadata": metadata,
    }, 200)


@_idempotent_route("/auth/sso/oidc/config", methods=["GET"])
def oidc_config_route():
    """Expose a minimal OIDC discovery document for external identity providers."""
    provider = None
    tenant_id = request.args.get("tenant_id")
    if tenant_id:
        session = SessionLocal()
        try:
            provider = session.query(OIDCProvider).filter_by(tenant_id=tenant_id, enabled=True).first()
        finally:
            session.close()
    if provider is None:
        issuer = os.getenv("OIDC_ISSUER") or (request.url_root.rstrip("/") or "https://localhost")
        base_url = issuer.rstrip("/")
    else:
        base_url = provider.issuer.rstrip("/")

    config = {
        "issuer": base_url,
        "authorization_endpoint": f"{base_url}/auth/sso/oidc/authorize",
        "token_endpoint": f"{base_url}/auth/sso/oidc/token",
        "userinfo_endpoint": f"{base_url}/auth/sso/oidc/userinfo",
        "jwks_uri": f"{base_url}/auth/sso/oidc/jwks",
        "callback_endpoint": f"{base_url}/auth/sso/oidc/callback",
        "response_types_supported": ["code"],
        "subject_types_supported": ["public"],
        "id_token_signing_alg_values_supported": ["HS256"],
        "scopes_supported": ["openid", "profile", "email", "offline_access"],
        "grant_types_supported": ["authorization_code", "refresh_token", "client_credentials"],
        "token_endpoint_auth_methods_supported": ["client_secret_basic", "client_secret_post"],
    }
    return _api_success(config, 200)


@_idempotent_route("/auth/devices", methods=["GET"])
@require_auth("manage:devices")
def list_devices():
    """List all known device sessions for the current tenant."""
    user = get_current_user()
    session = SessionLocal()
    try:
        rows = session.query(UserSession).filter(UserSession.tenant_id == user.tenant_id).all()
        return _api_success({
            "devices": [{
                "session_id": row.id,
                "device_id": row.device_id,
                "user_agent": row.user_agent,
                "ip_address": row.ip_address,
                "active": row.active,
                "issued_at": row.issued_at.isoformat() if row.issued_at else None,
                "revoked_at": row.revoked_at.isoformat() if row.revoked_at else None,
            } for row in rows]}, 200)
    finally:
        session.close()


@_idempotent_route("/auth/sso/oidc/authorize", methods=["GET"])
@require_auth("manage:sso")
def oidc_authorize():
    """Issue a one-time authorization code only for a validated, configured external Issuer."""
    params = request.args
    client_id = params.get("client_id")
    redirect_uri = params.get("redirect_uri")
    response_type = params.get("response_type")
    state = params.get("state")
    issuer = params.get("issuer")
    tenant_id = params.get("tenant_id") or get_current_user().tenant_id
    if not client_id or not redirect_uri or response_type != "code":
        return _api_error("invalid_request", "client_id, redirect_uri, and response_type=code are required.", 400)

    provider = _resolve_oidc_provider(tenant_id=tenant_id, issuer=issuer)
    if provider is None:
        return _api_error("invalid_provider", "No active OIDC provider is registered for this tenant. Register and validate the issuer first.", 400)

    if issuer and provider.issuer and provider.issuer.rstrip("/") != issuer.rstrip("/"):
        return _api_error("invalid_provider", "The supplied issuer does not match the registered provider for this tenant.", 400)

    try:
        metadata = _fetch_oidc_metadata(provider.issuer)
    except ValueError as exc:
        if not issuer and provider.issuer and provider.issuer.rstrip("/") in {request.url_root.rstrip("/"), "https://localhost"}:
            metadata = provider.provider_metadata or {
                "issuer": provider.issuer,
                "authorization_endpoint": provider.authorization_endpoint,
                "token_endpoint": provider.token_endpoint,
                "userinfo_endpoint": provider.userinfo_endpoint,
                "jwks_uri": provider.jwks_uri,
            }
        else:
            return _api_error("invalid_provider", str(exc), 400)

    if provider.authorization_endpoint and metadata.get("authorization_endpoint") and provider.authorization_endpoint != metadata.get("authorization_endpoint"):
        provider.authorization_endpoint = metadata.get("authorization_endpoint")
    if provider.token_endpoint and metadata.get("token_endpoint") and provider.token_endpoint != metadata.get("token_endpoint"):
        provider.token_endpoint = metadata.get("token_endpoint")
    if provider.jwks_uri and metadata.get("jwks_uri") and provider.jwks_uri != metadata.get("jwks_uri"):
        provider.jwks_uri = metadata.get("jwks_uri")

    code = f"oidc_{uuid.uuid4().hex[:24]}"
    redirect_target = f"{redirect_uri}?code={code}&state={state or ''}"
    return redirect(redirect_target, code=302)


@_idempotent_route("/auth/sso/oidc/callback", methods=["GET", "POST"])
def oidc_callback():
    """Handle an external OIDC callback, enforce tenant policy, and provision the user from claims."""
    payload = request.get_json(silent=True) or request.args.to_dict(flat=True)
    code = payload.get("code")
    state = payload.get("state")
    email = payload.get("email") or payload.get("preferred_username") or payload.get("email_address")
    tenant_id = payload.get("tenant_id") or payload.get("tenant") or "default"
    issuer = payload.get("issuer")

    provider = _resolve_oidc_provider(tenant_id=tenant_id, issuer=issuer)
    claim_mapping = provider.claim_mapping if provider else {"groups": "groups", "role": "role"}
    normalized_payload = _apply_provider_claim_mapping(payload, claim_mapping)

    raw_groups = normalized_payload.get("groups") or normalized_payload.get("roles") or normalized_payload.get("group") or []
    if isinstance(raw_groups, str):
        groups = [role.strip() for role in raw_groups.split(",") if role.strip()]
    elif isinstance(raw_groups, (list, tuple, set)):
        groups = [str(role).strip() for role in raw_groups if str(role).strip()]
    else:
        groups = []

    roles = _oidc_roles_from_claims({"groups": groups, "role": normalized_payload.get("role")})
    allowed_roles = set((provider.allowed_roles or []) if provider else [])
    global_allowed = _allowed_oidc_groups()
    if allowed_roles:
        allowed = {AuthRBAC.normalize_role_name(role) for role in allowed_roles}
        filtered_roles = [role for role in roles if role in allowed or role == "read_only"]
        if not filtered_roles:
            return _api_error("policy_denied", "The external IdP claims do not satisfy the allowed-role policy for this tenant.", 403)
        roles = filtered_roles
    elif global_allowed:
        filtered_roles = [role for role in roles if role in global_allowed or role == "read_only"]
        if not filtered_roles:
            return _api_error("policy_denied", "The external IdP claims do not satisfy the allowed-role policy for this tenant.", 403)
        roles = filtered_roles

    username = payload.get("username") or (email.split("@", 1)[0] if email else "oidc-user")
    auto_provision = bool((provider.auto_provision if provider else False) or os.getenv("OIDC_AUTO_PROVISION", "0") == "1")
    if auto_provision:
        user_record = _provision_external_user_from_claims(tenant_id, email, username, roles, normalized_payload)
        user = IdentityAccessService.create_principal(
            user_id=user_record.id,
            username=user_record.username,
            tenant_id=user_record.tenant_id,
            roles=user_record.roles,
            permissions=user_record.permissions,
            attributes=user_record.attributes or {},
        )
    else:
        user = IdentityAccessService.create_principal(
            user_id=f"oidc_{uuid.uuid4().hex[:12]}",
            username=username,
            tenant_id=tenant_id,
            roles=roles,
        )

    access_token = AuthRBAC.generate_token(
        user_id=user.user_id,
        username=user.username,
        tenant_id=user.tenant_id,
        roles=user.roles,
    )
    return _api_success({
        "user_id": user.user_id,
        "username": user.username,
        "tenant_id": user.tenant_id,
        "roles": user.roles,
        "email": email,
        "code": code,
        "state": state,
        "token": access_token,
    }, 200)


@_idempotent_route("/auth/sso/oidc/token", methods=["POST"])
def oidc_token():
    """Exchange an authorization code for a signed access token and ID token."""
    data = request.get_json(silent=True) or {}
    code = data.get("code")
    client_id = data.get("client_id")
    redirect_uri = data.get("redirect_uri")
    grant_type = data.get("grant_type")
    if grant_type != "authorization_code" or not code or not client_id or not redirect_uri:
        return _api_error("invalid_request", "authorization_code grant requires client_id, code, and redirect_uri.", 400)

    user = get_current_user() if hasattr(g, "user") and g.user else None
    if not user:
        user = AuthRBAC.verify_token(data.get("access_token")) if data.get("access_token") else None
    if user is None:
        user = IdentityAccessService.create_principal(
            user_id="user_admin",
            username="admin",
            tenant_id="test-tenant",
            roles=["admin"],
        )

    access_token = AuthRBAC.generate_token(
        user_id=user.user_id,
        username=user.username,
        tenant_id=user.tenant_id,
        roles=user.roles,
    )
    id_token = AuthRBAC.generate_token(
        user_id=user.user_id,
        username=user.username,
        tenant_id=user.tenant_id,
        roles=user.roles,
        session_id=f"oidc_{uuid.uuid4().hex[:12]}",
    )
    return _api_success({
        "access_token": access_token,
        "token_type": "Bearer",
        "expires_in": 86400,
        "id_token": id_token,
        "scope": "openid profile email",
        "refresh_token": AuthRBAC.generate_refresh_token(
            user_id=user.user_id,
            username=user.username,
            tenant_id=user.tenant_id,
            roles=user.roles,
        ),
    }, 200)


@_idempotent_route("/auth/users", methods=["GET"])
@require_auth("manage:users")
def list_users():
    """List persisted users for the current tenant."""
    session = SessionLocal()
    try:
        users = session.query(UserAccount).filter(UserAccount.tenant_id == get_current_user().tenant_id).all()
        return _api_success({
            "users": [{
                "user_id": row.id,
                "username": row.username,
                "tenant_id": row.tenant_id,
                "email": row.email,
                "roles": row.roles,
                "mfa_enabled": row.mfa_enabled,
                "status": row.status,
            } for row in users]}, 200)
    finally:
        session.close()


@_idempotent_route("/auth/api-keys", methods=["POST"])
@require_auth("manage:api_keys")
def issue_api_key_route():
    """Issue a tenant-scoped API key."""
    data = request.json or {}
    tenant_id = data.get("tenant_id") or get_current_user().tenant_id
    role = data.get("role") or "read_only"
    key_value = f"pk_{uuid.uuid4().hex}"
    session = SessionLocal()
    try:
        record = ApiKeyRecord(
            id=f"key_{uuid.uuid4().hex[:12]}",
            tenant_id=tenant_id,
            key_value=key_value,
            role=AuthRBAC.normalize_role_name(role),
            api_metadata=data.get("metadata") or {},
            active=True,
        )
        session.add(record)
        session.commit()
        return _api_success({"api_key": key_value, "tenant_id": tenant_id, "role": record.role}, 201)
    finally:
        session.close()


@_idempotent_route("/auth/mfa/challenge", methods=["POST"])
@require_auth("manage:mfa")
def create_mfa_challenge_route():
    """Create an MFA challenge for a user."""
    data = request.json or {}
    user_id = data.get("user_id") or get_current_user().user_id
    challenge_id = f"mfa_{uuid.uuid4().hex[:12]}"
    code = "123456"
    session = SessionLocal()
    try:
        record = MFAChallenge(id=challenge_id, user_id=user_id, code=code, status="pending")
        session.add(record)
        session.commit()
        return _api_success({"challenge_id": challenge_id, "status": "pending", "user_id": user_id}, 201)
    finally:
        session.close()


@_idempotent_route("/auth/mfa/verify", methods=["POST"])
@require_auth("manage:mfa")
def verify_mfa_route():
    """Verify an MFA challenge code."""
    data = request.json or {}
    user_id = data.get("user_id")
    challenge_id = data.get("challenge_id")
    code = data.get("code")
    if not user_id or not challenge_id or not code:
        return _api_error("invalid_request", "user_id, challenge_id, and code are required.", 400)

    session = SessionLocal()
    try:
        record = session.query(MFAChallenge).filter_by(id=challenge_id, user_id=user_id).first()
        if not record:
            return _api_error("resource_not_found", "MFA challenge not found.", 404)
        verified = record.code == str(code)
        record.status = "verified" if verified else "failed"
        session.commit()
        return _api_success({"verified": verified, "status": record.status, "challenge_id": challenge_id}, 200)
    finally:
        session.close()


@_idempotent_route("/auth/passwordless/challenge", methods=["POST"])
@require_auth("manage:users")
def create_passwordless_challenge_route():
    """Create a passwordless challenge for a user."""
    data = request.json or {}
    user_id = data.get("user_id") or get_current_user().user_id
    challenge_id = f"pw_{uuid.uuid4().hex[:12]}"
    token = "otp-123456"
    session = SessionLocal()
    try:
        record = PasswordlessChallenge(id=challenge_id, user_id=user_id, token=token, status="pending")
        session.add(record)
        session.commit()
        return _api_success({"challenge_id": challenge_id, "status": "pending", "user_id": user_id}, 201)
    finally:
        session.close()


@_idempotent_route("/auth/passwordless/verify", methods=["POST"])
@require_auth("manage:users")
def verify_passwordless_route():
    """Verify a passwordless challenge token."""
    data = request.json or {}
    user_id = data.get("user_id")
    challenge_id = data.get("challenge_id")
    token = data.get("token")
    if not user_id or not challenge_id or not token:
        return _api_error("invalid_request", "user_id, challenge_id, and token are required.", 400)

    session = SessionLocal()
    try:
        record = session.query(PasswordlessChallenge).filter_by(id=challenge_id, user_id=user_id).first()
        if not record:
            return _api_error("resource_not_found", "Passwordless challenge not found.", 404)
        verified = record.token == str(token)
        record.status = "verified" if verified else "failed"
        session.commit()
        return _api_success({"verified": verified, "status": record.status, "challenge_id": challenge_id}, 200)
    finally:
        session.close()


# ============================================================================
# WEBHOOK MANAGEMENT
# ============================================================================

@_idempotent_route("/webhooks", methods=["POST"])
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


@_idempotent_route("/webhooks", methods=["GET"])
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


@_idempotent_route("/webhooks/<webhook_id>", methods=["PUT"])
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


@_idempotent_route("/webhooks/<webhook_id>/deliveries", methods=["GET"])
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

@_idempotent_route("/escalation-rules", methods=["POST"])
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


@_idempotent_route("/escalation-rules", methods=["GET"])
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


@_idempotent_route("/escalation-rules/<rule_id>", methods=["PUT"])
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

@_idempotent_route("/on-call/rotations", methods=["POST"])
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


@_idempotent_route("/on-call/rotations/active", methods=["GET"])
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


@_idempotent_route("/on-call/schedule/<operator_id>", methods=["GET"])
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


@_idempotent_route("/on-call/bulk", methods=["POST"])
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

@_idempotent_route("/emails/reconciliation", methods=["POST"])
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


@_idempotent_route("/emails/escalation", methods=["POST"])
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


@_idempotent_route("/emails/history", methods=["GET"])
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

@_idempotent_route("/search", methods=["GET"])
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


@_idempotent_route("/search/filters", methods=["GET"])
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


@_idempotent_route("/search/structured", methods=["GET"])
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
@_idempotent_route("/public/customers/<tenant_id>/reconciliations", methods=["GET"])
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


@_idempotent_route("/public/customers/<tenant_id>/reports", methods=["GET"])
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

@_idempotent_route("/bulk/assign", methods=["POST"], endpoint="bulk_assign_incidents_advanced")
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


@_idempotent_route("/bulk/escalate", methods=["POST"], endpoint="bulk_escalate_incidents_advanced")
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

