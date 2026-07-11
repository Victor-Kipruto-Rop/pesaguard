import os
import sys
from types import SimpleNamespace

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

import reconciliation_job
from models import Base
from alerting_service import AlertingService
from metrics import build_metrics_payload


def test_alerting_service_routes_critical_to_sms_and_slack_and_dedupes():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)

    session = Session()
    service = AlertingService(session=session, tenant_settings={"alert_channels": ["slack", "sms"]})

    discrepancy = {
        "id": "disc-1",
        "tenant_id": "tenant-a",
        "trans_id": "TX-1",
        "severity": "critical",
        "status": "missing_payment",
        "anomalies": ["missing_payment"],
        "checked_at": "2026-07-04T00:00:00Z",
    }

    first = service.handle_discrepancy(discrepancy)
    second = service.handle_discrepancy(discrepancy)

    assert first["status"] == "queued"
    assert second["status"] == "deduped"
    assert {entry["channel"] for entry in first["deliveries"]} == {"slack", "sms"}
    assert len(first["deliveries"]) == 2


def test_metrics_payload_exposes_prometheus_text():
    payload = build_metrics_payload()

    assert "# HELP pesaguard_transactions_total" in payload
    assert "pesaguard_alerts_total" in payload
    assert "pesaguard_open_discrepancies" in payload


def test_reconciliation_job_routes_discrepancies_to_alerting_service(monkeypatch):
    calls = []

    class DummyProducer:
        def send(self, topic, value):
            calls.append((topic, value))

    class DummyConsumer:
        def __init__(self):
            self._messages = iter([
                SimpleNamespace(value={"TransID": "TX-100", "TransAmount": "100.00", "MSISDN": "254700000000", "TransTime": "20260704120000"})
            ])

        def __iter__(self):
            return self

        def __next__(self):
            return next(self._messages)

    monkeypatch.setattr(reconciliation_job, "KafkaConsumer", lambda *args, **kwargs: DummyConsumer())
    monkeypatch.setattr(reconciliation_job, "KafkaProducer", lambda *args, **kwargs: DummyProducer())
    monkeypatch.setattr(reconciliation_job, "ConnectorRegistry", type("DummyRegistry", (), {"from_env": staticmethod(lambda: type("Dummy", (), {"get_connector": lambda self, tenant_id: None})())}))
    monkeypatch.setattr(reconciliation_job, "check_for_anomalies", lambda event, seen: [])

    def fake_alert(evaluation):
        calls.append(("alerting", evaluation["trans_id"]))

    monkeypatch.setattr(reconciliation_job, "dispatch_discrepancy_alert", fake_alert)

    reconciliation_job.run()

    assert any(topic == "alerting" for topic, _ in calls)
