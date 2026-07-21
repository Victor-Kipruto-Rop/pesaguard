"""
Generate scheduled reconciliation reports (daily/weekly).
Intended to be run from cron or as a one-off service.
"""
from datetime import datetime, timedelta, timezone
import os
import uuid
import json
import logging

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from models import Base, Discrepancy, Report

logger = logging.getLogger("pesaguard.scheduled_reports")

DB_URL = os.getenv("DATABASE_URL", "postgresql://pesaguard:pesaguard@localhost:5432/pesaguard")
engine = create_engine(DB_URL, pool_pre_ping=True)
Session = sessionmaker(bind=engine, expire_on_commit=False)

# Ensure tables exist when run as standalone
Base.metadata.create_all(engine)


def generate_report_for_tenant(tenant_id: str, days: int = 1, report_type: str = "daily") -> dict:
    session = Session()
    try:
        now = datetime.now(timezone.utc)
        period_end = now
        period_start = now - timedelta(days=days)

        items = session.query(Discrepancy).filter(
            Discrepancy.tenant_id == tenant_id,
            Discrepancy.detected_at >= period_start,
            Discrepancy.detected_at <= period_end,
        ).all()

        total = len(items)
        resolved = sum(1 for i in items if i.resolved)
        open_count = total - resolved

        by_severity = {}
        for item in items:
            sev = item.severity or "unknown"
            by_severity[sev] = by_severity.get(sev, 0) + 1

        content = {
            "generated_at": now.isoformat(),
            "tenant_id": tenant_id,
            "period_start": period_start.isoformat(),
            "period_end": period_end.isoformat(),
            "summary": {
                "total_incidents": total,
                "resolved": resolved,
                "open": open_count,
            },
            "by_severity": by_severity,
        }

        report = Report(
            id=f"r_{uuid.uuid4().hex[:12]}",
            tenant_id=tenant_id,
            report_type=report_type,
            period_start=period_start,
            period_end=period_end,
            content=content,
            status="generated",
        )
        session.add(report)
        session.commit()
        logger.info("Generated %s report for %s: %s", report_type, tenant_id, report.id)
        return {"status": "ok", "report_id": report.id, "tenant_id": tenant_id}
    except Exception:
        logger.exception("Failed to generate report for tenant %s", tenant_id)
        return {"status": "error", "tenant_id": tenant_id}
    finally:
        session.close()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Generate scheduled reconciliation reports")
    parser.add_argument("--tenant", required=True, help="Tenant ID to generate report for (use 'all' to generate for all tenants)")
    parser.add_argument("--days", type=int, default=1, help="Lookback period in days")
    parser.add_argument("--type", default="daily", help="Report type: daily or weekly")

    args = parser.parse_args()

    session = Session()
    try:
        if args.tenant == "all":
            tenants = session.query(Discrepancy.tenant_id).distinct().all()
            tenant_ids = [t[0] for t in tenants if t[0]]
        else:
            tenant_ids = [args.tenant]
    finally:
        session.close()

    results = []
    for t in tenant_ids:
        results.append(generate_report_for_tenant(t, days=args.days, report_type=args.type))

    print(json.dumps(results, indent=2))
