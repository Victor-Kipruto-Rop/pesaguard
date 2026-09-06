"""Provider-neutral communications platform for PesaGuard."""

from .core.enums import CommunicationChannel, CommunicationPriority, NotificationStatus
from .core.exceptions import CommunicationError, PermanentCommunicationError, TransientCommunicationError
from .core.interfaces import CommunicationProvider, NotificationRequest, ProviderMessage

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
]
