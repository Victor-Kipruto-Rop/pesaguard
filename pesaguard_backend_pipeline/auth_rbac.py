"""Authentication and Role-Based Access Control (RBAC) for PesaGuard API."""

import jwt
import os
import uuid
from datetime import datetime, timedelta, timezone
from functools import wraps
from typing import Dict, Any, Optional, List
from flask import request, jsonify, g

SECRET_KEY = os.getenv("JWT_SECRET_KEY", "pesaguard-secret-key-change-in-prod")
ALGORITHM = "HS256"
TOKEN_EXPIRY_HOURS = 24
REVOCATION_FILE = os.getenv("JWT_REVOCATION_FILE", "revoked_tokens.txt")


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
        self.roles = roles  # ["admin", "operator", "viewer"]
        self.permissions = permissions


class AuthRBAC:
    """Authentication and authorization manager."""

    # Role-to-permissions mapping
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
        "viewer": [
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
        """Verify JWT token and return User object."""
        try:
            if cls.is_token_revoked(token):
                return None
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            user = User(
                user_id=payload["user_id"],
                username=payload["username"],
                tenant_id=payload["tenant_id"],
                roles=payload["roles"],
                permissions=payload["permissions"],
            )
            return user
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None

    @classmethod
    def _get_permissions_for_roles(cls, roles: List[str]) -> List[str]:
        """Get combined permissions for a list of roles."""
        permissions = set()
        for role in roles:
            if role in cls.ROLE_PERMISSIONS:
                permissions.update(cls.ROLE_PERMISSIONS[role])
        return list(permissions)

    @classmethod
    def _load_revoked_tokens(cls) -> set[str]:
        if not hasattr(cls, "_revoked_tokens"):
            cls._revoked_tokens = set()
        if os.path.exists(REVOCATION_FILE):
            with open(REVOCATION_FILE, "r", encoding="utf-8") as handle:
                cls._revoked_tokens.update({line.strip() for line in handle if line.strip()})
        return cls._revoked_tokens

    @classmethod
    def _persist_revoked_token(cls, token: str) -> None:
        with open(REVOCATION_FILE, "a", encoding="utf-8") as handle:
            handle.write(f"{token}\n")

    @classmethod
    def is_token_revoked(cls, token: str) -> bool:
        revoked_tokens = cls._load_revoked_tokens()
        return token in revoked_tokens

    @classmethod
    def revoke_token(cls, token: str) -> None:
        revoked_tokens = cls._load_revoked_tokens()
        if token not in revoked_tokens:
            revoked_tokens.add(token)
            cls._persist_revoked_token(token)

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
