"""Health-check helpers shared by the web services."""

import os
import time
import threading
from typing import Any, Dict, Optional

import requests
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
DEFAULT_DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://pesaguard:pesaguard@localhost:5432/pesaguard",
)

# ----------------------------------------------------------------------------
# Which optional services actually gate "ok" vs "degraded" overall status.
#
# Kafka/PyFlink streaming was explicitly deferred from the MVP scope, and
# Redis is only used as a best-effort cache elsewhere in the codebase
# (already wrapped in try/except so its absence doesn't break anything).
# Previously, both unconditionally counted toward overall status, meaning a
# pilot deployment that intentionally doesn't run either would report
# "degraded" PERMANENTLY — training whoever watches it to ignore the status,
# so a real new problem later just looks like "same as always."
#
# Default: NOT required (matches current MVP scope). If Kafka or Redis is
# genuinely deployed for your pilot, set the corresponding env var to "1" and
# they'll count toward overall status again.
# ----------------------------------------------------------------------------
KAFKA_REQUIRED_FOR_OK = os.getenv("PESAGUARD_HEALTH_REQUIRE_KAFKA", "0") == "1"
REDIS_REQUIRED_FOR_OK = os.getenv("PESAGUARD_HEALTH_REQUIRE_REDIS", "0") == "1"

DARAJA_OAUTH_URL = os.getenv(
    "DARAJA_OAUTH_URL",
    "https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials",
)
# How often to actually hit Daraja's OAuth endpoint for a real connectivity
# check. Kept infrequent so a health check polled every few seconds doesn't
# hammer Safaricom's rate limits.
DARAJA_CHECK_CACHE_SECONDS = int(os.getenv("PESAGUARD_DARAJA_HEALTH_CACHE_SECONDS", "180"))


def _database_connect_args(database_url: str, timeout: int) -> Dict[str, Any]:
    if database_url.startswith("sqlite"):
        return {"check_same_thread": False}
    if database_url.startswith("postgresql"):
        return {"connect_timeout": timeout}
    return {}


_db_engines: Dict[str, Any] = {}


def _get_or_create_engine(database_url: str, timeout: int):
    cache_key = f"{database_url}::{timeout}"
    engine = _db_engines.get(cache_key)
    if engine is None:
        engine = create_engine(
            database_url,
            pool_pre_ping=True,
            pool_size=2,
            max_overflow=0,
            connect_args=_database_connect_args(database_url, timeout),
        )
        _db_engines[cache_key] = engine
    return engine


def check_database_connection(database_url: Optional[str] = None, timeout: int = 5) -> Dict[str, Any]:
    url = database_url or DEFAULT_DATABASE_URL
    try:
        engine = _get_or_create_engine(url, timeout)
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
    """Check Kafka broker connectivity.

    FIXED: previously, if the KafkaProducer constructor started background
    sender threads and then something failed during the bootstrap/metadata
    check, producer.close() was never reached (no try/finally) — those
    threads leaked. Under an actual Kafka outage, a frequently-polled health
    check would spawn a new leaking producer on every single call, exactly
    when resource exhaustion is least affordable. Now wrapped in try/finally
    so close() is always attempted regardless of how the check exits.
    """
    try:
        from kafka import KafkaProducer
    except ImportError:
        return {
            "status": "failed",
            "kafka": {"status": "failed", "error": "kafka-python not installed"},
        }

    producer = None
    try:
        producer = KafkaProducer(
            bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
            request_timeout_ms=timeout * 1000,
            api_version_auto_timeout_ms=timeout * 1000,
        )
        if not producer.bootstrap_connected():
            return {
                "status": "failed",
                "kafka": {"status": "failed", "error": "unable to connect to Kafka brokers"},
            }
        return {"status": "ok", "kafka": {"status": "ok"}}
    except Exception as exc:
        return {
            "status": "failed",
            "kafka": {"status": "failed", "error": str(exc)},
        }
    finally:
        if producer is not None:
            try:
                producer.close(timeout=timeout)
            except Exception:
                pass  # best-effort cleanup; already reporting the real check result above


_redis_client_cache: Dict[str, Any] = {}
_redis_client_lock = threading.Lock()


def _get_or_create_redis_client(redis_url: str, timeout: int):
    """Reuse one Redis client per URL instead of constructing a new one on
    every health check call.

    FIXED: previously a new client (and its underlying connection) was
    created on every call and never explicitly closed — less severe than the
    database engine leak since redis-py clients are lighter weight, but the
    same class of problem under frequent polling.
    """
    cache_key = f"{redis_url}::{timeout}"
    with _redis_client_lock:
        client = _redis_client_cache.get(cache_key)
        if client is None:
            import redis
            client = redis.from_url(redis_url, socket_connect_timeout=timeout, socket_timeout=timeout)
            _redis_client_cache[cache_key] = client
        return client


def check_redis_connectivity(timeout: int = 5) -> Dict[str, Any]:
    try:
        import redis  # noqa: F401 — import check; real usage via cached client below
    except ImportError:
        return {
            "status": "failed",
            "redis": {"status": "failed", "error": "redis package not installed"},
        }

    try:
        client = _get_or_create_redis_client(REDIS_URL, timeout)
        client.ping()
        return {"status": "ok", "redis": {"status": "ok"}}
    except Exception as exc:
        # Connection may be broken (e.g. Redis restarted) — drop the cached
        # client so the next check attempts a fresh connection rather than
        # repeatedly retrying a known-bad one.
        _redis_client_cache.pop(f"{REDIS_URL}::{timeout}", None)
        return {
            "status": "failed",
            "redis": {"status": "failed", "error": str(exc)},
        }


_daraja_check_lock = threading.Lock()
_daraja_check_cache: Dict[str, Any] = {"result": None, "checked_at": 0.0}


def check_daraja_connectivity(timeout: int = 5) -> Dict[str, Any]:
    """Check Daraja API credentials AND real connectivity.

    FIXED: previously only checked that DARAJA_CONSUMER_KEY /
    DARAJA_CONSUMER_SECRET were present and >= 10 characters — it never
    actually verified Daraja was reachable or that the credentials worked,
    so it could report "ok" during a real Daraja outage or with revoked
    credentials.

    Now performs a real OAuth token request, but throttled: a real network
    call is made at most once every DARAJA_CHECK_CACHE_SECONDS (default 180s)
    per process, with the cached result reused in between. This means a
    health check polled every few seconds still gets a genuine connectivity
    signal without hammering Safaricom's rate limits.
    """
    consumer_key = os.getenv("DARAJA_CONSUMER_KEY", "")
    consumer_secret = os.getenv("DARAJA_CONSUMER_SECRET", "")

    if not consumer_key or not consumer_secret:
        return {
            "status": "degraded",
            "daraja": {"status": "degraded", "reason": "credentials_not_configured"},
        }

    now = time.time()
    with _daraja_check_lock:
        cached = _daraja_check_cache["result"]
        cached_at = _daraja_check_cache["checked_at"]
        if cached is not None and (now - cached_at) < DARAJA_CHECK_CACHE_SECONDS:
            return cached

        try:
            response = requests.get(
                DARAJA_OAUTH_URL,
                auth=(consumer_key, consumer_secret),
                timeout=timeout,
            )
            if response.status_code == 200 and "access_token" in response.json():
                result = {"status": "ok", "daraja": {"status": "ok"}}
            else:
                result = {
                    "status": "failed",
                    "daraja": {
                        "status": "failed",
                        "error": f"unexpected response (status {response.status_code})",
                    },
                }
        except Exception as exc:
            result = {
                "status": "failed",
                "daraja": {"status": "failed", "error": str(exc)},
            }

        _daraja_check_cache["result"] = result
        _daraja_check_cache["checked_at"] = now
        return result


def build_health_payload() -> Dict[str, Any]:
    db_result = check_database_connection()
    kafka_result = check_kafka_connectivity()
    redis_result = check_redis_connectivity()
    daraja_result = check_daraja_connectivity()

    db_ok = db_result["database"]["status"] == "ok"
    kafka_ok = kafka_result["kafka"]["status"] == "ok"
    redis_ok = redis_result["redis"]["status"] == "ok"
    daraja_ok = daraja_result["daraja"]["status"] == "ok"

    if not db_ok:
        overall_status = "failed"
    else:
        # Kafka/Redis only gate overall status if explicitly marked required
        # for this deployment (see KAFKA_REQUIRED_FOR_OK / REDIS_REQUIRED_FOR_OK
        # above) — matching that they're optional/deferred infrastructure at
        # MVP stage rather than hardcoding them as always mandatory.
        kafka_gate_ok = kafka_ok or not KAFKA_REQUIRED_FOR_OK
        redis_gate_ok = redis_ok or not REDIS_REQUIRED_FOR_OK
        if kafka_gate_ok and redis_gate_ok and daraja_ok:
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

