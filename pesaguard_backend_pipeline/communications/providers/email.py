from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ..core.enums import CommunicationChannel
from ..core.interfaces import CommunicationProvider, NotificationRequest, ProviderMessage
from .factory import build_default_provider_for_channel
from .router import ProviderRouter
from .smtp import SmtpEmailProvider


@dataclass(frozen=True)
class EmailProviderConfig:
    """Simple configuration carrier for email provider selection.

    The repository already prefers dependency-injected communication adapters;
    this config object keeps the configuration explicit without twisting the
    existing application object graph.
    """

    provider: str = "smtp_email"
    from_email: str = "noreply@pesaguard.local"
    gateway_client: Any | None = None


class EmailProviderFactory:
    """Create the email provider using the same gateway contract in the repo."""

    def __init__(self, gateway_client: Any | None = None, config: EmailProviderConfig | None = None):
        self.gateway_client = gateway_client
        self.config = config or EmailProviderConfig()

    def create(self) -> CommunicationProvider:
        if self.config.provider != "smtp_email":
            raise ValueError(f"unsupported explicit email provider: {self.config.provider}")
        if self.gateway_client is None:
            raise RuntimeError("email provider requires an injected gateway client")
        return SmtpEmailProvider(self.gateway_client, from_email=self.config.from_email)


class EmailRouter(ProviderRouter):
    """Thin compatibility wrapper with provider-aware route names.

    This satisfies the requested enterprise-facing object shape while delegating
    to the existing generic router and provider abstraction already in the repo.
    """

    def __init__(self, providers: dict[str, CommunicationProvider], order: dict[CommunicationChannel, list[str]], *, failure_threshold: int = 3, cooldown_seconds: int = 60, half_open_max_calls: int = 2):
        super().__init__(providers, order, failure_threshold=failure_threshold, cooldown_seconds=cooldown_seconds, half_open_max_calls=half_open_max_calls)


class EmailProviderHealth:
    """Expose an explicit health object for email provider monitoring."""

    def __init__(self, score: float = 100.0):
        self.score = score

    def register_result(self, provider: str, failed: bool = False, latency_ms: int = 0) -> None:
        if failed:
            self.score = max(0.0, self.score - 5.0)
        else:
            self.score = min(100.0, self.score + 0.5)

    def snapshot(self) -> dict[str, Any]:
        return {
            "provider": "smtp_email",
            "health_score": self.score,
            "status": "healthy" if self.score >= 90 else "degraded",
        }
