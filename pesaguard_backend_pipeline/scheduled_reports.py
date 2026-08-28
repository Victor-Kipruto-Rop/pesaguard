"""
Scheduled Reconciliation Reports Engine for PesaGuard.

Generates daily, weekly, or ad-hoc reconciliation performance summaries, calculating
historical discrepancy volumes, resolution rates, anomaly categories, and financial impact metrics.
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from pesaguard_backend_pipeline.models import Base, Discrepancy, Report

logger = logging.getLogger("pesaguard.scheduled_reports")

DB_URL = os.getenv("DATABASE_URL", "postgresql://pesaguard:pesaguard@localhost:5432/pesaguard")
REPORTS_DB_URL = os.getenv("REPORTS_DATABASE_URL", DB_URL)
engine = create_engine(DB_URL, pool_pre_ping=True)
reports_engine = create_engine(REPORTS_DB_URL, pool_pre_ping=True)
Session = sessionmaker(bind=engine, expire_on_commit=False)
ReportsSession = sessionmaker(bind=reports_engine, expire_on_commit=False)

# Ensure tables exist when run as standalone
Base.metadata.create_all(engine)
Base.metadata.create_all(reports_engine)


def get_all_active_tenants() -> List[str]:
    """Return the distinct tenant IDs that currently have discrepancy records."""
    with Session() as session:
        tenant_ids = (
            session.query(Discrepancy.tenant_id)
            .filter(Discrepancy.tenant_id.isnot(None))
            .distinct()
            .all()
        )
    return sorted([tenant_id[0] for tenant_id in tenant_ids if tenant_id[0]])


def generate_report_for_tenant(tenant_id: str, days: int = 1, report_type: str = "daily") -> dict:
    """Generate a reconciliation summary report for a tenant over a recent lookback window."""
    now = datetime.now(timezone.utc)
    period_end = now
    period_start = now - timedelta(days=days)

    with Session() as session:
        discrepancies = (
            session.query(Discrepancy)
            .filter(
                Discrepancy.tenant_id == tenant_id,
                Discrepancy.detected_at >= period_start,
                Discrepancy.detected_at <= period_end,
            )
            .all()
        )

        total_incidents = len(discrepancies)
        resolved_count = sum(1 for discrepancy in discrepancies if discrepancy.resolved)
        open_count = total_incidents - resolved_count
        resolution_rate = (resolved_count / total_incidents * 100.0) if total_incidents > 0 else 100.0
        anomaly_types = sorted({discrepancy.anomaly_type for discrepancy in discrepancies if discrepancy.anomaly_type})
        content: Dict[str, Any] = {
            "tenant_id": tenant_id,
            "report_type": report_type,
            "period_start": period_start.isoformat(),
            "period_end": period_end.isoformat(),
            "total_incidents": total_incidents,
            "resolved_count": resolved_count,
            "open_count": open_count,
            "resolution_rate": round(resolution_rate, 2),
            "anomaly_types": anomaly_types,
        }

    with ReportsSession() as reports_session:
        report = Report(
            id=f"r_{uuid.uuid4().hex[:12]}",
            tenant_id=tenant_id,
            report_type=report_type,
            period_start=period_start,
            period_end=period_end,
            content=content,
            status="generated",
        )
        reports_session.add(report)
        reports_session.commit()

    logger.info("Generated %s report for %s: %s", report_type, tenant_id, report.id)
    return {"status": "ok", "report_id": report.id, "tenant_id": tenant_id}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="PesaGuard Scheduled Reconciliation Report Generator")
    parser.add_argument(
        "--tenant",
        default="all",
        help="Tenant ID to generate report for (use 'all' to process all tenants)",
    )
    parser.add_argument("--days", type=int, default=1, help="Lookback window in days (default: 1)")
    parser.add_argument("--type", default="daily", choices=["daily", "weekly", "monthly"], help="Report type cadence")
    args = parser.parse_args()

    target_tenants = get_all_active_tenants() if args.tenant.lower() == "all" else [args.tenant]

    logger.info("Starting report generation for %d tenant(s)...", len(target_tenants))
    results = [
        generate_report_for_tenant(tenant_id=t, days=args.days, report_type=args.type)
        for t in target_tenants
    ]

    print(json.dumps(results, indent=2))
