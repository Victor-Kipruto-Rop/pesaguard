"""
Dashboard CSV Export REST API Blueprint for PesaGuard.

Provides secure, tenant-scoped streaming CSV exports for transaction discrepancies,
audit records, and reconciliation audit trails with RBAC enforcement.
"""

from __future__ import annotations

import csv
import io
import logging
from datetime import datetime, timezone
from typing import Any, Generator, Optional

from flask import Blueprint, Response, jsonify, request, g

from rbac import PERM_VIEW_DISCREPANCIES, has_permission
from pesaguard_backend_pipeline.models import Discrepancy
from pesaguard_backend_pipeline.app_2 import SessionLocal

logger = logging.getLogger("pesaguard.dashboard_export")

bp = Blueprint("dashboard_export", __name__, url_prefix="/v1")


def _sanitize_csv_cell(value: Any) -> str:
    """Sanitize cell values to prevent CSV formula injection (CSV Injection / DDE)."""
    if value is None:
        return ""
    val_str = str(value)
    # If cell starts with risky injection characters, prefix with single quote
    if val_str and val_str[0] in {"=", "+", "-", "@", "\t", "\r"}:
        return f"'{val_str}"
    return val_str


def _parse_iso_datetime(date_str: Optional[str]) -> Optional[datetime]:
    """Parse ISO date string into a timezone-aware UTC datetime object."""
    if not date_str:
        return None
    try:
        # Handle 'YYYY-MM-DD' or full ISO format
        cleaned = date_str.strip()
        if len(cleaned) == 10:
            cleaned += "T00:00:00Z"
        dt = datetime.fromisoformat(cleaned.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except ValueError:
        return None


@bp.route("/export/csv", methods=["GET"])
def export_csv():
    """Stream CSV export of discrepancy records for an authorized tenant."""
    # 1. Extract context & authorization
    user = getattr(g, "user", None)
    role = getattr(user, "role", "viewer") if user else "admin"

    if not has_permission(role, PERM_VIEW_DISCREPANCIES):
        return jsonify({"error": "forbidden", "message": "Insufficient permissions to export discrepancy records."}), 403

    tenant_id = request.args.get("tenant_id", "").strip()
    if not tenant_id:
        # Fallback to context tenant if omitted
        tenant_id = getattr(g, "tenant_id", None) or request.headers.get("X-Tenant-ID", "").strip()
    
    if not tenant_id:
        return jsonify({"error": "bad_request", "message": "tenant_id parameter is required."}), 400

    # 2. Parse date filters
    dt_from = _parse_iso_datetime(request.args.get("from"))
    dt_to = _parse_iso_datetime(request.args.get("to"))

    session = SessionLocal()
    try:
        query = session.query(Discrepancy).filter(Discrepancy.tenant_id == tenant_id)
        if dt_from:
            query = query.filter(Discrepancy.detected_at >= dt_from)
        if dt_to:
            query = query.filter(Discrepancy.detected_at <= dt_to)

        query = query.order_by(Discrepancy.detected_at.desc())

        def generate_csv_stream() -> Generator[str, None, None]:
            """Generator stream for memory-efficient CSV output."""
            stream_output = io.StringIO()
            fieldnames = ["id", "trans_id", "anomaly_type", "status", "severity", "resolved", "tenant_id", "detected_at"]
            writer = csv.DictWriter(stream_output, fieldnames=fieldnames)
            
            # Write header
            writer.writeheader()
            yield stream_output.getvalue()
            stream_output.seek(0)
            stream_output.truncate(0)

            # Stream rows in chunks / iteration
            for item in query.yield_per(500):
                writer.writerow({
                    "id": _sanitize_csv_cell(getattr(item, "id", "")),
                    "trans_id": _sanitize_csv_cell(getattr(item, "trans_id", "")),
                    "anomaly_type": _sanitize_csv_cell(getattr(item, "anomaly_type", "")),
                    "status": _sanitize_csv_cell(getattr(item, "status", "")),
                    "severity": _sanitize_csv_cell(getattr(item, "severity", "")),
                    "resolved": "true" if getattr(item, "resolved", False) else "false",
                    "tenant_id": _sanitize_csv_cell(getattr(item, "tenant_id", "")),
                    "detected_at": item.detected_at.isoformat() if getattr(item, "detected_at", None) else "",
                })
                yield stream_output.getvalue()
                stream_output.seek(0)
                stream_output.truncate(0)

        filename = f"pesaguard-discrepancies-{tenant_id}-{datetime.now(timezone.utc).strftime('%Y%m%d')}.csv"
        logger.info("Streaming CSV export for tenant_id=%s by role=%s", tenant_id, role)

        return Response(
            generate_csv_stream(),
            mimetype="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )

    except Exception as exc:
        logger.exception("CSV export failed for tenant_id=%s: %s", tenant_id, exc)
        return jsonify({"error": "export_failed", "message": "Failed to generate CSV export."}), 500
    finally:
        session.close()
