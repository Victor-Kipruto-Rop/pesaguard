"""Centralized Sentry and observability bootstrap for PesaGuard.

This module keeps integration optional, privacy-safe, and development-friendly.
It is intentionally lightweight so that Flask routes and background workers can
share a single Sentry initialization contract without making observability a
critical processing dependency.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any, Dict, Iterable, Optional

logger = logging.getLogger("pesaguard.observability")


def _load_dotenv_file(env_path: str | os.PathLike[str] = ".env") -> None:
    """Populate Sentry-related environment variables from a deployment .env file.

    This function is intentionally optional and side-effect free when the file is
    absent. It only fills missing variables and never overrides a runtime
    environment value already present in the process.
    """
    path = Path(env_path)
    if not path.exists():
        return

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"\'')
        if not key or key.startswith("#"):
            continue

        # Only seed the values that Sentry and deployment need, and only when
        # the process does not already have a more specific runtime value.
        if key in {
            "SENTRY_DSN",
            "SENTRY_ENVIRONMENT",
            "SENTRY_RELEASE",
            "SENTRY_TRACES_SAMPLE_RATE",
            "SENTRY_PROFILES_SAMPLE_RATE",
            "SENTRY_SEND_DEFAULT_PII",
        } and not os.getenv(key):
            os.environ[key] = value


_load_dotenv_file()

try:
    import sentry_sdk
    from sentry_sdk.integrations.flask import FlaskIntegration
    from sentry_sdk.integrations.logging import LoggingIntegration
except ImportError:  # pragma: no cover - dependency optional in local dev
    sentry_sdk = None
    FlaskIntegration = None
    LoggingIntegration = None


_ENVIRONMENT_LOOKUP = {
    "development": "development",
    "dev": "development",
    "staging": "staging",
    "stage": "staging",
    "production": "production",
    "prod": "production",
}


def _normalized_environment() -> str:
    """Return a safe environment label supported by Sentry and project operations."""
    raw = (
        os.getenv("SENTRY_ENVIRONMENT")
        or os.getenv("FLASK_ENV")
        or os.getenv("PESAGUARD_ENV")
        or "development"
    ).lower()
    return _ENVIRONMENT_LOOKUP.get(raw, "development")


def _release_name() -> str:
    """Prefer a CI release or git SHA; otherwise return project-local development label."""
    return os.getenv("SENTRY_RELEASE") or os.getenv("GIT_SHA") or "pesaguard@local"


def _sample_rate(name: str, default: str) -> float:
    """Parse a float preference safely and clamp it to the [0, 1] range."""
    raw = os.getenv(name, default)
    try:
        value = float(raw)
    except (TypeError, ValueError):
        value = float(default)
    return max(0.0, min(1.0, value))


def init_sentry(service: str = "webhook", provider: str = "mpesa") -> bool:
    """Initialize Sentry as an optional, privacy-safe dependency.

    Returns True when Sentry is configured and initialized successfully,
    False when no SENTRY_DSN is supplied or the runtime dependency is absent.
    """
    dsn = os.getenv("SENTRY_DSN")
    if not dsn or not sentry_sdk or not FlaskIntegration or not LoggingIntegration:
        logger.info("Sentry initialization skipped because SENTRY_DSN is not configured or sentry-sdk is unavailable.")
        return False

    try:
        sentry_sdk.init(
            dsn=dsn,
            environment=_normalized_environment(),
            release=_release_name(),
            integrations=[
                FlaskIntegration(),
                LoggingIntegration(level=logging.INFO, event_level=logging.ERROR),
            ],
            traces_sample_rate=_sample_rate("SENTRY_TRACES_SAMPLE_RATE", "0.1"),
            profiles_sample_rate=_sample_rate("SENTRY_PROFILES_SAMPLE_RATE", "0.0"),
            send_default_pii=False,
        )
        sentry_sdk.set_tag("service", service)
        sentry_sdk.set_tag("provider", provider)
        sentry_sdk.set_tag("environment", _normalized_environment())
        sentry_sdk.set_tag("component", "backend")
        logger.info("Sentry initialized for PesaGuard with environment=%s service=%s provider=%s", _normalized_environment(), service, provider)
        return True
    except Exception as exc:
        logger.warning("Sentry initialization failed gracefully: %s", exc)
        return False


def add_sentry_context(operation: str, **context: Any) -> None:
    """Attach safe, non-PII transaction or workflow context to the current Sentry scope."""
    if sentry_sdk is None:
        return
    try:
        tag_key = "operation"
        sentry_sdk.set_tag(tag_key, operation)
        if context:
            safe_context = {
                key: value for key, value in context.items()
                if isinstance(value, (str, int, float, bool, type(None)))
            }
            sentry_sdk.set_context("pesaguard_context", safe_context)
    except Exception:
        logger.debug("Sentry context enrichment skipped safely.", exc_info=True)


def capture_exception(exc: Exception, *, operation: str = "unhandled", extra: Optional[Dict[str, Any]] = None) -> None:
    """Capture a Python exception without exposing financial or secret payloads."""
    if sentry_sdk is None:
        return
    try:
        sentry_sdk.set_tag("operation", operation)
        if extra:
            sentry_sdk.set_context("pesaguard_safe_context", {k: str(v) for k, v in extra.items()})
        sentry_sdk.capture_exception(exc)
    except Exception:
        logger.debug("Sentry exception capture skipped safely.", exc_info=True)


def capture_message(message: str, *, level: str = "info", **tags: Any) -> None:
    """Capture a structured message with only non-sensitive tags."""
    if sentry_sdk is None:
        return
    try:
        for key, value in tags.items():
            if isinstance(key, str) and isinstance(value, str):
                sentry_sdk.set_tag(key, value)
        sentry_sdk.capture_message(message, level=level)
    except Exception:
        logger.debug("Sentry message capture skipped safely.", exc_info=True)
