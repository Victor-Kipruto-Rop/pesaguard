"""
Enterprise-grade structured JSON logging and async correlation context tracing for PesaGuard.

Provides a unified JSON log envelope with correlation ID tracking across web requests,
background queues, and async workers.
"""

from __future__ import annotations

import json
import logging
import os
import sys
import uuid
from contextlib import contextmanager
from contextvars import ContextVar, Token
from datetime import datetime, timezone
from typing import Any, Dict, Generator, Optional

# ContextVar for end-to-end distributed request and transaction correlation tracing
_correlation_id: ContextVar[str] = ContextVar("correlation_id", default="")

# Standard LogRecord attributes to exclude from custom extra key extraction
_RESERVED_RECORD_ATTRS = {
    "args", "asctime", "created", "exc_info", "exc_text", "filename",
    "funcName", "levelname", "levelno", "lineno", "message", "module",
    "msecs", "msg", "name", "pathname", "process", "processName",
    "relativeCreated", "stack_info", "thread", "threadName", "taskName",
}


class JsonFormatter(logging.Formatter):
    """Emit logs as single-line JSON objects with standard telemetry envelopes."""

    def format(self, record: logging.LogRecord) -> str:
        cid = _correlation_id.get() or getattr(record, "correlation_id", "")
        if not cid:
            cid = str(uuid.uuid4())[:8]

        timestamp = datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat()

        payload: Dict[str, Any] = {
            "ts": timestamp,
            "level": record.levelname,
            "logger": record.name,
            "correlation_id": cid,
            "message": record.getMessage(),
        }

        # Include exception tracebacks if present
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)

        # Extract all custom 'extra' kwargs passed into log statements
        for key, value in record.__dict__.items():
            if key not in _RESERVED_RECORD_ATTRS and not key.startswith("_"):
                try:
                    # Verify key value is JSON serializable
                    json.dumps(value)
                    payload[key] = value
                except (TypeError, ValueError):
                    payload[key] = str(value)

        return json.dumps(payload, ensure_ascii=False)


def configure_logging(log_level: Optional[str] = None) -> None:
    """
    Configure the root logger to emit structured JSON logs.
    Prevents duplicate handler instantiation during app startup or re-initialization.
    """
    level = (log_level or os.getenv("LOG_LEVEL", "INFO")).upper()

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())

    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Avoid adding duplicate handlers if already configured
    if not any(isinstance(h, logging.StreamHandler) and isinstance(h.formatter, JsonFormatter) for h in root_logger.handlers):
        root_logger.handlers = [handler]


def set_correlation_id(correlation_id: str) -> Token[str]:
    """Set the correlation ID for the current request or task context."""
    cid = correlation_id.strip() if correlation_id else str(uuid.uuid4())[:8]
    return _correlation_id.set(cid)


def get_correlation_id() -> str:
    """Retrieve the current correlation ID, generating a fresh one if unassigned."""
    cid = _correlation_id.get()
    if not cid:
        cid = str(uuid.uuid4())[:8]
        _correlation_id.set(cid)
    return cid


@contextmanager
def correlation_context(correlation_id: Optional[str] = None) -> Generator[str, None, None]:
    """
    Context manager for scoping correlation IDs to specific execution blocks or threads.
    
    Usage:
        with correlation_context(req_id):
            logger.info("Processing webhook")
    """
    cid = correlation_id or str(uuid.uuid4())[:8]
    token = set_correlation_id(cid)
    try:
        yield cid
    finally:
        _correlation_id.reset(token)


def init_observability() -> Dict[str, Any]:
    """Initialise optional Sentry and OpenTelemetry integrations when configured."""
    status: Dict[str, Any] = {"sentry": "disabled", "opentelemetry": "disabled"}

    env_name = (os.getenv("PESAGUARD_ENV", "development") or "development").lower()
    sentry_dsn = os.getenv("SENTRY_DSN")
    sentry_opt_in = os.getenv("SENTRY_ENABLE", "").strip().lower() in {"1", "true", "yes", "on"}
    sentry_explicitly_disabled = os.getenv("SENTRY_DISABLE", "").strip().lower() in {"1", "true", "yes", "on"}

    if sentry_dsn and not sentry_explicitly_disabled and (env_name not in {"development", "local"} or sentry_opt_in):
        try:
            import sentry_sdk
            sentry_sdk.init(
                dsn=sentry_dsn,
                environment=env_name,
                traces_sample_rate=float(os.getenv("SENTRY_TRACES_SAMPLE_RATE", "0.2")),
                send_default_pii=False,
            )
            status["sentry"] = "enabled"
        except Exception as exc:  # pragma: no cover - optional dependency
            status["sentry"] = f"error:{exc}"

    otel_enabled = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT") or os.getenv("OTEL_SERVICE_NAME")
    if otel_enabled:
        try:
            from opentelemetry import trace
            from opentelemetry.sdk.resources import Resource
            from opentelemetry.sdk.trace import TracerProvider
            from opentelemetry.sdk.trace.export import BatchSpanProcessor
            from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter

            resource = Resource.create({"service.name": os.getenv("OTEL_SERVICE_NAME", "pesaguard-backend")})
            provider = TracerProvider(resource=resource)
            otlp_exporter = OTLPSpanExporter(endpoint=os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT"))
            provider.add_span_processor(BatchSpanProcessor(otlp_exporter))
            trace.set_tracer_provider(provider)
            status["opentelemetry"] = "enabled"
        except Exception as exc:  # pragma: no cover - optional dependency
            status["opentelemetry"] = f"error:{exc}"

    return status
