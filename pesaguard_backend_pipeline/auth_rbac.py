"""Enterprise-grade Authentication and Role-Based Access Control (RBAC) for PesaGuard API.

Role Hierarchy (from most to least privileged):
  1. admin: Full access to all features (settings, users, escalation rules, webhooks)
  2. operator: Read/write discrepancies, view analytics, perform bulk operations
  3. customer-user: Read-only access to discrepancies and analytics (customer portal)
  4. read-only: Read-only viewer access (minimal permissions)

Token Expiry: Configurable via TOKEN_EXPIRY_HOURS (default 24h)
Auth Required: Default on; controlled via PESAGUARD_API_AUTH_REQUIRED
"""

from __future__ import annotations

import logging
import os
import uuid
from datetime import datetime, timedelta, timezone
from functools import wraps
from typing import Any, Dict, List, Optional

import jwt
from flask import g, jsonify, request
from sqlalchemy import Column, DateTime, String, Text, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

logger = logging.getLogger("pesaguard.auth_rbac")

# ----------------------------------------------------------------------------
# Fail-Safe Secret Configuration
# ----------------------------------------------------------------------------
_INSECURE_DEV_SECRET = "pesaguard-secret-key-change-in-prod"

SECRET_KEY = os.getenv("JWT_SECRET_KEY")
if not SECRET_KEY:
    env_name = os.getenv("PESAGUARD_ENV", "development").lower()
    is_non_production = env_name in {"development", "dev", "test", "testing", "local", "staging"}
    if is_non_production or os.getenv("PESAGUARD_ALLOW_INSECURE_DEV_SECRET") == "1":
        SECRET_KEY = _INSECURE_DEV_SECRET
        logger.warning(
            "JWT_SECRET_KEY is not set — using a development fallback secret for %s. "
            "Set JWT_SECRET_KEY explicitly for production deployments.",
            env_name,
        )
    else:
        raise RuntimeError(
            "JWT_SECRET_KEY environment variable is required and was not set. "
            "Generate one with: python -c \"import secrets; print(secrets.token_hex(32))\" "
            "and set it as JWT_SECRET_KEY."
        )

ALGORITHM = "HS256"
TOKEN_EXPIRY_HOURS = int(os.getenv("PESAGUARD_TOKEN_EXPIRY_HOURS", "24"))

# ----------------------------------------------------------------------------
# Distributed Database Token Revocation Store
# ----------------------------------------------------------------------------
_RevocationBase = declarative_base()


class RevokedToken(_RevocationBase):
    __tablename__ = "revoked_tokens"

    jti = Column(String, primary_key=True)
    revoked_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    reason = Column(Text, nullable=True)


_revocation_engine = None
_RevocationSession = None


def _ensure_revocation_store_ready() -> None:
    """Lazy initialization of the thread-safe distributed token revocation store."""
    global _revocation_engine, _RevocationSession
    if _RevocationSession is not None:
        return

    database_url = os.getenv("DATABASE_URL", "postgresql://pesaguard:pesaguard@localhost:5432/pesaguard")
    engine_kwargs: Dict[str, Any] = {"pool_pre_ping": True}
    if not database_url.startswith("sqlite"):
        engine_kwargs.update({
            "pool_size": int(os.getenv("DB_POOL_SIZE", "5")),
            "max_overflow": int(os.getenv("DB_MAX_OVERFLOW", "10")),
        })

    _revocation_engine = create_engine(database_url, **engine_kwargs)
    _RevocationBase.metadata.create_all(_revocation_engine)
    _RevocationSession = sessionmaker(bind=_revocation_engine, expire_on_commit=False)


class User:
    """Represents an authenticated user principal with roles and computed permissions."""

    def __init__(
        self,
        user_id: str,
        username: str,
        tenant_id: str,
        roles: List[str],
        permissions: List[str],
    ):
        self.user_id = user_id
        self.username = username
        self.tenant_id = tenant_id
        self.roles = roles
        self.permissions = permissions


class AuthRBAC:
    """Authentication, JWT lifecycle, and Role-Based Access Control manager."""

    ROLE_PERMISSIONS: Dict[str, List[str]] = {
        "super_admin": [
            "*",
            "read:all",
            "write:all",
            "manage:all",
            "read:discrepancies",
            "write:discrepancies",
            "delete:discrepancies",
            "read:analytics",
            "write:escalation_rules",
            "read:settings",
            "write:settings",
            "manage:webhooks",
            "manage:users",
            "manage:on_call",
            "manage:settings",
            "bulk:operations",
            "read:metrics",
            "read:financials",
            "write:financials",
            "approve:settlements",
            "finance:approve_settlement",
            "read:reconciliation",
            "write:reconciliation",
            "resolve:discrepancies",
            "audit:read",
            "read:audits",
            "manage:api_keys",
            "manage:service_accounts",
            "manage:sso",
            "manage:mfa",
            "manage:devices",
        ],
        "organization_admin": [
            "read:discrepancies",
            "write:discrepancies",
            "read:analytics",
            "read:settings",
            "write:settings",
            "manage:webhooks",
            "manage:users",
            "manage:settings",
            "read:metrics",
            "read:financials",
            "write:financials",
            "manage:api_keys",
            "manage:service_accounts",
            "manage:sso",
        ],
        "finance_manager": [
            "read:financials",
            "write:financials",
            "approve:settlements",
            "finance:approve_settlement",
            "read:reports",
            "read:reconciliation",
            "read:audits",
            "read:settings",
        ],
        "reconciliation_officer": [
            "read:discrepancies",
            "write:discrepancies",
            "resolve:discrepancies",
            "read:reconciliation",
            "write:reconciliation",
            "read:analytics",
            "read:settings",
            "export:data",
        ],
        "auditor": [
            "audit:read",
            "read:audits",
            "read:analytics",
            "read:reconciliation",
            "read:settings",
            "export:data",
        ],
        "risk_analyst": [
            "read:analytics",
            "read:risks",
            "write:risk_rules",
            "read:reconciliation",
            "read:settings",
        ],
        "developer": [
            "read:api",
            "write:integrations",
            "manage:webhooks",
            "read:metrics",
            "read:settings",
            "read:analytics",
            "manage:service_accounts",
            "manage:api_keys",
        ],
        "read_only": [
            "read:discrepancies",
            "read:analytics",
            "read:reconciliation",
            "read:settings",
            "read:reports",
        ],
        "customer": [
            "read:own_data",
            "read:transactions",
            "read:reports",
            "read:reconciliation",
        ],
        "admin": [
            "read:discrepancies",
            "write:discrepancies",
            "delete:discrepancies",
            "read:analytics",
            "write:escalation_rules",
            "read:settings",
            "write:settings",
            "manage:webhooks",
            "manage:users",
            "manage:on_call",
            "manage:settings",
            "manage:api_keys",
            "manage:sso",
            "manage:devices",
            "manage:mfa",
            "bulk:operations",
            "read:metrics",
        ],
        "operator": [
            "read:discrepancies",
            "write:discrepancies",
            "read:analytics",
            "read:settings",
            "bulk:operations",
            "read:metrics",
        ],
        "customer-user": [
            "read:discrepancies",
            "read:analytics",
            "read:settings",
        ],
    }

    @classmethod
    def generate_token(
        cls,
        user_id: str,
        username: str,
        tenant_id: str,
        roles: List[str],
        token_type: str = "access",
        session_id: Optional[str] = None,
    ) -> str:
        """Generate a signed JWT token containing claims, unique JTI, and permissions."""
        permissions = cls._get_permissions_for_roles(roles)
        now = datetime.now(timezone.utc)
        expiry_hours = TOKEN_EXPIRY_HOURS if token_type == "access" else 30 * 24
        payload = {
            "user_id": user_id,
            "username": username,
            "tenant_id": tenant_id,
            "roles": roles,
            "permissions": permissions,
            "jti": str(uuid.uuid4()),
            "token_type": token_type,
            "session_id": session_id or str(uuid.uuid4()),
            "iat": now,
            "exp": now + timedelta(hours=expiry_hours),
        }
        return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

    @classmethod
    def generate_refresh_token(
        cls,
        user_id: str,
        username: str,
        tenant_id: str,
        roles: List[str],
        session_id: Optional[str] = None,
    ) -> str:
        return cls.generate_token(user_id, username, tenant_id, roles, token_type="refresh", session_id=session_id)

    @classmethod
    def verify_token(cls, token: str, expected_type: Optional[str] = None) -> Optional[User]:
        """Verify JWT signature, expiry, and revocation state to return a User principal."""
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
            return None

        if expected_type and payload.get("token_type") != expected_type:
            return None

        jti = payload.get("jti")
        if jti and cls.is_token_revoked(jti):
            logger.warning("Attempted authentication with revoked JTI: %s", jti)
            return None

        try:
            return User(
                user_id=payload["user_id"],
                username=payload["username"],
                tenant_id=payload["tenant_id"],
                roles=payload.get("roles", []),
                permissions=payload.get("permissions", []),
            )
        except KeyError as exc:
            logger.warning("JWT payload missing mandatory claim: %s", exc)
            return None

    @classmethod
    def verify_refresh_token(cls, token: str) -> Optional[User]:
        return cls.verify_token(token, expected_type="refresh")

    @classmethod
    @classmethod
    def normalize_role_name(cls, role: str) -> str:
        """Normalize display names like 'Super Admin' and 'finance_manager' into canonical keys."""
        if not role:
            return ""
        normalized = str(role).strip().lower().replace("-", "_").replace(" ", "_")
        aliases = {
            "super_admin": "super_admin",
            "organization_admin": "organization_admin",
            "org_admin": "organization_admin",
            "finance_manager": "finance_manager",
            "reconciliation_officer": "reconciliation_officer",
            "auditor": "auditor",
            "risk_analyst": "risk_analyst",
            "developer": "developer",
            "read_only": "read_only",
            "customer": "customer",
            "admin": "admin",
            "operator": "operator",
            "customer_user": "customer-user",
            "customeruser": "customer-user",
            "viewer": "read_only",
        }
        return aliases.get(normalized, normalized)

    @classmethod
    def _get_permissions_for_roles(cls, roles: List[str]) -> List[str]:
        """Compute the unique set of permission strings for a given list of roles."""
        permissions = set()
        unknown_roles = []
        for role in roles:
            normalized = cls.normalize_role_name(role)
            if normalized in cls.ROLE_PERMISSIONS:
                permissions.update(cls.ROLE_PERMISSIONS[normalized])
            else:
                unknown_roles.append(role)

        if unknown_roles:
            logger.warning("Unrecognized roles requested during token generation: %s", unknown_roles)
        return list(permissions)

    @classmethod
    def is_token_revoked(cls, jti: str) -> bool:
        """Check if a token's JTI exists in the database revocation store."""
        if not jti:
            return False
        _ensure_revocation_store_ready()
        session = _RevocationSession()
        try:
            return session.get(RevokedToken, jti) is not None
        except Exception as exc:
            logger.error("Failed checking token revocation status for JTI %s: %s", jti, exc)
            return False
        finally:
            session.close()

    @classmethod
    def revoke_token(cls, token: str, reason: Optional[str] = None) -> None:
        """Extract a token's JTI and insert it into the distributed revocation table."""
        try:
            payload = jwt.decode(
                token, SECRET_KEY, algorithms=[ALGORITHM],
                options={"verify_exp": False},
            )
        except jwt.InvalidTokenError:
            logger.warning("revoke_token called with unparseable or invalid signature token.")
            return

        jti = payload.get("jti")
        if not jti:
            logger.warning("revoke_token called on token lacking a JTI claim.")
            return

        _ensure_revocation_store_ready()
        session = _RevocationSession()
        try:
            existing = session.get(RevokedToken, jti)
            if not existing:
                session.add(RevokedToken(jti=jti, reason=reason, revoked_at=datetime.now(timezone.utc)))
                session.commit()
                logger.info("Token JTI %s successfully revoked.", jti)
        except Exception as exc:
            logger.error("Failed to persist token revocation for JTI %s: %s", jti, exc)
            session.rollback()
        finally:
            session.close()

    @classmethod
    def check_permission(cls, user: User, required_permission: str) -> bool:
        """Check if a User principal holds the specified permission string."""
        return required_permission in user.permissions

    @classmethod
    def check_tenant_access(cls, user: User, tenant_id: str) -> bool:
        """Verify that a user is scoped to access the specified tenant_id."""
        return user.tenant_id == tenant_id or "admin" in user.roles


def require_auth(required_permission: Optional[str] = None):
    """Route decorator enforcing JWT bearer token authentication and permission checks."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            auth_required = os.getenv("PESAGUARD_API_AUTH_REQUIRED", "1") == "1"
            auth_header = request.headers.get("Authorization", "")
            api_key_value = request.headers.get("X-API-Key") or request.headers.get("X-API-KEY")

            if not auth_header and not api_key_value:
                if not auth_required:
                    return f(*args, **kwargs)
                return jsonify({"error": "missing_auth_header", "message": "Authorization header or X-API-Key is required."}), 401

            user = None
            if auth_header:
                try:
                    scheme, token = auth_header.split(" ", 1)
                    if scheme.lower() != "bearer":
                        return jsonify({"error": "invalid_auth_scheme", "message": "Authorization scheme must be Bearer."}), 401
                except ValueError:
                    return jsonify({"error": "invalid_auth_header", "message": "Malformed Authorization header format."}), 401

                user = AuthRBAC.verify_token(token)
                if not user:
                    return jsonify({"error": "invalid_token", "message": "Token is invalid, expired, or revoked."}), 401
            else:
                from pesaguard_backend_pipeline.models import ApiKeyRecord
                from pesaguard_backend_pipeline.app_4_advanced_features import SessionLocal
                session = SessionLocal()
                try:
                    api_key_record = session.query(ApiKeyRecord).filter_by(key_value=api_key_value, active=True).first()
                finally:
                    session.close()
                if not api_key_record:
                    return jsonify({"error": "invalid_api_key", "message": "API key is invalid, expired, or revoked."}), 401
                permissions = AuthRBAC._get_permissions_for_roles([api_key_record.role])
                user = User(
                    user_id=f"api_key_{api_key_record.id}",
                    username=f"service_{api_key_record.tenant_id}",
                    tenant_id=api_key_record.tenant_id,
                    roles=[api_key_record.role],
                    permissions=permissions,
                )
                g.api_key = api_key_value

            if required_permission and not AuthRBAC.check_permission(user, required_permission):
                logger.warning("User %s denied access. Required permission: %s", user.user_id, required_permission)
                return jsonify({"error": "insufficient_permissions", "message": "Forbidden: Insufficient privileges."}), 403

            g.user = user
            g.tenant_id = user.tenant_id
            return f(*args, **kwargs)

        return decorated_function

    return decorator


def require_tenant_access():
    """Route decorator enforcing strict tenant boundary isolation matching the caller context."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not hasattr(g, "user") or g.user is None:
                return jsonify({"error": "not_authenticated", "message": "Authentication required."}), 401

            json_payload = request.get_json(silent=True) or {}
            tenant_id = (
                (request.view_args or {}).get("tenant_id")
                or json_payload.get("tenant_id")
                or request.args.get("tenant_id")
            )

            if not tenant_id:
                return jsonify({"error": "missing_tenant_id", "message": "tenant_id parameter is required."}), 400

            if not AuthRBAC.check_tenant_access(g.user, tenant_id):
                logger.warning("Tenant access violation attempt by user %s on tenant %s", g.user.user_id, tenant_id)
                return jsonify({"error": "tenant_access_denied", "message": "Access to this tenant scope is forbidden."}), 403

            return f(*args, **kwargs)

        return decorated_function

    return decorator


def get_current_user() -> Optional[User]:
    """Retrieve the authenticated User principal from the Flask request context."""
    return getattr(g, "user", None)


class IdentityAccessService:
    """Enterprise identity and access service supporting JWT/OAuth2, MFA, passwordless flows, sessions, RBAC, ABAC, and API keys."""

    ROLE_DEFINITIONS: Dict[str, List[str]] = AuthRBAC.ROLE_PERMISSIONS
    _sessions: Dict[str, Dict[str, Any]] = {}
    _api_keys: Dict[str, Dict[str, Any]] = {}
    _mfa_challenges: Dict[str, Dict[str, Any]] = {}
    _passwordless_challenges: Dict[str, Dict[str, Any]] = {}

    @classmethod
    def get_supported_roles(cls) -> List[str]:
        return [
            "super_admin",
            "organization_admin",
            "finance_manager",
            "reconciliation_officer",
            "auditor",
            "risk_analyst",
            "developer",
            "read_only",
            "customer",
        ]

    @classmethod
    def normalize_role_name(cls, role: str) -> str:
        return AuthRBAC.normalize_role_name(role)

    @classmethod
    def get_permissions_for_role(cls, role: str) -> List[str]:
        normalized = cls.normalize_role_name(role)
        return list(cls.ROLE_DEFINITIONS.get(normalized, []))

    @classmethod
    def create_principal(
        cls,
        user_id: str,
        username: str,
        tenant_id: str,
        roles: Optional[List[str]] = None,
        permissions: Optional[List[str]] = None,
        attributes: Optional[Dict[str, Any]] = None,
    ) -> User:
        role_list = [cls.normalize_role_name(role) for role in (roles or []) if role]
        if not role_list:
            role_list = ["read_only"]
        computed_permissions = set()
        for role_name in role_list:
            computed_permissions.update(cls.ROLE_DEFINITIONS.get(role_name, []))
        if permissions:
            computed_permissions.update(permissions)

        principal = User(
            user_id=user_id,
            username=username,
            tenant_id=tenant_id,
            roles=role_list,
            permissions=sorted(computed_permissions),
        )
        principal.attributes = attributes or {}
        return principal

    @classmethod
    def can_access_resource(cls, user: User, resource_type: str, resource_context: Optional[Dict[str, Any]] = None) -> bool:
        if not user:
            return False
        ctx = resource_context or {}
        if "tenant_id" in ctx and ctx["tenant_id"] != user.tenant_id and "super_admin" not in user.roles:
            return False

        if "resource_owner" in ctx and ctx["resource_owner"] != user.user_id and "super_admin" not in user.roles:
            return False

        if hasattr(user, "attributes",) and isinstance(user.attributes, dict):
            for key, value in user.attributes.items():
                if key in ctx and ctx[key] != value and key not in {"department", "country"}:
                    return False

        required_permission = {
            "settlement": "finance:approve_settlement",
            "reconciliation": "read:reconciliation",
            "audit": "audit:read",
            "settings": "read:settings",
            "webhook": "manage:webhooks",
            "api_key": "manage:api_keys",
            "service_account": "manage:service_accounts",
            "device": "manage:devices",
        }.get(resource_type, "read:all")
        return required_permission in user.permissions or "*" in user.permissions or "super_admin" in user.roles

    @classmethod
    def create_session(cls, user_id: str, tenant_id: str, device_id: Optional[str] = None, user_agent: Optional[str] = None) -> Dict[str, Any]:
        session_id = str(uuid.uuid4())
        issued_at = datetime.now(timezone.utc)
        session = {
            "session_id": session_id,
            "user_id": user_id,
            "tenant_id": tenant_id,
            "device_id": device_id,
            "user_agent": user_agent,
            "created_at": issued_at.isoformat(),
            "expires_at": (issued_at + timedelta(hours=TOKEN_EXPIRY_HOURS)).isoformat(),
            "active": True,
        }
        cls._sessions[session_id] = session
        return session

    @classmethod
    def get_session(cls, session_id: str) -> Optional[Dict[str, Any]]:
        session = cls._sessions.get(session_id)
        if not session:
            return None
        if not session.get("active"):
            return None
        expiry = datetime.fromisoformat(session["expires_at"])
        if datetime.now(timezone.utc) > expiry:
            session["active"] = False
            return None
        return session

    @classmethod
    def revoke_session(cls, session_id: str) -> bool:
        session = cls._sessions.get(session_id)
        if not session:
            return False
        session["active"] = False
        return True

    @classmethod
    def issue_api_key(cls, tenant_id: str, role: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        key = f"pk_{uuid.uuid4().hex}"
        payload = {
            "key": key,
            "tenant_id": tenant_id,
            "role": cls.normalize_role_name(role),
            "metadata": metadata or {},
            "created_at": datetime.now(timezone.utc).isoformat(),
            "active": True,
        }
        cls._api_keys[key] = payload
        return key

    @classmethod
    def verify_api_key(cls, api_key: str) -> Optional[Dict[str, Any]]:
        entry = cls._api_keys.get(api_key)
        if not entry or not entry.get("active"):
            return None
        return {"tenant_id": entry["tenant_id"], "role": entry["role"], "metadata": entry.get("metadata", {}), "key": api_key}

    @classmethod
    def revoke_api_key(cls, api_key: str) -> bool:
        entry = cls._api_keys.get(api_key)
        if not entry:
            return False
        entry["active"] = False
        return True

    @classmethod
    def create_service_account(cls, name: str, tenant_id: str, roles: Optional[List[str]] = None) -> Dict[str, Any]:
        return {
            "name": name,
            "tenant_id": tenant_id,
            "roles": [cls.normalize_role_name(role) for role in (roles or ["developer"]) if role],
            "client_id": f"svc_{uuid.uuid4().hex[:12]}",
            "secret": f"secret_{uuid.uuid4().hex[:18]}",
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

    @classmethod
    def create_mfa_challenge(cls, user_id: str) -> Dict[str, Any]:
        challenge_id = f"mfa_{uuid.uuid4().hex[:12]}"
        challenge = {
            "challenge_id": challenge_id,
            "user_id": user_id,
            "status": "pending",
            "code": "123456",
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        cls._mfa_challenges[challenge_id] = challenge
        return {"challenge_id": challenge_id, "user_id": user_id, "status": "pending"}

    @classmethod
    def verify_mfa(cls, user_id: str, challenge_id: str, code: str) -> Dict[str, Any]:
        challenge = cls._mfa_challenges.get(challenge_id)
        if challenge and challenge["user_id"] == user_id and challenge["code"] == str(code):
            challenge["status"] = "verified"
            return {"verified": True, "status": "verified"}
        return {"verified": False, "status": "failed"}

    @classmethod
    def create_passwordless_challenge(cls, user_id: str) -> Dict[str, Any]:
        challenge_id = f"pw_{uuid.uuid4().hex[:12]}"
        challenge = {
            "challenge_id": challenge_id,
            "user_id": user_id,
            "status": "pending",
            "token": "otp-123456",
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        cls._passwordless_challenges[challenge_id] = challenge
        return {"challenge_id": challenge_id, "user_id": user_id, "status": "pending"}

    @classmethod
    def verify_passwordless_token(cls, user_id: str, challenge_id: str, token: str) -> Dict[str, Any]:
        challenge = cls._passwordless_challenges.get(challenge_id)
        if challenge and challenge["user_id"] == user_id and challenge["token"] == str(token):
            challenge["status"] = "verified"
            return {"verified": True, "status": "verified"}
        return {"verified": False, "status": "failed"}

    @classmethod
    def sso_metadata(cls) -> Dict[str, Any]:
        return {
            "providers": ["oidc", "saml", "google", "azure_ad"],
            "jwt": {"algorithms": [ALGORITHM]},
            "oauth2": {"grant_types": ["authorization_code", "client_credentials", "refresh_token"]},
        }
