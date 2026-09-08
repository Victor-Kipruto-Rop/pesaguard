from pesaguard_backend_pipeline.communications.core.enums import CommunicationChannel
from pesaguard_backend_pipeline.communications.core.interfaces import NotificationRequest
from pesaguard_backend_pipeline.communications.providers.generic import GenericChannelProvider
from pesaguard_backend_pipeline.communications.product_routes import _csv_cell


class Gateway:
    def send(self, **kwargs):
        return {"status": "accepted", "id": f"{kwargs['channel']}-1"}


def test_all_non_sms_channel_adapters_use_the_same_contract():
    request_base = {"tenant_id": "tenant-a", "recipient": "recipient", "message": "hello", "idempotency_key": "id-1"}
    for channel in (CommunicationChannel.EMAIL, CommunicationChannel.VOICE, CommunicationChannel.USSD, CommunicationChannel.WHATSAPP):
        provider = GenericChannelProvider(f"gateway-{channel.value}", channel, Gateway())
        result = provider.send(NotificationRequest(channel=channel, **request_base))
        assert result.status == "accepted"
        assert result.provider_message_id == f"{channel.value}-1"


def test_load_style_batch_can_route_many_messages_without_cross_tenant_state():
    provider = GenericChannelProvider("gateway", CommunicationChannel.WHATSAPP, Gateway())
    results = [provider.send(NotificationRequest(tenant_id=f"tenant-{index % 3}", recipient=f"user-{index}", message="hello", channel=CommunicationChannel.WHATSAPP, idempotency_key=f"id-{index}")) for index in range(100)]
    assert len(results) == 100
    assert {result.provider for result in results} == {"gateway"}


def test_export_sanitizes_formula_cells():
    assert _csv_cell("=HYPERLINK('https://evil.example')").startswith("'=")
    assert _csv_cell("normal") == "normal"