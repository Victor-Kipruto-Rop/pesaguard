import builtins
import hashlib
import hmac
import importlib
import json
import os
import sys
import tempfile
import types

import pytest

from pesaguard_backend_pipeline.auth_rbac import AuthRBAC


@pytest.fixture()
def webhook_client(monkeypatch):
    with tempfile.TemporaryDirectory() as tmpdir:
        monkeypatch.setenv("DATABASE_URL", f"sqlite:///{os.path.join(tmpdir, 'pesaguard_test.db')}")
        monkeypatch.setenv("DARAJA_ALLOWED_IPS", "127.0.0.1")
        monkeypatch.setenv("DARAJA_SHARED_SECRET", "test-secret")
        monkeypatch.setenv("PESAGUARD_WEBHOOK_MAX_BODY_BYTES", "256")
        import app as webhook_app

        webhook_app = importlib.reload(webhook_app)
        webhook_app.app.config.update(TESTING=True)
        with webhook_app.app.test_client() as client:
            yield client


@pytest.fixture()
def dashboard_client(monkeypatch):
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "dashboard_test.db")
        monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path}")
        monkeypatch.setenv("PESAGUARD_API_AUTH_REQUIRED", "1")
        from pesaguard_backend_pipeline import app_2

        app_2 = importlib.reload(app_2)
        app_2.Base.metadata.create_all(app_2.engine)
        app_2.app.config.update(TESTING=False)
        with app_2.app.test_client() as client:
            yield client, app_2


def test_webhook_rejects_oversized_payload_and_bad_source(webhook_client):
    response = webhook_client.post(
        "/webhook/mpesa/confirmation",
        data=b"{" + b"a" * 300 + b"}",
        content_type="application/json",
    )
    assert response.status_code == 413

    response = webhook_client.post(
        "/webhook/mpesa/confirmation",
        json={"TransactionType": "Pay Bill", "TransID": "abc", "TransTime": "20240101120000", "TransAmount": "10", "BusinessShortCode": "123456", "MSISDN": "254700000000"},
        headers={"X-Daraja-Shared-Secret": "wrong-secret"},
    )
    assert response.status_code == 403


def test_dashboard_api_requires_valid_bearer_token(dashboard_client):
    client, _ = dashboard_client

    unauthorized = client.get("/discrepancies")
    assert unauthorized.status_code == 401

    token = AuthRBAC.generate_token(
        user_id="ops-1",
        username="ops",
        tenant_id="tenant-a",
        roles=["operator"],
    )
    authorized = client.get("/discrepancies", headers={"Authorization": f"Bearer {token}"})
    assert authorized.status_code == 200


def test_dashboard_scopes_results_to_the_authenticated_tenant(dashboard_client):
    client, app_module = dashboard_client

    session = app_module.SessionLocal(read_only=False)
    try:
        session.add_all([
            app_module.Discrepancy(
                id="tenant-a-1",
                trans_id="tenant-a-1",
                tenant_id="tenant-a",
                anomaly_type="missing_payment",
                status="needs_review",
                severity="critical",
                details="tenant a mismatch",
                resolved=False,
            ),
            app_module.Discrepancy(
                id="tenant-b-1",
                trans_id="tenant-b-1",
                tenant_id="tenant-b",
                anomaly_type="duplicate",
                status="needs_review",
                severity="warning",
                details="tenant b mismatch",
                resolved=False,
            ),
        ])
        session.commit()
    finally:
        session.close()

    token = AuthRBAC.generate_token(
        user_id="ops-tenant-a",
        username="ops",
        tenant_id="tenant-a",
        roles=["operator"],
    )
    response = client.get("/discrepancies", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    payload = response.get_json()
    assert all(item["tenant_id"] == "tenant-a" for item in payload["items"])


def test_webhook_accepts_valid_source_and_replays_are_ignored(webhook_client):
    payload = {
        "TransactionType": "Pay Bill",
        "TransID": "abc-123",
        "TransTime": "20240101120000",
        "TransAmount": "10",
        "BusinessShortCode": "123456",
        "MSISDN": "254700000000",
    }

    first_response = webhook_client.post(
        "/webhook/mpesa/confirmation",
        json=payload,
        headers={"X-Daraja-Shared-Secret": "test-secret"},
    )
    assert first_response.status_code == 200

    duplicate_response = webhook_client.post(
        "/webhook/mpesa/confirmation",
        json=payload,
        headers={"X-Daraja-Shared-Secret": "test-secret"},
    )
    assert duplicate_response.status_code == 200
    assert "duplicate ignored" in duplicate_response.get_json()["ResultDesc"].lower()


def test_webhook_records_source_ip_and_valid_signature(monkeypatch):
    with tempfile.TemporaryDirectory() as tmpdir:
        monkeypatch.setenv("DATABASE_URL", f"sqlite:///{os.path.join(tmpdir, 'pesaguard_test.db')}")
        monkeypatch.setenv("DARAJA_ALLOWED_IPS", "127.0.0.1")
        monkeypatch.setenv("DARAJA_CONSUMER_SECRET", "test-secret")
        monkeypatch.setenv("PESAGUARD_WEBHOOK_MAX_BODY_BYTES", "256")

        import app as webhook_app
        webhook_app = importlib.reload(webhook_app)
        webhook_app.app.config.update(TESTING=True)

        payload = {
            "TransactionType": "Pay Bill",
            "TransID": "audit-123",
            "TransTime": "20240101120000",
            "TransAmount": "10",
            "BusinessShortCode": "123456",
            "MSISDN": "254700000000",
        }
        body = json.dumps(payload).encode("utf-8")
        signature = hmac.new(b"test-secret", body, hashlib.sha256).hexdigest().upper()

        with webhook_app.app.test_client() as client:
            response = client.post(
                "/webhook/mpesa/confirmation",
                data=body,
                content_type="application/json",
                headers={"X-Daraja-Signature": signature},
            )

        assert response.status_code == 200
        record = webhook_app.event_store.get_processed("audit-123")
        assert record is not None
        assert record["source_ip"] == "127.0.0.1"
        assert record["signature_verified"] is True


def test_webhook_health_returns_ok_when_services_available(webhook_client, monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "sqlite:///:memory:")
    monkeypatch.setenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
    import health as health_module
    importlib.reload(health_module)

    response = webhook_client.get("/health")
    assert response.status_code in (200, 503)
    assert "status" in response.json


def test_dashboard_health_returns_ok_when_services_available(dashboard_client, monkeypatch):
    client, _ = dashboard_client
    monkeypatch.setenv("DATABASE_URL", "sqlite:///:memory:")
    monkeypatch.setenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
    import health as health_module
    importlib.reload(health_module)

    response = client.get("/health")
    assert response.status_code in (200, 503)
    assert "checks" in response.json


def test_status_and_health_contracts_include_trace_metadata(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "sqlite:///:memory:")
    monkeypatch.setenv("PESAGUARD_HEALTH_CHECK_KAFKA", "0")
    monkeypatch.setenv("PESAGUARD_HEALTH_CHECK_REDIS", "0")
    monkeypatch.setenv("PESAGUARD_HEALTH_CHECK_DARAJA", "0")
    import health as health_module
    import app as webhook_app

    health_module = importlib.reload(health_module)
    webhook_app = importlib.reload(webhook_app)

    summary = health_module.build_status_summary()
    assert summary["service"] == "pesaguard"
    assert summary["status"] in {"ok", "degraded", "failed"}
    assert "generated_at" in summary
    assert "request_id" in summary
    assert "tenant_id" in summary
    assert "summary" in summary

    with webhook_app.app.test_client() as client:
        response = client.get("/status", headers={"X-Request-ID": "trace-123", "X-Tenant-ID": "tenant-a"})
        assert response.status_code in (200, 503)
        payload = response.get_json()
        assert payload["request_id"] == "trace-123"
        assert payload["tenant_id"] == "tenant-a"
        assert payload["service"] == "pesaguard"
        assert response.headers["X-Trace-Id"] == "trace-123"
        assert response.headers["X-Correlation-ID"] == "trace-123"


def test_observability_init_enables_sentry_and_otel_when_configured(monkeypatch):
    monkeypatch.setenv("SENTRY_DSN", "https://public@example.ingest.sentry.io/1")
    monkeypatch.setenv("SENTRY_TRACES_SAMPLE_RATE", "1.0")
    monkeypatch.setenv("PESAGUARD_ENV", "test")
    monkeypatch.setenv("OTEL_SERVICE_NAME", "pesaguard-test")
    monkeypatch.setenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4318/v1/traces")

    import pesaguard_backend_pipeline.logging_utils as logging_utils

    status = logging_utils.init_observability()
    assert status["sentry"] in {"enabled", "error:missing sentry-sdk dependency"}
    assert status["opentelemetry"] in {"enabled", "error:missing opentelemetry packages"}


def test_observability_skips_sentry_in_development_by_default(monkeypatch):
    monkeypatch.setenv("PESAGUARD_ENV", "development")
    monkeypatch.setenv("SENTRY_DSN", "https://public@example.ingest.sentry.io/1")

    import pesaguard_backend_pipeline.logging_utils as logging_utils

    status = logging_utils.init_observability()
    assert status["sentry"] == "disabled"


def test_premium_alert_routing_and_status_page_ux(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "sqlite:///:memory:")
    monkeypatch.setenv("PESAGUARD_HEALTH_CHECK_KAFKA", "0")
    monkeypatch.setenv("PESAGUARD_HEALTH_CHECK_REDIS", "0")
    monkeypatch.setenv("PESAGUARD_HEALTH_CHECK_DARAJA", "0")

    import health as health_module
    import notifier
    import app as webhook_app

    health_module = importlib.reload(health_module)
    notifier = importlib.reload(notifier)
    webhook_app = importlib.reload(webhook_app)

    route = notifier.route_alert({"trans_id": "tx-7", "tenant_id": "tenant-a", "severity": "critical"})
    assert route["severity"] == "critical"
    assert "slack" in route["channels"]
    assert "sms" in route["channels"]
    assert route["status"] == "ready"
    assert route["routing_policy"] == "critical_first"
    assert route["retry_policy"]["max_retries"] >= 2
    assert route["cooldown_seconds"] >= 300

    escalation = __import__("pesaguard_backend_pipeline.escalation_engine", fromlist=["route_escalation"]).route_escalation("tenant-a", "critical", "reconciliation")
    assert escalation["status"] == "ready"
    assert escalation["routing_policy"] == "critical_first"
    assert escalation["retry_policy"]["max_retries"] >= 2
    assert escalation["cooldown_seconds"] >= 300

    status_page = health_module.build_status_page(service_name="pesaguard-premium")
    assert status_page["service"] == "pesaguard-premium"
    assert "status" in status_page
    assert "summary" in status_page
    assert "checks" in status_page
    assert "ux" in status_page
    assert status_page["ux"]["theme"] == "premium"

    with webhook_app.app.test_client() as client:
        response = client.get("/status", headers={"X-Request-ID": "trace-999", "X-Tenant-ID": "tenant-a"})
        assert response.status_code in (200, 503)
        payload = response.get_json()
        assert payload["service"] == "pesaguard"
        assert payload["ux"]["theme"] == "premium"
        assert payload["ux"]["status_label"] in {"Healthy", "Degraded", "Critical"}


def test_legacy_api_contract_uses_standard_envelope(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "sqlite:///:memory:")
    monkeypatch.setenv("PESAGUARD_ADMIN_API_TOKEN", "legacy-token")
    import importlib
    import pesaguard_backend_pipeline.app_1 as legacy_api

    legacy_api = importlib.reload(legacy_api)

    with legacy_api.app.test_client() as client:
        response = client.get("/api/stats/summary", headers={"X-Admin-Token": "legacy-token"})
        assert response.status_code == 200
        payload = response.get_json()
        assert payload["status"] == "success"
        assert "data" in payload
        assert "request_id" in payload
        assert "tenant_id" in payload

    with legacy_api.app.test_client() as client:
        response = client.get("/api/discrepancies?limit=abc", headers={"X-Admin-Token": "legacy-token"})
        assert response.status_code == 400
        payload = response.get_json()
        assert payload["status"] == "error"
        assert payload["error"]["code"] == "invalid_query"

    with legacy_api.app.test_client() as client:
        response = client.get("/api/stats/summary")
        assert response.status_code == 403
        payload = response.get_json()
        assert payload["status"] == "error"
        assert payload["error"]["code"] == "forbidden"


def test_deployment_readiness_includes_backup_and_incident_controls(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "sqlite:///:memory:")
    monkeypatch.setenv("PESAGUARD_HEALTH_CHECK_KAFKA", "0")
    monkeypatch.setenv("PESAGUARD_HEALTH_CHECK_REDIS", "0")
    monkeypatch.setenv("PESAGUARD_HEALTH_CHECK_DARAJA", "0")

    import health as health_module
    importlib.reload(health_module)

    readiness = health_module.build_deployment_readiness()
    assert readiness["status"] in {"ready", "degraded"}
    assert "backup" in readiness["controls"]
    assert "incident_response" in readiness["controls"]
    assert readiness["controls"]["backup"]["status"] in {"ready", "configured", "degraded"}

    page = health_module.build_status_page(service_name="pesaguard-premium")
    assert "deployment_readiness" in page
    assert "incident_readiness" in page
    assert page["deployment_readiness"]["status"] in {"ready", "degraded"}


def test_check_kafka_connectivity_returns_failed_when_kafka_dependency_is_missing(monkeypatch):
    monkeypatch.setitem(sys.modules, "kafka", types.ModuleType("kafka"))
    import health as health_module
    importlib.reload(health_module)

    result = health_module.check_kafka_connectivity()
    assert result["status"] == "failed"
    assert result["kafka"]["status"] == "failed"
    assert "kafka-python not installed" in result["kafka"]["error"]


def test_check_kafka_connectivity_returns_failed_when_connection_fails(monkeypatch):
    class FakeProducer:
        def __init__(self, *args, **kwargs):
            pass

        def bootstrap_connected(self):
            return False

        def close(self, timeout=None):
            pass

    kafka_module = types.ModuleType("kafka")
    kafka_module.KafkaProducer = FakeProducer
    monkeypatch.setitem(sys.modules, "kafka", kafka_module)
    import health as health_module
    importlib.reload(health_module)

    result = health_module.check_kafka_connectivity()
    assert result["status"] == "failed"
    assert result["kafka"]["status"] == "failed"
    assert "unable to connect to Kafka brokers" in result["kafka"]["error"]


def test_check_redis_connectivity_returns_failed_when_dependency_is_missing(monkeypatch):
    original_import = builtins.__import__

    def fake_import(name, globals=None, locals=None, fromlist=(), level=0):
        if name == "redis":
            raise ImportError("redis package not installed")
        return original_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", fake_import)
    import health as health_module
    importlib.reload(health_module)

    result = health_module.check_redis_connectivity()
    assert result["status"] == "failed"
    assert result["redis"]["status"] == "failed"
    assert "redis package not installed" in result["redis"]["error"]


def test_check_redis_connectivity_returns_failed_when_ping_fails(monkeypatch):
    class FakeClient:
        def ping(self):
            raise ConnectionError("unable to reach redis")

    fake_redis = types.ModuleType("redis")
    fake_redis.from_url = staticmethod(lambda *args, **kwargs: FakeClient())
    monkeypatch.setitem(sys.modules, "redis", fake_redis)
    import health as health_module
    importlib.reload(health_module)

    result = health_module.check_redis_connectivity()
    assert result["status"] == "failed"
    assert result["redis"]["status"] == "failed"
    assert "unable to reach redis" in result["redis"]["error"].lower()


def test_enqueue_transaction_event_returns_failed_when_rq_dependency_is_missing(monkeypatch):
    original_import = builtins.__import__

    def fake_import(name, globals=None, locals=None, fromlist=(), level=0):
        if name in ("redis", "rq"):
            raise ImportError("required package not installed")
        return original_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", fake_import)
    import background_tasks as background_tasks_module
    importlib.reload(background_tasks_module)

    result = background_tasks_module.enqueue_transaction_event("mpesa.transactions.raw", {"TransID": "abc"})
    assert result["status"] == "failed"
    assert "rq or redis package not installed" in result["error"]


def test_enqueue_transaction_event_queues_job_when_redis_available(monkeypatch):
    class FakeJob:
        id = "fake-job-id"

    class FakeQueue:
        def __init__(self, *args, **kwargs):
            pass

        def enqueue(self, fn, topic, payload, job_timeout=None, **kwargs):
            assert topic == "mpesa.transactions.raw"
            assert payload["TransID"] == "abc"
            assert kwargs.get("correlation_id") == "trace-456"
            return FakeJob()

    class FakeConnection:
        def __init__(self, redis_conn):
            self.redis_conn = redis_conn

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_val, exc_tb):
            return False

    class FakeRedisClient:
        pass

    fake_redis = types.ModuleType("redis")
    fake_redis.from_url = staticmethod(lambda *args, **kwargs: FakeRedisClient())
    fake_rq = types.ModuleType("rq")
    fake_rq.Queue = FakeQueue
    fake_rq.Connection = FakeConnection

    monkeypatch.setitem(sys.modules, "redis", fake_redis)
    monkeypatch.setitem(sys.modules, "rq", fake_rq)
    import background_tasks as background_tasks_module
    importlib.reload(background_tasks_module)

    from pesaguard_backend_pipeline.logging_utils import correlation_context
    with correlation_context("trace-456"):
        result = background_tasks_module.enqueue_transaction_event("mpesa.transactions.raw", {"TransID": "abc"})

    assert result["status"] == "queued"
    assert result["job_id"] == "fake-job-id"
    assert result["queue"] == "transaction_events"


def test_check_database_connection_returns_failed_for_invalid_database_path(monkeypatch):
    with tempfile.TemporaryDirectory() as tmpdir:
        invalid_dir = os.path.join(tmpdir, "missing")
        bad_db_url = f"sqlite:////{invalid_dir}/pesaguard.db"
        monkeypatch.setenv("DATABASE_URL", bad_db_url)
        import health as health_module
        importlib.reload(health_module)

        result = health_module.check_database_connection()
        assert result["status"] == "failed"
        assert result["database"]["status"] == "failed"
        assert "unable to open database file" in result["database"]["error"] or "unable to open database file" in result["database"]["error"].lower()
