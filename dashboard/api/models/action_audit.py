"""
Action Audit Entry Model & Factory for PesaGuard.

Maintains immutable audit trails for administrative actions, security configuration changes,
and discrepancy updates across tenants for compliance verification and security monitoring.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from sqlalchemy import Column, DateTime, JSON, String
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class ActionAuditEntry(Base):
    """Database model for tracking tenant-scoped administrative and system actions."""

    __tablename__ = "action_audit_entries"

    id = Column(String, primary_key=True, default=lambda: f"audit_{uuid.uuid4().hex[:12]}")
    tenant_id = Column(String, nullable=False, index=True)
    actor = Column(String, nullable=False, index=True)
    action = Column(String, nullable=False, index=True)
    details = Column(JSON, default=dict, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)

    def to_dict(self) -> Dict[str, Any]:
        """Convert audit model instance to a standard dictionary payload."""
        return {
            "id": self.id,
            "tenant_id": self.tenant_id,
            "actor": self.actor,
            "action": self.action,
            "details": self.details or {},
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


def build_audit_entry(
    tenant_id: str,
    actor: str,
    action: str,
    details: Optional[Dict[str, Any]] = None,
    audit_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Factory helper to construct standardized audit entry dictionaries.

    Args:
        tenant_id: Target tenant identifier
        actor: Username, service account, or user ID performing the action
        action: Identifier of the action performed (e.g., 'settings.update', 'webhook.create')
        details: Optional contextual metadata dictionary
        audit_id: Optional explicit audit ID override

    Returns:
        Structured audit dictionary ready for DB insertion or Kafka streaming.
    """
    return {
        "id": audit_id or f"audit_{uuid.uuid4().hex[:12]}",
        "tenant_id": tenant_id,
        "actor": actor,
        "action": action,
        "details": details or {},
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
