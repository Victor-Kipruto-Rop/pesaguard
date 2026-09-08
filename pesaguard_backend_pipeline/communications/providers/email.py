from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ..core.enums import CommunicationChannel
from ..core.interfaces import CommunicationProvider, NotificationRequest, ProviderMessage
from .factory import build_default_provider_for_channel
from .router import ProviderRouter
from .smtp import SmtpEmailProvider


class EmailProviderRegistry:
    """Explicit registry that names the enterprise email providers in the repo.

    It keeps the provider map stable, discoverable, and extension-friendly so
    deployments can swap from SMTP to a mock provider or a future SES/SendGrid
    gateway without changing the caller contract.
    """

    def __init__(self):
        self._providers: dict[str, type[CommunicationProvider]] = {
            "smtp_email": SmtpEmailProvider,
            "mock_email": MockEmailProvider,
        }

    def register(self, name: str, provider_cls: type[CommunicationProvider]) -> None:
        self._providers[name.lower()] = provider_cls

    def get(self, name: str) -> type[CommunicationProvider]:
        return self._providers[name.lower()]

    def names(self) -> list[str]:
        return sorted(self._providers)


class MockEmailProvider(SmtpEmailProvider):
    """Deterministic mock SMTP-style provider for local and test delivery.

    It adopts the same send contract and status envelope as the repository's
    provider model, which enables deterministic tests without inventing a
    separate disconnected application.
    """

    name = "mock_email"

    def __init__(self, client: Any | None = None, *, from_email: str = "noreply@pesaguard.local"):
        self.client = client or _MockEmailGateway()
        self.from_email = from_email

    def _send(self, request: NotificationRequest) -> ProviderMessage:
        recipient = self.validate_recipient(request.channel, request.recipient)
        subject = str((request.variables or {}).get("subject") or "PesaGuard notification")
        message = {
            "to": recipient,
            "from_email": self.from_email,
            "subject": subject,
            "body": request.message,
            "idempotency_key": request.idempotency_key,
        }
        response = self.client.send_message(message)
        if not isinstance(response, dict) or not response.get("message_id"):
            raise RuntimeError("mock email gateway rejected message")
        return ProviderMessage(
            provider=self.name,
            provider_message_id=str(response.get("message_id")),
            status="accepted",
            raw_response=response,
        )


class _MockEmailGateway:
    def send_message(self, message: dict[str, Any]) -> dict[str, Any]:
        return {"message_id": "mock-sent-1", "status": "accepted", "to": message.get("to")}


@dataclass(frozen=True)
class EmailProviderConfig:
    """Configuration carrier for email provider selection.

    It remains compatible with the existing repo's dependency-injected
    communication provider pattern while naming the requested provider object
    directly in a way that is discoverable for operators and tests.
    """

    provider: str = "smtp_email"
    from_email: str = "noreply@pesaguard.local"
    gateway_client: Any | None = None


class EmailProviderFactory:
    """Create the email provider using the repository's transport contract."""

    def __init__(self, gateway_client: Any | None = None, config: EmailProviderConfig | None = None, registry: EmailProviderRegistry | None = None):
        self.gateway_client = gateway_client
        self.config = config or EmailProviderConfig()
        self.registry = registry or EmailProviderRegistry()

    def create(self) -> CommunicationProvider:
        provider_name = self.config.provider.lower()
        if provider_name not in self.registry.names():
            raise ValueError(f"unsupported explicit email provider: {self.config.provider}")
        provider_cls = self.registry.get(provider_name)
        if provider_name == "smtp_email":
            if self.gateway_client is None:
                raise RuntimeError("email provider requires an injected gateway client")
            return provider_cls(self.gateway_client, from_email=self.config.from_email)
        if provider_name == "mock_email":
            return provider_cls(self.gateway_client, from_email=self.config.from_email)
        raise ValueError(f"unsupported explicit email provider: {self.config.provider}")


class EmailRouter(ProviderRouter):
    """Compatibility router that routes through a configured provider map."""

    def __init__(self, providers: dict[str, CommunicationProvider], order: dict[CommunicationChannel, list[str]], *, failure_threshold: int = 3, cooldown_seconds: int = 60, half_open_max_calls: int = 2):
        super().__init__(providers, order, failure_threshold=failure_threshold, cooldown_seconds=cooldown_seconds, half_open_max_calls=half_open_max_calls)


class EmailProviderHealth:
    """Health object for provider health snapshots without making claims."""

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
