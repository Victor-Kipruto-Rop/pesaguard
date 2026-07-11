from dataclasses import dataclass
from typing import Set


@dataclass(frozen=True)
class RoleDefinition:
    name: str
    permissions: Set[str]


ROLES = {
    "admin": RoleDefinition("admin", {"manage:settings", "manage:connectors", "view:audit_log", "resolve:discrepancies"}),
    "viewer": RoleDefinition("viewer", {"view:discrepancies", "resolve:discrepancies"}),
}


def has_permission(role: str, permission: str) -> bool:
    return permission in ROLES.get(role, RoleDefinition(role, set())).permissions
