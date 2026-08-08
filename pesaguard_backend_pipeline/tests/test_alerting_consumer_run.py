import importlib
from types import SimpleNamespace


def test_alerting_consumer_run_monkeypatched(monkeypatch, tmp_path):
    """Run the alerting consumer loop with monkeypatched Kafka and AlertingService.

    The test ensures the consumer reads one message, invokes the alerting service,
    and commits the message.
    """
    # Ensure the consumer uses a local sqlite DB for session creation
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path / 'alerts.db'}")
    monkeypatch.setenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")

    from pesaguard_backend_pipeline import alerting_consumer as ac_mod

    calls = {"handled": [], "committed": False}

    class DummyConsumer:
        def __init__(self):
            self._messages = iter([
                SimpleNamespace(value={
                    "id": "disc-test",
                    "tenant_id": "t1",
                    "trans_id": "TX-1",
                    "severity": "critical",
                    "status": "missing_payment",
                    "anomalies": ["missing_payment"],
                })
            ])

        def __iter__(self):
            return self

        def __next__(self):
            return next(self._messages)

        def commit(self, message=None):
            calls["committed"] = True

    class DummyAlertingService:
        def __init__(self, session_factory=None, tenant_settings=None, session=None):
            pass

        def handle_discrepancy(self, payload):
            calls["handled"].append(payload.get("trans_id"))
            return {"status": "queued", "alert_id": payload.get("id"), "deliveries": [], "delivery_mode": "realtime"}

    # Monkeypatch the KafkaConsumer, AlertingService and tenant settings provider on the module
    monkeypatch.setattr(ac_mod, "KafkaConsumer", lambda *args, **kwargs: DummyConsumer())
    monkeypatch.setattr(ac_mod, "AlertingService", DummyAlertingService)
    monkeypatch.setattr(ac_mod, "TenantSettingsStore", lambda *args, **kwargs: type("TS", (), {"get": staticmethod(lambda tid: {"alert_channels": ["slack"]})})())

    # Run the consumer; it should process one message and then naturally stop
    ac_mod.run()

    assert calls["handled"] == ["TX-1"]
    assert calls["committed"] is True
