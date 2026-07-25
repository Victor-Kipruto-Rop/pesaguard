"""Authentication and Role-Based Access Control (RBAC) for PesaGuard API.

Role Hierarchy (from most to least privileged):
  1. admin: Full access to all features (settings, users, escalation rules, webhooks)
  2. operator: Read/write discrepancies, view analytics, perform bulk operations
  3. customer-user: Read-only access to discrepancies and analytics (customer portal)
  4. read-only: Read-only viewer access (minimal permissions)

Token Expiry: 24 hours (configurable via TOKEN_EXPIRY_HOURS)
Auth Required: Optional (default off); enable via PESAGUARD_API_AUTH_REQUIRED=1 environment variable

Permission Format: "resource:action" (e.g., "read:discrepancies", "write:escalation_rules")
"""

import logging
import jwt
import os
import uuid
from datetime import datetime, timedelta, timezone
from functools import wraps
from typing import Dict, Any, Optional, List
from flask import request, jsonify, g

from sqlalchemy import create_engine, Column, String, DateTime, Text
from sqlalchemy.orm import declarative_base, sessionmaker

logger = logging.getLogger("pesaguard.auth_rbac")

# ----------------------------------------------------------------------------
# FIXED: SECRET_KEY previously defaulted to a hardcoded string
# ("pesaguard-secret-key-change-in-prod") if JWT_SECRET_KEY wasn't set. That
# string is public (it's in the source code, and now in chat history too) —
# anyone who knows it can forge a valid, signed token for ANY user_id,
# tenant_id, and role list, completely bypassing login. This is worse than
# no auth at all, because it looks like auth is working.
#
# Now: fails loudly at import time unless a real secret is configured, OR the
# caller has explicitly opted into an insecure dev secret (for local testing
# only — never set this in a deployment that touches real customer data).
# ----------------------------------------------------------------------------
_INSECURE_DEV_SECRET = "pesaguard-secret-key-change-in-prod"

SECRET_KEY = os.getenv("JWT_SECRET_KEY")
if not SECRET_KEY:
    if os.getenv("PESAGUARD_ALLOW_INSECURE_DEV_SECRET") == "1":
        SECRET_KEY = _INSECURE_DEV_SECRET
        logger.warning(
            "JWT_SECRET_KEY is not set — using an insecure, publicly-known dev "
            "secret because PESAGUARD_ALLOW_INSECURE_DEV_SECRET=1. This must "
            "NEVER be set in any environment handling real customer data — "
            "anyone who knows this secret can forge valid tokens for any user "
            "or tenant."
        )
    else:
        raise RuntimeError(
            "JWT_SECRET_KEY environment variable is required and was not set. "
            "Generate one with: python -c \"import secrets; print(secrets.token_hex(32))\" "
            "and set it as JWT_SECRET_KEY. For local development only, you may "
            "instead set PESAGUARD_ALLOW_INSECURE_DEV_SECRET=1 to use a known, "
            "insecure placeholder — never do this anywhere real data is handled."
        )

ALGORITHM = "HS256"
TOKEN_EXPIRY_HOURS = 24

# ----------------------------------------------------------------------------
# FIXED: revocation previously lived in a local flat file
# (revoked_tokens.txt) plus an in-memory class-level set. That breaks the
# moment PesaGuard runs more than one process/container without a shared
# filesystem — a token revoked on instance A would keep working on instance
# B, since B never sees A's file or in-memory set. This is a real gap for
# the horizontal-scaling phase already on the roadmap.
#
# Now: revocation state lives in the database (shared across all instances),
# keyed by the token's `jti` claim rather than the raw token string — jti is
# short, unique, and already present in every token issued.
# ----------------------------------------------------------------------------
_RevocationBase = declarative_base()


class RevokedToken(_RevocationBase):
    __tablename__ = "revoked_tokens"

    jti = Column(String, primary_key=True)
    revoked_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    reason = Column(Text, nullable=True)


_revocation_engine = None
_RevocationSession = None


def _ensure_revocation_store_ready() -> None:
    global _revocation_engine, _RevocationSession
    if _RevocationSession is not None:
        return
    database_url = os.getenv("DATABASE_URL", "postgresql://pesaguard:pesaguard@localhost:5432/pesaguard")
    _revocation_engine = create_engine(database_url, pool_pre_ping=True)
    _RevocationBase.metadata.create_all(_revocation_engine)
    _RevocationSession = sessionmaker(bind=_revocation_engine)


class User:
    """Represents an authenticated user with roles."""

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
        self.roles = roles  # ["admin", "operator", "customer-user", "read-only"]
        self.permissions = permissions


class AuthRBAC:
    """Authentication and authorization manager."""

    # Role-to-permissions mapping (from most to least privileged)
    ROLE_PERMISSIONS = {
        "admin": [
            "read:discrepancies",
            "write:discrepancies",
            "delete:discrepancies",
            "read:analytics",
            "write:escalation_rules",
            "manage:webhooks",
            "manage:users",
            "manage:on_call",
            "manage:settings",
            "bulk:operations",
        ],
        "operator": [
            "read:discrepancies",
            "write:discrepancies",
            "read:analytics",
            "bulk:operations",
        ],
        "customer-user": [
            "read:discrepancies",
            "read:analytics",
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
        """Generate JWT token for user."""
        permissions = cls._get_permissions_for_roles(roles)
        payload = {
            "user_id": user_id,
            "username": username,
            "tenant_id": tenant_id,
            "roles": roles,
            "permissions": permissions,
            "jti": str(uuid.uuid4()),
            "iat": datetime.now(timezone.utc),
            "exp": datetime.now(timezone.utc) + timedelta(hours=TOKEN_EXPIRY_HOURS),
        }
        token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
        return token

    @classmethod
    def verify_token(cls, token: str) -> Optional[User]:
        """Verify JWT token and return User object.

        Signature and expiry are checked by jwt.decode() itself (raises on
        failure, caught below). Revocation is checked by jti against the
        shared database store, not the raw token string.
        """
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None

        jti = payload.get("jti")
        if jti and cls.is_token_revoked(jti):
            return None

        try:
            user = User(
                user_id=payload["user_id"],
                username=payload["username"],
                tenant_id=payload["tenant_id"],
                roles=payload["roles"],
                permissions=payload["permissions"],
            )
        except KeyError:
            logger.warning("Token payload missing expected claim(s), rejecting")
            return None
        return user

    @classmethod
    def _get_permissions_for_roles(cls, roles: List[str]) -> List[str]:
        """Get combined permissions for a list of roles.

        Unknown role names are logged (not silently dropped without a trace)
        so a typo'd role produces a visible warning instead of a
        confusing, silently permission-less token.
        """
        permissions = set()
        unknown_roles = []
        for role in roles:
            if role in cls.ROLE_PERMISSIONS:
                permissions.update(cls.ROLE_PERMISSIONS[role])
            else:
                unknown_roles.append(role)
        if unknown_roles:
            logger.warning("Unrecognized role(s) requested, granting no permissions for them: %s", unknown_roles)
        return list(permissions)

    @classmethod
    def is_token_revoked(cls, jti: str) -> bool:
        """Check revocation status by jti against the shared DB store."""
        if not jti:
            return False
        _ensure_revocation_store_ready()
        session = _RevocationSession()
        try:
            return session.get(RevokedToken, jti) is not None
        finally:
            session.close()

    @classmethod
    def revoke_token(cls, token: str, reason: Optional[str] = None) -> None:
        """Revoke a token by extracting and storing its jti.

        Decodes without verifying expiry (an expired token doesn't need
        revoking, but a not-yet-expired token presented for revocation should
        still be revocable even if, say, clock skew makes verification
        awkward) but DOES verify the signature — an attacker should not be
        able to cause arbitrary jti values to be inserted by presenting a
        forged, unsigned token.
        """
        try:
            payload = jwt.decode(
                token, SECRET_KEY, algorithms=[ALGORITHM],
                options={"verify_exp": False},
            )
        except jwt.InvalidTokenError:
            logger.warning("revoke_token() called with an invalid/unverifiable token; ignoring")
            return

        jti = payload.get("jti")
        if not jti:
            logger.warning("revoke_token() called with a token missing jti; ignoring")
            return

        _ensure_revocation_store_ready()
        session = _RevocationSession()
        try:
            existing = session.get(RevokedToken, jti)
            if not existing:
                session.add(RevokedToken(jti=jti, reason=reason))
                session.commit()
        finally:
            session.close()

    @classmethod
    def check_permission(cls, user: User, required_permission: str) -> bool:
        """Check if user has required permission."""
        return required_permission in user.permissions

    @classmethod
    def check_tenant_access(cls, user: User, tenant_id: str) -> bool:
        """Check if user can access a specific tenant."""
        return user.tenant_id == tenant_id


def require_auth(required_permission: str = None):
    """Decorator to require authentication on a route."""
    # If API auth is not required for this deployment, return a decorator
    # that accepts requests without auth but still honors provided
    # Authorization headers: verify tokens and enforce required
    # permissions when present. This keeps behavior consistent in tests
    # and pilot deployments.
    if os.getenv("PESAGUARD_API_AUTH_REQUIRED", "0") != "1":
        def passthrough_decorator(f):
            @wraps(f)
            def wrapped(*args, **kwargs):
                auth_header = request.headers.get("Authorization")
                if auth_header:
                    try:
                        scheme, token = auth_header.split(" ")
                        if scheme.lower() != "bearer":
                            return jsonify({"error": "invalid_auth_scheme"}), 401
                    except ValueError:
                        return jsonify({"error": "invalid_auth_header"}), 401

                    user = AuthRBAC.verify_token(token)
                    if not user:
                        return jsonify({"error": "invalid_token"}), 401

                    # If this decorator was created with a required permission,
                    # enforce it when a token is provided.
                    if required_permission and not AuthRBAC.check_permission(user, required_permission):
                        return jsonify({"error": "insufficient_permissions"}), 403

                    g.user = user

                # No auth header: allow through as anonymous when auth isn't required
                return f(*args, **kwargs)

            return wrapped

        return passthrough_decorator

    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            auth_header = request.headers.get("Authorization")
            if not auth_header:
                return jsonify({"error": "missing_auth_header"}), 401

            try:
                scheme, token = auth_header.split(" ")
                if scheme.lower() != "bearer":
                    return jsonify({"error": "invalid_auth_scheme"}), 401
            except ValueError:
                return jsonify({"error": "invalid_auth_header"}), 401

            user = AuthRBAC.verify_token(token)
            if not user:
                return jsonify({"error": "invalid_token"}), 401

            if required_permission and not AuthRBAC.check_permission(
                user, required_permission
            ):
                return jsonify({"error": "insufficient_permissions"}), 403

            g.user = user
            return f(*args, **kwargs)

        return decorated_function

    return decorator


def require_tenant_access():
    """Decorator to verify tenant_id in request matches user's tenant."""

    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not hasattr(g, "user"):
                return jsonify({"error": "not_authenticated"}), 401

            json_payload = request.get_json(silent=True) or {}
            tenant_id = (
                (request.view_args or {}).get("tenant_id")
                or json_payload.get("tenant_id")
                or request.args.get("tenant_id")
            )
            if not tenant_id:
                return jsonify({"error": "missing_tenant_id"}), 400

            if not AuthRBAC.check_tenant_access(g.user, tenant_id):
                return jsonify({"error": "tenant_access_denied"}), 403

            return f(*args, **kwargs)

        return decorated_function

    return decorator


def get_current_user() -> Optional[User]:
    """Get current authenticated user from request context."""
    return getattr(g, "user", None)
