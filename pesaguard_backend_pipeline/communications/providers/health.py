"""Provider health scoring from persisted delivery outcomes.

The score aggregates real delivery data (success rate, latency, timeout rate,
delivery rate, webhook health) over a configurable window so dashboards and
the failover policy operate on actual evidence rather than assumptions.
"""
from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from enum import StrEnum
from typing import Any

from sqlalchemy import func
from sqlalchemy.orm import Session

from ..models import CommunicationAttempt, CommunicationIncident, CommunicationNotification, CommunicationWebhookEvent


class HealthLevel(StrEnum):
    HEALTHY = "HEALTHY"
    DEGRADED = "DEGRADED"
    CRITICAL = "CRITICAL"
    OUTAGE = "OUTAGE"


DEFAULT_WINDOW_HOURS = 24


def _window_hours() -> int:
    try:
        return max(1, int(os.getenv("PESAGUARD_COMMUNICATION_HEALTH_WINDOW_HOURS", str(DEFAULT_WINDOW_HOURS))))
    except ValueError:
        return DEFAULT_WINDOW_HOURS


def _level(score: float, success_rate: float) -> HealthLevel:
    if success_rate <= 0.5:
        return HealthLevel.OUTAGE
    if score >= 90:
        return HealthLevel.HEALTHY
    if score >= 70:
        return HealthLevel.DEGRADED
    return HealthLevel.CRITICAL


def provider_health_snapshot(session: Session, provider: str, *, window_hours: int | None = None) -> dict[str, Any]:
    """Compute a 0-100 health score for one provider from real outcomes."""
    hours = window_hours or _window_hours()
    since = datetime.now(timezone.utc) - timedelta(hours=hours)

    attempts = session.query(
        CommunicationAttempt.status,
        func.count(CommunicationAttempt.id),
        func.avg(CommunicationAttempt.latency_ms),
    ).filter(
        CommunicationAttempt.provider == provider,
        CommunicationAttempt.started_at >= since,
    ).group_by(CommunicationAttempt.status).all()

    total = sum(count for _, count, _ in attempts) or 0
    by_status: dict[str, int] = {}
    latencies: list[float] = []
    for status, count, avg_latency in attempts:
        by_status[status] = count
        if avg_latency is not None:
            latencies.append(float(avg_latency))
    success_total = sum(count for status, count in by_status.items() if status in {"accepted", "submitted", "sent", "delivered"})
    failures = sum(count for status, count in by_status.items() if status in {"failed", "dead_letter", "retrying"})
    timeouts = by_status.get("retrying", 0)
    success_rate = round(success_total / total, 4) if total else 1.0
    failure_rate = round(failures / total, 4) if total else 0.0
    timeout_rate = round(timeouts / total, 4) if total else 0.0
    average_latency_ms = round(sum(latencies) / len(latencies), 1) if latencies else 0.0