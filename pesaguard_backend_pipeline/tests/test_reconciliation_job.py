import importlib
import os
import tempfile
from types import SimpleNamespace

import pytest

from pesaguard_backend_pipeline.event_store import ProcessResult


def test_persist_atomically_returns_duplicate_without_audit(monkeypatch, tmp_path):
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path / 'recon_test.db'}")
    monkeypatch.setenv("AUDIT_DATABASE_URL", f"sqlite:///{tmp_path / 'recon_test.db'}")

    from pesaguard_backend_pipeline import reconciliation_job as job_module
    job_module = importlib.reload(job_module)

    called = {
        "mark_processed": False,
        "audit_committed": False,
    }

    def fake_mark_processed_in_session(session, event, tenant_id=None):
        called["mark_processed"] = True
        return ProcessResult.DUPLICATE

    monkeypatch.setattr(job_module.event_store, "mark_processed_in_session", fake_mark_processed_in_session)

    event = {"TransID": "TX-100"}
    evaluation = {"status": "matched", "match": True, "anomalies": []}

    result = job_module._persist_atomically(event, evaluation, "TX-100", tenant_id="tenant-x")

    assert result == ProcessResult.DUPLICATE
    assert called["mark_processed"] is True

    # Audit should not have been committed for duplicate handling.
    session = job_module.AuditSession()
    try:
        audits = session.query(job_module.ActionAuditEntry).filter_by(actor="reconciliation_job").all()
        assert len(audits) == 0
    finally:
        session.close()


def test_publish_downstream_does_not_raise_on_producer_failure(monkeypatch):
    from pesaguard_backend_pipeline import reconciliation_job as job_module
    job_module = importlib.reload(job_module)

    class FailingProducer:
        def send(self, topic, key=None, value=None):
            raise RuntimeError("kafka unavailable")

        def flush(self, timeout=None):
            return None

    producer = FailingProducer()
    evaluation = {"status": "needs_review", "match": False, "anomalies": ["missing_payment"], "trans_id": "TX-200"}

    job_module._publish_downstream(evaluation, "TX-200", producer, tenant_id="tenant-x")


def test_run_skips_duplicate_and_commits_offset(monkeypatch, tmp_path):
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "recon_test.db")
        monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path}")
        monkeypatch.setenv("AUDIT_DATABASE_URL", f"sqlite:///{db_path}")
        monkeypatch.setenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")

        import reconciliation_job as job_module
        job_module = importlib.reload(job_module)

        class DummyMessage(SimpleNamespace):
            pass

        class DummyConsumer:
            def __init__(self):
                self.committed = False
                self._polled = False
                self._messages = [
                    SimpleNamespace(value={"TransID": "TX-300", "tenant_id": "tenant-x"})
                ]

            def poll(self, timeout_ms=1000):
                if self._polled:
                    job_module._RUNNING = False
                    return {}
                self._polled = True
                return {"topic-partition": self._messages}

            def close(self):
                pass

            def commit(self, message=None):
                self.committed = True

        class DummyProducer:
            def send(self, topic, key=None, value=None):
                return SimpleNamespace(get=lambda timeout=None: None)

            def close(self, timeout=None):
                pass

        saved_consumer = None

        def build_consumer(*args, **kwargs):
            nonlocal saved_consumer
            saved_consumer = DummyConsumer()
            return saved_consumer

        monkeypatch.setattr(job_module, "KafkaConsumer", build_consumer)
        monkeypatch.setattr(job_module, "KafkaProducer", lambda *args, **kwargs: DummyProducer())
        monkeypatch.setattr(job_module, "ConnectorRegistry", type("DummyRegistry", (), {"from_env": staticmethod(lambda: type("Dummy", (), {"get_connector": lambda self, tenant_id: None})())}))
        monkeypatch.setattr(job_module, "settings_store", SimpleNamespace(get=lambda tenant_id: {}))
        monkeypatch.setattr(job_module, "check_for_anomalies", lambda event, seen: [])
        monkeypatch.setattr(job_module.event_store, "already_processed", lambda trans_id: True)

        # Ensure run exits quickly after the first poll loop
        monkeypatch.setattr(job_module, "_RUNNING", True)
        job_module.run()

        assert saved_consumer is not None
        assert saved_consumer.committed is True


def test_run_commits_offset_for_iterator_consumer(monkeypatch, tmp_path):
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path / 'recon_iter.db'}")
    monkeypatch.setenv("AUDIT_DATABASE_URL", f"sqlite:///{tmp_path / 'recon_iter.db'}")
    monkeypatch.setenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")

    from pesaguard_backend_pipeline import reconciliation_job as job_module
    job_module = importlib.reload(job_module)

    class DummyMessage(SimpleNamespace):
        pass

    class DummyConsumer:
        def __init__(self):
            self.committed = False
            self._messages = iter([
                SimpleNamespace(value={"TransID": "TX-400", "TransAmount": "100.00", "MSISDN": "254700000000", "TransTime": "20260704120000"})
            ])

        def __iter__(self):
            return self

        def __next__(self):
            message = next(self._messages)
            job_module._RUNNING = False
            return message

        def commit(self, message=None):
            self.committed = True

        def close(self):
            pass

    class DummyProducer:
        def send(self, topic, key=None, value=None):
            return SimpleNamespace(get=lambda timeout=None: None)

        def close(self, timeout=None):
            pass

    saved_consumer = None

    def build_consumer(*args, **kwargs):
        nonlocal saved_consumer
        saved_consumer = DummyConsumer()
        return saved_consumer

    monkeypatch.setattr(job_module, "KafkaConsumer", build_consumer)
    monkeypatch.setattr(job_module, "KafkaProducer", lambda *args, **kwargs: DummyProducer())
    monkeypatch.setattr(job_module, "ConnectorRegistry", type("DummyRegistry", (), {"from_env": staticmethod(lambda: type("Dummy", (), {"get_connector": lambda self, tenant_id: None})())}))
    monkeypatch.setattr(job_module, "settings_store", SimpleNamespace(get=lambda tenant_id: {}))
    monkeypatch.setattr(job_module, "check_for_anomalies", lambda event, seen: [])
    monkeypatch.setattr(job_module.event_store, "already_processed", lambda trans_id: False)
    monkeypatch.setattr(job_module, "_RUNNING", True)

    job_module.run()
    assert saved_consumer is not None
    assert saved_consumer.committed is True
    assert job_module._RUNNING is False
