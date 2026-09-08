from __future__ import annotations

import hashlib
import hmac
import secrets
import string
import uuid
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from sqlalchemy.orm import Session

from .core.enums import CommunicationChannel
from .models import CommunicationConsent, CommunicationOtpChallenge, CommunicationPreference, CommunicationTemplate


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def create_template(session: Session, *, tenant_id: str, slug: str, channel: CommunicationChannel, body: str, variables: list[str]) -> CommunicationTemplate:
    latest = session.query(CommunicationTemplate).filter_by(tenant_id=tenant_id, slug=slug).order_by(CommunicationTemplate.version.desc()).first()
    template = CommunicationTemplate(
        id=f"template_{uuid.uuid4().hex}", tenant_id=tenant_id, slug=slug,
        version=(latest.version + 1 if latest else 1), channel=channel.value,
        body=body, variables=variables, status="draft",
    )
    session.add(template)
    session.flush()
    return template


def approve_template(session: Session, template: CommunicationTemplate, approver: str) -> CommunicationTemplate:
    template.status = "approved"
    template.approved_by = approver
    template.approved_at = utc_now()
    session.flush()
    return template


def render_template(template: CommunicationTemplate, values: dict[str, object]) -> str:
    missing = [name for name in (template.variables or []) if name not in values]
    if missing:
        raise ValueError(f"missing template variables: {', '.join(missing)}")
    return template.body.format_map(values)


def set_consent(session: Session, *, tenant_id: str, recipient: str, channel: CommunicationChannel, purpose: str, granted: bool, source: str = "api") -> CommunicationConsent:
    consent = session.query(CommunicationConsent).filter_by(tenant_id=tenant_id, recipient=recipient, channel=channel.value).one_or_none()
    if consent is None:
        consent = CommunicationConsent(id=f"consent_{uuid.uuid4().hex}", tenant_id=tenant_id, recipient=recipient, channel=channel.value, purpose=purpose)
        session.add(consent)
    consent.purpose, consent.granted, consent.source, consent.updated_at = purpose, int(granted), source, utc_now()
    session.flush()
    return consent


def is_allowed_now(preference: CommunicationPreference | None, *, now: datetime | None = None) -> bool:
    if preference is None or not preference.quiet_hours_start or not preference.quiet_hours_end:
        return True
    current = (now or utc_now()).astimezone(ZoneInfo(preference.timezone)).strftime("%H:%M")
    start, end = preference.quiet_hours_start, preference.quiet_hours_end
    return not (start <= current < end if start < end else current >= start or current < end)


def issue_otp(session: Session, *, tenant_id: str, recipient: str, purpose: str, ttl_seconds: int = 300) -> tuple[CommunicationOtpChallenge, str]:
    code = "".join(secrets.choice(string.digits) for _ in range(6))
    challenge = CommunicationOtpChallenge(
        id=f"otp_{uuid.uuid4().hex}", tenant_id=tenant_id, recipient=recipient, purpose=purpose,
        code_hash=hashlib.sha256(code.encode()).hexdigest(), expires_at=utc_now() + timedelta(seconds=ttl_seconds),
    )
    session.add(challenge)
    session.flush()
    return challenge, code


def verify_otp(session: Session, challenge: CommunicationOtpChallenge, code: str) -> bool:
    if challenge.consumed_at or challenge.expires_at <= utc_now() or challenge.attempts >= challenge.max_attempts:
        return False
    challenge.attempts += 1
    valid = hmac.compare_digest(challenge.code_hash, hashlib.sha256(code.encode()).hexdigest())
    if valid:
        challenge.consumed_at = utc_now()
    session.flush()
    return valid