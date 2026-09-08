"""Provider adapters for the communications platform."""

from .email import (
    EmailProviderConfig,
    EmailProviderFactory,
    EmailProviderHealth,
    EmailProviderRegistry,
    EmailRouter,
    MockEmailProvider,
)

__all__ = [
    "EmailProviderConfig",
    "EmailProviderFactory",
    "EmailProviderHealth",
    "EmailProviderRegistry",
    "EmailRouter",
    "MockEmailProvider",
]
