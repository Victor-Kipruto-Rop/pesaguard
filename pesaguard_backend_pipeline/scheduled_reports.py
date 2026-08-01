"""
Scheduled Reconciliation Reports Engine for PesaGuard.

Generates daily, weekly, or ad-hoc reconciliation performance summaries, calculating
discrepancy volumes, resolution rates, anomaly categories, and financial impact metrics.
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import create_engine, distinct, func
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


def generate_report_for_tenant(tenant_id: str, days: int = 1, report_type: str = "daily") -> dict:
    session = Session()
    reports_session = ReportsSession()
    try:
        now = datetime.now(timezone.utc)
        period_end = now
        period_start = now - timedelta(days=days)

    Args:
        tenant_id: Target tenant identifier
        days: Lookback period window in days
        report_type: Report cadence type ('daily', 'weekly', 'monthly')

    Returns:
        Summary execution dict containing status and report_id
    """
    now = datetime.now(timezone.utc)
    period_end = now
    period_start = now - timedelta(days=days)

    with Session() as session:
        try:
            # Query discrepancies detected within the window
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
            resolved_count = sum(1 for d in discrepancies if d.resolved)
            open_count = total_incidents - resolved_count
            resolution_rate = (resolved_count / total_incidents * 100.0) if total_incidents > 0 else 100.0

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
    except Exception:
        logger.exception("Failed to generate report for tenant %s", tenant_id)
        return {"status": "error", "tenant_id": tenant_id}
    finally:
        session.close()
        reports_session.close()


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
