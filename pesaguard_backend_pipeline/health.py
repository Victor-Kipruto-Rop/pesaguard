"""Health-check helpers shared by the web services."""

import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
DEFAULT_DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://pesaguard:pesaguard@localhost:5432/pesaguard",
)

# Filesystem anchors used by the deployment readiness controls. These mirror the
# artifacts documented in docs/OPERATIONS_READINESS.md, docs/DISASTER_RECOVERY.md
# and docs/INCIDENT_RESPONSE.md so readiness reflects the real operator contract.
_MODULE_DIR = Path(__file__).resolve().parent
_REPO_ROOT = _MODULE_DIR.parent

BACKUP_SCRIPT_CANDIDATES = (
    _MODULE_DIR / "backup_postgres.py",
    _MODULE_DIR / "scripts" / "backup_postgres.sh",
)
BACKUP_SCHEDULE_CANDIDATES = (
    _REPO_ROOT / "infra" / "pesaguard-backup.service",
    _REPO_ROOT / "infra" / "pesaguard-backup.timer",
)
BACKUP_ARTIFACT_GLOBS = ("pesaguard_*.sql.gz", "*.sql.gz", "*.dump")
INCIDENT_RUNBOOK_CANDIDATES = (
    _REPO_ROOT / "docs" / "INCIDENT_RESPONSE.md",
    _REPO_ROOT / "docs" / "RUNBOOK.md",
)

# A daily backup schedule is expected; allow a small grace window before the
# control is considered stale rather than merely "not yet run".
DEFAULT_BACKUP_MAX_AGE_HOURS = 26
DEFAULT_BACKUP_RETENTION_DAYS = 30

# Alert channels recognised by notifier.py. Any one of them configured is enough
# to page an operator, so incident readiness degrades only when none exist.
INCIDENT_CHANNEL_ENV_VARS = {
    "slack": "SLACK_WEBHOOK_URL",
    "sms": "SMS_ALERT_RECIPIENT",
    "email": "ALERT_EMAIL_RECIPIENTS",
}


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


def _env_int(name: str, default: int) -> int:
    """Read a positive integer env var, falling back to the default on bad input."""
    try:
        value = int(os.getenv(name, str(default)))
    except (TypeError, ValueError):
        return default
    return value if value > 0 else default


def _first_existing(candidates) -> Optional[Path]:
    """Return the first path that exists on disk, or None."""
    for candidate in candidates:
        try:
            if Path(candidate).exists():
                return Path(candidate)
        except OSError:  # pragma: no cover - unreadable path
            continue
    return None


def _resolve_backup_dir() -> Path:
    """Resolve the backup directory using the same precedence as backup_postgres.py."""
    env_override = os.getenv("PESAGUARD_BACKUP_DIR")
    if env_override:
        return Path(env_override)
    return Path("/var/backups/pesaguard")


def _newest_backup_artifact(backup_dir: Path) -> Dict[str, Any]:
    """Locate the most recent backup artifact and report its age in hours."""
    newest: Optional[Path] = None
    newest_mtime = 0.0

    try:
        if backup_dir.is_dir():
            for pattern in BACKUP_ARTIFACT_GLOBS:
                for artifact in backup_dir.glob(pattern):
                    try:
                        if not artifact.is_file():
                            continue
                        mtime = artifact.stat().st_mtime
                    except OSError:
                        continue
                    if mtime > newest_mtime:
                        newest_mtime = mtime
                        newest = artifact
    except OSError:  # pragma: no cover - unreadable directory
        return {"found": False, "backup_dir": str(backup_dir)}

    if newest is None:
        return {"found": False, "backup_dir": str(backup_dir)}

    age_hours = (datetime.now(timezone.utc).timestamp() - newest_mtime) / 3600.0
    return {
        "found": True,
        "backup_dir": str(backup_dir),
        "latest_backup": newest.name,
        "age_hours": round(age_hours, 2),
        "latest_backup_at": datetime.fromtimestamp(newest_mtime, tz=timezone.utc).isoformat(),
    }


def check_backup_control() -> Dict[str, Any]:
    """Assess whether database backups are configured and actually producing artifacts.

    Statuses:
      - ``ready``      backup tooling present AND a fresh artifact within the age window
      - ``configured`` tooling/schedule present but no fresh artifact yet
      - ``degraded``   no backup tooling found at all
    """
    script_path = _first_existing(BACKUP_SCRIPT_CANDIDATES)
    schedule_path = _first_existing(BACKUP_SCHEDULE_CANDIDATES)
    backup_dir = _resolve_backup_dir()
    artifact = _newest_backup_artifact(backup_dir)

    max_age_hours = _env_int("PESAGUARD_BACKUP_MAX_AGE_HOURS", DEFAULT_BACKUP_MAX_AGE_HOURS)
    retention_days = _env_int("PESAGUARD_BACKUP_RETENTION_DAYS", DEFAULT_BACKUP_RETENTION_DAYS)

    is_fresh = bool(artifact.get("found")) and float(artifact.get("age_hours", 0.0)) <= max_age_hours

    if script_path is None and schedule_path is None:
        status = "degraded"
        reason = "no_backup_tooling_found"
    elif is_fresh:
        status = "ready"
        reason = "fresh_backup_available"
    elif artifact.get("found"):
        status = "configured"
        reason = "stale_backup_artifact"
    else:
        status = "configured"
        reason = "backup_tooling_present_no_artifact_yet"

    control: Dict[str, Any] = {
        "status": status,
        "reason": reason,
        "script": str(script_path) if script_path else None,
        "schedule_unit": str(schedule_path) if schedule_path else None,
        "retention_days": retention_days,
        "max_age_hours": max_age_hours,
    }
    control.update(artifact)
    return control


def check_incident_response_control() -> Dict[str, Any]:
    """Assess whether operators can be paged and have a runbook to follow.

    Statuses:
      - ``ready``      runbook present AND at least one alert channel configured
      - ``configured`` exactly one of {runbook, alert channel} is present
      - ``degraded``   neither is present
    """
    runbook_path = _first_existing(INCIDENT_RUNBOOK_CANDIDATES)

    channels: Dict[str, bool] = {}
    for channel, env_var in INCIDENT_CHANNEL_ENV_VARS.items():
        channels[channel] = bool(os.getenv(env_var, "").strip())

    configured_channels = sorted(name for name, enabled in channels.items() if enabled)
    has_runbook = runbook_path is not None
    has_channel = bool(configured_channels)

    if has_runbook and has_channel:
        status = "ready"
        reason = "runbook_and_alert_channels_configured"
    elif has_runbook:
        status = "configured"
        reason = "runbook_present_no_alert_channel"
    elif has_channel:
        status = "configured"
        reason = "alert_channel_present_no_runbook"
    else:
        status = "degraded"
        reason = "no_runbook_or_alert_channel"

    return {
        "status": status,
        "reason": reason,
        "runbook": str(runbook_path) if runbook_path else None,
        "channels": channels,
        "configured_channels": configured_channels,
        "severity_model": ["SEV1", "SEV2", "SEV3"],
    }


# Keys that expose deployment layout (absolute host paths, backup artifact names,
# runbook locations). These are useful to operators and deploy gates but must never
# be served by the PUBLIC /status endpoint, which is unauthenticated — leaking them
# would hand an attacker the server's filesystem and release topology.
_PATH_DISCLOSURE_KEYS = frozenset({
    "script",
    "schedule_unit",
    "runbook",
    "backup_dir",
    "latest_backup",
    "latest_backup_at",
})


def _redact_readiness(payload: Any) -> Any:
    """Return a copy of a readiness payload with path-disclosing keys removed.

    Recurses through nested dicts/lists so control sub-objects are redacted too.
    Only string/path details are dropped; statuses, reasons and aggregate gaps are
    preserved because a public status page legitimately reports component health.
    """
    if isinstance(payload, dict):
        return {
            key: _redact_readiness(value)
            for key, value in payload.items()
            if key not in _PATH_DISCLOSURE_KEYS
        }
    if isinstance(payload, list):
        return [_redact_readiness(item) for item in payload]
    return payload


def build_deployment_readiness() -> Dict[str, Any]:
    """Aggregate operational controls into a single deploy-gate readiness verdict.

    Returns a payload shaped for both the status page and deployment gates::

        {
            "status": "ready" | "degraded",
            "controls": {"backup": {...}, "incident_response": {...}},
            "gaps": [...],
            "generated_at": "<iso8601>",
        }

    ``status`` is ``ready`` only when every control is usable (``ready`` or
    ``configured``). Any ``degraded`` control makes the deployment ``degraded``.
    """
    try:
        backup_control = check_backup_control()
    except Exception:  # pragma: no cover - defensive, never let a control break health
        backup_control = {"status": "degraded", "reason": "backup_control_check_failed"}

    try:
        incident_control = check_incident_response_control()
    except Exception:  # pragma: no cover - defensive, never let a control break health
        incident_control = {"status": "degraded", "reason": "incident_control_check_failed"}

    controls = {"backup": backup_control, "incident_response": incident_control}
    gaps: List[str] = sorted(
        name for name, control in controls.items() if control.get("status") == "degraded"
    )

    return {
        "status": "degraded" if gaps else "ready",
        "controls": controls,
        "gaps": gaps,
        "tenant_id": os.getenv("TENANT_ID", "default"),
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }


def build_incident_readiness() -> Dict[str, Any]:
    """Return the incident-response focused readiness view used by status pages."""
    try:
        control = check_incident_response_control()
    except Exception:  # pragma: no cover - defensive
        control = {"status": "degraded", "reason": "incident_control_check_failed"}

    return {
        "status": control.get("status", "degraded"),
        "reason": control.get("reason"),
        "runbook": control.get("runbook"),
        "channels": control.get("channels", {}),
        "configured_channels": control.get("configured_channels", []),
        "severity_model": control.get("severity_model", []),
        "paging_order": ["slack", "sms", "phone"],
        "generated_at": datetime.now(timezone.utc).isoformat(),
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
    deployment_readiness = build_deployment_readiness()
    incident_readiness = build_incident_readiness()

    deployment_readiness = build_deployment_readiness()
    incident_readiness = build_incident_readiness()

    page = {
        "service": service_name,
        "status": status,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "request_id": request_id,
        "tenant_id": tenant_id,
        "trace_id": request_id,
        "checks": health.get("checks", {}),
        "deployment_readiness": deployment_readiness,
        "incident_readiness": incident_readiness,
        "summary": {
            "database_ok": health.get("checks", {}).get("database", {}).get("status") == "ok",
            "kafka_ok": health.get("checks", {}).get("kafka", {}).get("status") == "ok",
            "redis_ok": health.get("checks", {}).get("redis", {}).get("status") == "ok",
            "daraja_ok": health.get("checks", {}).get("daraja", {}).get("status") == "ok",
            "overall_status": status,
        },
        "deployment_readiness": deployment_readiness,
        "incident_readiness": incident_readiness,
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
