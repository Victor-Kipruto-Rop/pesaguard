"""Authentication and Role-Based Access Control (RBAC) for PesaGuard API."""

import jwt
import os
from datetime import datetime, timedelta, timezone
from functools import wraps
from typing import Dict, Any, Optional, List
from flask import request, jsonify, g

SECRET_KEY = os.getenv("JWT_SECRET_KEY", "pesaguard-secret-key-change-in-prod")
ALGORITHM = "HS256"
TOKEN_EXPIRY_HOURS = 24


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
            "iat": datetime.now(timezone.utc),
            "exp": datetime.now(timezone.utc) + timedelta(hours=TOKEN_EXPIRY_HOURS),
        }
        token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
        return token

    @classmethod
    def verify_token(cls, token: str) -> Optional[User]:
        """Verify JWT token and return User object."""
        try:
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
    def check_permission(cls, user: User, required_permission: str) -> bool:
        """Check if user has required permission."""
        return required_permission in user.permissions

    @classmethod
    def check_tenant_access(cls, user: User, tenant_id: str) -> bool:
        """Check if user can access a specific tenant."""
        return user.tenant_id == tenant_id


def require_auth(required_permission: str = None):
    """Decorator to require authentication on a route."""

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

            tenant_id = request.view_args.get("tenant_id") or request.json.get(
                "tenant_id"
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
