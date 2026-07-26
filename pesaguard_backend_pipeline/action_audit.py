from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, Optional
import uuid

from sqlalchemy import Column, String, DateTime, JSON

from pesaguard_backend_pipeline.models import Base


class ActionAuditEntry(Base):
    __tablename__ = "action_audit_entries"

    id = Column(String, primary_key=True)
    tenant_id = Column(String, nullable=False, index=True)  # Indexed for multi-tenant query performance
    actor = Column(String, nullable=False)
    action = Column(String, nullable=False)
    details = Column(JSON, default=dict, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)


@dataclass
class ActionAuditRecord:
    tenant_id: str
    actor: str
    action: str
    details: Optional[Dict[str, Any]] = None
    id: Optional[str] = field(default=None)


def build_audit_entry(record: ActionAuditRecord) -> Dict[str, Any]:
    """
    Transforms an ActionAuditRecord into a dictionary ready for persistence
    or streaming, ensuring a unique ID and normalized timestamps.
    """
    audit_id = record.id or f"audit_{int(datetime.now(timezone.utc).timestamp() * 1000)}_{uuid.uuid4().hex[:8]}"
    
    return {
        "id": audit_id,
        "tenant_id": record.tenant_id,
        "actor": record.actor,
        "action": record.action,
        "details": record.details or {},
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
