from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from .application.notification_service import NotificationService
from .core.enums import CommunicationChannel
from .core.interfaces import NotificationRequest
from .models import CommunicationCampaign, CommunicationCampaignRecipient, CommunicationTemplate
from .domain import render_template


def enqueue_due_campaign(session: Session, campaign: CommunicationCampaign, service: NotificationService) -> int:
    """Expand a due campaign into idempotent notification requests."""
    now = datetime.now(timezone.utc)
    if campaign.status not in {"queued", "scheduled"} or (campaign.scheduled_at and campaign.scheduled_at > now):
        return 0
    template = session.query(CommunicationTemplate).filter_by(id=campaign.template_id, tenant_id=campaign.tenant_id, status="approved").one()
    campaign.status = "running"
    count = 0
    for item in campaign.audience:
        recipient = str(item.get("recipient") if isinstance(item, dict) else item)
        variables = item if isinstance(item, dict) else {}
        existing = session.query(CommunicationCampaignRecipient).filter_by(campaign_id=campaign.id, recipient=recipient).one_or_none()
        if existing is not None:
            continue
        row = CommunicationCampaignRecipient(id=f"campaign_recipient_{uuid.uuid4().hex}", campaign_id=campaign.id, recipient=recipient)
        session.add(row)
        try:
            notification = service.enqueue(NotificationRequest(
                tenant_id=campaign.tenant_id, recipient=recipient, message=render_template(template, variables),
                channel=CommunicationChannel(campaign.channel), idempotency_key=f"{campaign.id}:{recipient}",
                template_id=template.id, variables={**variables, "purpose": "marketing"},
            ))
            row.notification_id = notification.id
            row.status = "queued"
        except Exception as exc:
            row.status, row.error = "failed", str(exc)
        count += 1
    campaign.status = "completed"
    campaign.completed_at = now
    session.flush()
    return count