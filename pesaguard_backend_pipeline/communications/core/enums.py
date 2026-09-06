from __future__ import annotations

from enum import StrEnum


class CommunicationChannel(StrEnum):
    SMS = "sms"
    EMAIL = "email"
    VOICE = "voice"
    USSD = "ussd"
    WHATSAPP = "whatsapp"


class CommunicationPriority(StrEnum):
    CRITICAL = "critical"
    HIGH = "high"
    NORMAL = "normal"
    LOW = "low"


class NotificationStatus(StrEnum):
    CREATED = "created"
    QUEUED = "queued"
    PROCESSING = "processing"
    ACCEPTED = "accepted"
    SUBMITTED = "submitted"
    SENT = "sent"
    DELIVERED = "delivered"
    FAILED = "failed"
    REJECTED = "rejected"
    EXPIRED = "expired"
    CANCELLED = "cancelled"
    RETRYING = "retrying"
    DEAD_LETTER = "dead_letter"
