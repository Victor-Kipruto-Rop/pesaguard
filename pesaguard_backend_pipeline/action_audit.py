from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import Column, String, Text, DateTime, JSON

from pesaguard_backend_pipeline.models import Base


class ActionAuditEntry(Base):
    __tablename__ = "action_audit_entries"

    id = Column(String, primary_key=True)
    tenant_id = Column(String, nullable=False)
    actor = Column(String, nullable=False)
    action = Column(String, nullable=False)
    details = Column(JSON, default=dict)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


@dataclass
class ActionAuditRecord:
    tenant_id: str
    actor: str
    action: str
    details: Optional[Dict[str, Any]] = None


def build_audit_entry(record: ActionAuditRecord) -> Dict[str, Any]:
    return {
        "tenant_id": record.tenant_id,
        "actor": record.actor,
        "action": record.action,
        "details": record.details or {},
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
