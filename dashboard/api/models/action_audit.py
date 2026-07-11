from datetime import datetime, timezone
from typing import Any, Dict, Optional

from sqlalchemy import Column, DateTime, JSON, String
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class ActionAuditEntry(Base):
    __tablename__ = "action_audit_entries"

    id = Column(String, primary_key=True)
    tenant_id = Column(String, nullable=False)
    actor = Column(String, nullable=False)
    action = Column(String, nullable=False)
    details = Column(JSON, default=dict)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


def build_audit_entry(tenant_id: str, actor: str, action: str, details: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    return {
        "tenant_id": tenant_id,
        "actor": actor,
        "action": action,
        "details": details or {},
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
