"""
Role-Based Access Control (RBAC) Module for PesaGuard.

Defines role permissions, permission check guards, and authorization constants
for multi-tenant administrative and financial operations.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Set

# Canonical Permission Constants
PERM_MANAGE_SETTINGS = "manage:settings"
PERM_VIEW_SETTINGS = "view:settings"
PERM_MANAGE_CONNECTORS = "manage:connectors"
PERM_VIEW_AUDIT_LOG = "view:audit_log"
PERM_RESOLVE_DISCREPANCIES = "resolve:discrepancies"
PERM_VIEW_DISCREPANCIES = "view:discrepancies"
PERM_MANAGE_WEBHOOKS = "manage:webhooks"

ALL_PERMISSIONS: Set[str] = {
    PERM_MANAGE_SETTINGS,
    PERM_VIEW_SETTINGS,
    PERM_MANAGE_CONNECTORS,
    PERM_VIEW_AUDIT_LOG,
    PERM_RESOLVE_DISCREPANCIES,
    PERM_VIEW_DISCREPANCIES,
    PERM_MANAGE_WEBHOOKS,
}


@dataclass(frozen=True)
class RoleDefinition:
    """Immutable role definition mapping a role name to its granted permissions."""
    name: str
    permissions: Set[str]


ROLES: dict[str, RoleDefinition] = {
    "admin": RoleDefinition(
        "admin",
        {
            PERM_MANAGE_SETTINGS,
            PERM_VIEW_SETTINGS,
            PERM_MANAGE_CONNECTORS,
            PERM_VIEW_AUDIT_LOG,
            PERM_RESOLVE_DISCREPANCIES,
            PERM_VIEW_DISCREPANCIES,
            PERM_MANAGE_WEBHOOKS,
        },
    ),
    "finance_officer": RoleDefinition(
        "finance_officer",
        {
            PERM_VIEW_SETTINGS,
            PERM_RESOLVE_DISCREPANCIES,
            PERM_VIEW_DISCREPANCIES,
            PERM_VIEW_AUDIT_LOG,
        },
    ),
    "viewer": RoleDefinition(
        "viewer",
        {
            PERM_VIEW_DISCREPANCIES,
            PERM_VIEW_SETTINGS,
        },
    ),
    "system": RoleDefinition(
        "system",
        ALL_PERMISSIONS,
    ),
}


def has_permission(role: str, permission: str) -> bool:
    """Check if a given role possesses a specific permission string.

    Args:
        role: Role name string (e.g. 'admin', 'viewer')
        permission: Permission key to verify

    Returns:
        True if permitted, False otherwise.
    """
    normalized_role = (role or "").strip().lower()
    role_def = ROLES.get(normalized_role)
    if not role_def:
        return False
    return permission in role_def.permissions


def enforce_permission(role: str, permission: str, tenant_id: str = "default") -> None:
    """Enforce permission check, raising a PermissionError if unauthorized.

    Args:
        role: Active user role
        permission: Required permission
        tenant_id: Target tenant for audit/error context

    Raises:
        PermissionError: If the role lacks the required permission
    """
    if not has_permission(role, permission):
        raise PermissionError(
            f"Access denied for role '{role}' on tenant '{tenant_id}': missing required permission '{permission}'."
        )
