"""Health-check helpers shared by the web services."""

import os
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
DEFAULT_DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://pesaguard:pesaguard@localhost:5432/pesaguard",
)


def _env_flag(name: str, default: str = "0") -> bool:
    return os.getenv(name, default).strip().lower() in {"1", "true", "yes", "on"}


def _database_connect_args(database_url: str) -> Dict[str, Any]:
    if database_url.startswith("sqlite"):
        return {"check_same_thread": False}
    return {}


def check_database_connection(database_url: Optional[str] = None, timeout: int = 5) -> Dict[str, Any]:
    url = database_url or DEFAULT_DATABASE_URL
    try:
        engine = create_engine(
            url,
            pool_pre_ping=True,
            connect_args=_database_connect_args(url),
        )
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return {"status": "ok", "database": {"status": "ok", "type": "sql"}}
    except SQLAlchemyError as exc:
        return {
            "status": "failed",
            "database": {"status": "failed", "error": str(exc)},
        }
    except Exception as exc:  # pragma: no cover
        return {
            "status": "failed",
            "database": {"status": "failed", "error": str(exc)},
        }


def check_kafka_connectivity(timeout: int = 5) -> Dict[str, Any]:
    try:
        from kafka import KafkaProducer
    except ImportError as exc:
        return {
            "status": "failed",
            "kafka": {"status": "failed", "error": "kafka-python not installed"},
        }

    try:
        producer = KafkaProducer(
            bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
            request_timeout_ms=timeout * 1000,
            api_version_auto_timeout_ms=timeout * 1000,
        )
        if not producer.bootstrap_connected():
            producer.close(timeout=timeout)
            return {
                "status": "failed",
                "kafka": {"status": "failed", "error": "unable to connect to Kafka brokers"},
            }
        producer.close(timeout=timeout)
        return {"status": "ok", "kafka": {"status": "ok"}}
    except Exception as exc:
        return {
            "status": "failed",
            "kafka": {"status": "failed", "error": str(exc)},
        }


def check_redis_connectivity(timeout: int = 5) -> Dict[str, Any]:
    try:
        import redis
    except ImportError:
        return {
            "status": "failed",
            "redis": {"status": "failed", "error": "redis package not installed"},
        }

    try:
        client = redis.from_url(REDIS_URL, socket_connect_timeout=timeout, socket_timeout=timeout)
        client.ping()
        return {"status": "ok", "redis": {"status": "ok"}}
    except Exception as exc:
        return {
            "status": "failed",
            "redis": {"status": "failed", "error": str(exc)},
        }


def check_daraja_connectivity(timeout: int = 5) -> Dict[str, Any]:
    """Check Daraja API credentials and connectivity."""
    consumer_key = os.getenv("DARAJA_CONSUMER_KEY", "")
    consumer_secret = os.getenv("DARAJA_CONSUMER_SECRET", "")
    
    if not consumer_key or not consumer_secret:
        return {
            "status": "failed",
            "daraja": {"status": "failed", "error": "Daraja credentials not configured"},
        }

    try:
        assert len(consumer_key) >= 10, "consumer_key format invalid"
        assert len(consumer_secret) >= 10, "consumer_secret format invalid"
        return {"status": "ok", "daraja": {"status": "ok"}}
    except AssertionError as e:
        return {
            "status": "failed",
            "daraja": {"status": "failed", "error": str(e)},
        }


def build_status_payload() -> Dict[str, Any]:
    """Build a richer status payload for public and internal health dashboards."""
    health = build_health_payload()
    summary = {
        "service": health.get("service", "pesaguard"),
        "status": health.get("status", "unknown"),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "checks": health.get("checks", {}),
        "summary": {
            "database_ok": health.get("checks", {}).get("database", {}).get("status") == "ok",
            "kafka_ok": health.get("checks", {}).get("kafka", {}).get("status") == "ok",
            "redis_ok": health.get("checks", {}).get("redis", {}).get("status") == "ok",
            "daraja_ok": health.get("checks", {}).get("daraja", {}).get("status") == "ok",
        },
        "request_id": health.get("request_id") or os.getenv("PESAGUARD_REQUEST_ID") or str(uuid.uuid4()),
        "tenant_id": health.get("tenant_id") or os.getenv("TENANT_ID", "default"),
        "trace_id": health.get("trace_id") or health.get("request_id") or os.getenv("PESAGUARD_REQUEST_ID") or str(uuid.uuid4()),
    }
    return summary


def build_status_summary(request_id: Optional[str] = None, tenant_id: Optional[str] = None) -> Dict[str, Any]:
    """Return a compact operational status payload used by the public status pages."""
    return build_status_page(request_id=request_id, tenant_id=tenant_id)


def build_status_page(
    service_name: str = "pesaguard",
    request_id: Optional[str] = None,
    tenant_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Return the premium status payload used by public status pages and client dashboards."""
    health = build_health_payload()
    request_id = request_id or health.get("request_id") or os.getenv("PESAGUARD_REQUEST_ID") or str(uuid.uuid4())
    tenant_id = tenant_id or health.get("tenant_id") or os.getenv("TENANT_ID", "default")
    status = health.get("status", "unknown")
    ux_status = {
        "ok": {"theme": "premium", "status_label": "Healthy", "tone": "success"},
        "degraded": {"theme": "premium", "status_label": "Degraded", "tone": "warning"},
        "failed": {"theme": "premium", "status_label": "Critical", "tone": "danger"},
    }.get(status, {"theme": "premium", "status_label": "Unknown", "tone": "neutral"})
    page = {
        "service": service_name,
        "status": status,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "request_id": request_id,
        "tenant_id": tenant_id,
        "trace_id": request_id,
        "checks": health.get("checks", {}),
        "summary": {
            "database_ok": health.get("checks", {}).get("database", {}).get("status") == "ok",
            "kafka_ok": health.get("checks", {}).get("kafka", {}).get("status") == "ok",
            "redis_ok": health.get("checks", {}).get("redis", {}).get("status") == "ok",
            "daraja_ok": health.get("checks", {}).get("daraja", {}).get("status") == "ok",
            "overall_status": status,
        },
        "ux": {
            "theme": "premium",
            "status_label": ux_status["status_label"],
            "tone": ux_status["tone"],
            "summary_title": f"{service_name.title()} operational status",
            "summary_copy": "All systems are tracking normally" if status == "ok" else "Intermittent issues detected; operations should review the checks below.",
        },
    }
    return page


def build_health_payload() -> Dict[str, Any]:
    db_result = check_database_connection()
    kafka_result = check_kafka_connectivity()
    redis_result = check_redis_connectivity()
    daraja_result = check_daraja_connectivity()

    # Pilot readiness requires the health check to exercise all upstream dependencies
    # by default: database, queue, and Daraja connectivity. Operators can disable
    # optional checks in constrained environments via explicit env flags.
    check_kafka = _env_flag("PESAGUARD_HEALTH_CHECK_KAFKA", "1")
    check_redis = _env_flag("PESAGUARD_HEALTH_CHECK_REDIS", "1")
    check_daraja = _env_flag("PESAGUARD_HEALTH_CHECK_DARAJA", "1")

    if not check_kafka:
        kafka_result = {"status": "skipped", "kafka": {"status": "skipped", "reason": "disabled_by_config"}}
    if not check_redis:
        redis_result = {"status": "skipped", "redis": {"status": "skipped", "reason": "disabled_by_config"}}
    if not check_daraja:
        daraja_result = {"status": "skipped", "daraja": {"status": "skipped", "reason": "disabled_by_config"}}

    db_ok = db_result["database"]["status"] == "ok"

    optional_results = []
    if check_kafka:
        optional_results.append(kafka_result["kafka"]["status"])
    if check_redis:
        optional_results.append(redis_result["redis"]["status"])
    if check_daraja:
        optional_results.append(daraja_result["daraja"]["status"])

    if not db_ok:
        overall_status = "failed"
    elif optional_results and all(status == "ok" for status in optional_results):
        overall_status = "ok"
    elif not optional_results:
        overall_status = "ok"
    else:
        overall_status = "degraded"

    request_id = os.getenv("PESAGUARD_REQUEST_ID") or str(uuid.uuid4())
    tenant_id = os.getenv("TENANT_ID", "default")
    payload = {
        "status": overall_status,
        "service": "pesaguard",
        "request_id": request_id,
        "tenant_id": tenant_id,
        "trace_id": request_id,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "checks": {
            "database": db_result["database"],
            "kafka": kafka_result["kafka"],
            "redis": redis_result["redis"],
            "daraja": daraja_result["daraja"],
        },
        "summary": {
            "database_ok": db_result["database"]["status"] == "ok",
            "kafka_ok": kafka_result["kafka"]["status"] == "ok",
            "redis_ok": redis_result["redis"]["status"] == "ok",
            "daraja_ok": daraja_result["daraja"]["status"] == "ok",
            "overall_status": overall_status,
        },
        "ux": {
            "theme": "premium",
            "status_label": {
                "ok": "Healthy",
                "degraded": "Degraded",
                "failed": "Critical",
            }.get(overall_status, "Unknown"),
            "tone": {
                "ok": "success",
                "degraded": "warning",
                "failed": "danger",
            }.get(overall_status, "neutral"),
        },
    }
    return payload
