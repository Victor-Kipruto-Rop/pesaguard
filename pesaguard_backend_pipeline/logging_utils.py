"""Structured JSON logging helpers for operational visibility."""

import json
import logging
import os
import uuid
from datetime import datetime, timezone
from typing import Any, Dict
from contextvars import ContextVar

# Context variable for correlation IDs (allows async tracing)
_correlation_id: ContextVar[str] = ContextVar("correlation_id", default="")


class JsonFormatter(logging.Formatter):
    """Emit logs as JSON objects with a consistent envelope, including correlation ID."""

    def format(self, record: logging.LogRecord) -> str:
        # Try to get correlation_id from context variable, record, or generate new one
        correlation_id = _correlation_id.get() or getattr(record, "correlation_id", str(uuid.uuid4())[:8])
        
        payload: Dict[str, Any] = {
            "ts": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "correlation_id": correlation_id,
            "message": record.getMessage(),
        }
        
        # Add optional structured fields from LogRecord
        if hasattr(record, "tenant_id"):
            payload["tenant_id"] = record.tenant_id
        if hasattr(record, "trans_id"):
            payload["trans_id"] = record.trans_id
        if hasattr(record, "source_ip"):
            payload["source_ip"] = record.source_ip
        if hasattr(record, "error"):
            payload["error"] = record.error
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload)


def configure_logging() -> None:
    """Configure the root logger to emit structured JSON logs with correlation IDs."""
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())

    root_logger = logging.getLogger()
    root_logger.handlers = [handler]
    root_logger.setLevel(os.getenv("LOG_LEVEL", "INFO").upper())


def set_correlation_id(correlation_id: str) -> None:
    """Set the correlation ID for the current request context."""
    _correlation_id.set(correlation_id)


def get_correlation_id() -> str:
    """Get the current correlation ID or generate a new one."""
    cid = _correlation_id.get()
    if not cid:
        cid = str(uuid.uuid4())[:8]
        _correlation_id.set(cid)
    return cid
