"""Provider-neutral communications platform for PesaGuard."""

from .core.enums import CommunicationChannel, CommunicationPriority, NotificationStatus
from .core.exceptions import CommunicationError, PermanentCommunicationError, TransientCommunicationError
from .core.interfaces import CommunicationProvider, NotificationRequest, ProviderMessage
from .events import (
    fraud_notification_event,
    reconciliation_notification_event,
    security_notification_event,
    transaction_notification_event,
)

__all__ = [
    "CommunicationChannel",
    "CommunicationPriority",
    "CommunicationProvider",
    "CommunicationError",
    "NotificationRequest",
    "NotificationStatus",
    "PermanentCommunicationError",
    "ProviderMessage",
    "TransientCommunicationError",
    "fraud_notification_event",
    "reconciliation_notification_event",
    "security_notification_event",
    "transaction_notification_event",
]
