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
        "read-only": [
            "read:discrepancies",
            "read:analytics",
        ],
    }

    @classmethod
    def generate_token(
        cls,
        user_id: str,
        username: str,
        tenant_id: str,
        roles: List[str],
    ) -> str:
        """Generate a signed JWT token containing claims, unique JTI, and permissions."""
        permissions = cls._get_permissions_for_roles(roles)
        now = datetime.now(timezone.utc)
        payload = {
            "user_id": user_id,
            "username": username,
            "tenant_id": tenant_id,
            "roles": roles,
            "permissions": permissions,
            "jti": str(uuid.uuid4()),
            "iat": now,
            "exp": now + timedelta(hours=TOKEN_EXPIRY_HOURS),
        }
        return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

    @classmethod
    def verify_token(cls, token: str) -> Optional[User]:
        """Verify JWT signature, expiry, and revocation state to return a User principal."""
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
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
    def _get_permissions_for_roles(cls, roles: List[str]) -> List[str]:
        """Compute the unique set of permission strings for a given list of roles."""
        permissions = set()
        unknown_roles = []
        for role in roles:
            if role in cls.ROLE_PERMISSIONS:
                permissions.update(cls.ROLE_PERMISSIONS[role])
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

            if not auth_header:
                if not auth_required:
                    return f(*args, **kwargs)
                return jsonify({"error": "missing_auth_header", "message": "Authorization header is required."}), 401

            try:
                scheme, token = auth_header.split(" ", 1)
                if scheme.lower() != "bearer":
                    return jsonify({"error": "invalid_auth_scheme", "message": "Authorization scheme must be Bearer."}), 401
            except ValueError:
                return jsonify({"error": "invalid_auth_header", "message": "Malformed Authorization header format."}), 401

            user = AuthRBAC.verify_token(token)
            if not user:
                return jsonify({"error": "invalid_token", "message": "Token is invalid, expired, or revoked."}), 401

            if required_permission and not AuthRBAC.check_permission(user, required_permission):
                logger.warning("User %s denied access. Required permission: %s", user.user_id, required_permission)
                return jsonify({"error": "insufficient_permissions", "message": "Forbidden: Insufficient privileges."}), 403

            g.user = user
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
