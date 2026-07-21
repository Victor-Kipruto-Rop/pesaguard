"""Health-check helpers shared by the web services."""

import os
from typing import Any, Dict, Optional

from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
DEFAULT_DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://pesaguard:pesaguard@localhost:5432/pesaguard",
)


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
    
    # If credentials not configured, consider it degraded but not failed
    if not consumer_key or not consumer_secret:
        return {
            "status": "degraded",
            "daraja": {"status": "degraded", "reason": "credentials_not_configured"},
        }
    
    # Quick credential format check (not a real API call to avoid rate limits)
    try:
        assert len(consumer_key) >= 10, "consumer_key format invalid"
        assert len(consumer_secret) >= 10, "consumer_secret format invalid"
        return {"status": "ok", "daraja": {"status": "ok"}}
    except AssertionError as e:
        return {
            "status": "failed",
            "daraja": {"status": "failed", "error": str(e)},
        }


def build_health_payload() -> Dict[str, Any]:
    db_result = check_database_connection()
    kafka_result = check_kafka_connectivity()
    redis_result = check_redis_connectivity()
    daraja_result = check_daraja_connectivity()
    
    # Determine overall status:
    # - "ok" if all critical services (DB) are up
    # - "degraded" if DB is up but optional services (Kafka, Redis, Daraja) are not
    # - "failed" if critical services (DB) are down
    db_ok = db_result["database"]["status"] == "ok"
    kafka_ok = kafka_result["kafka"]["status"] == "ok"
    redis_ok = redis_result["redis"]["status"] == "ok"
    daraja_ok = daraja_result["daraja"]["status"] == "ok"
    
    if not db_ok:
        overall_status = "failed"
    elif kafka_ok and redis_ok and daraja_ok:
        overall_status = "ok"
    else:
        overall_status = "degraded"
    
    return {
        "status": overall_status,
        "service": "pesaguard",
        "checks": {
            "database": db_result["database"],
            "kafka": kafka_result["kafka"],
            "redis": redis_result["redis"],
            "daraja": daraja_result["daraja"],
        },
    }
