import csv
import io
import os
import sys
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from flask import Blueprint, Response, jsonify, request

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from models import Discrepancy
from models import DeadLetter, Report, Transaction
from action_audit import ActionAuditEntry

bp = Blueprint("export_routes", __name__, url_prefix="/v1")


@bp.route("/export/csv", methods=["GET"])
def export_csv():
    tenant_id = request.args.get("tenant_id", "").strip()
    if not tenant_id:
        return jsonify({"error": "tenant_id is required"}), 400

    from app_2 import SessionLocal

    session = SessionLocal()
    try:
        rows = session.query(Discrepancy).filter(Discrepancy.tenant_id == tenant_id)
        if request.args.get("from"):
            rows = rows.filter(Discrepancy.detected_at >= request.args.get("from"))
        if request.args.get("to"):
            rows = rows.filter(Discrepancy.detected_at <= request.args.get("to"))

        items = rows.order_by(Discrepancy.detected_at.desc()).all()
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=["id", "trans_id", "anomaly_type", "status", "severity", "resolved", "tenant_id"])
        writer.writeheader()
        for item in items:
            writer.writerow({
                "id": item.id,
                "trans_id": item.trans_id,
                "anomaly_type": item.anomaly_type,
                "status": item.status,
                "severity": item.severity,
                "resolved": "true" if item.resolved else "false",
                "tenant_id": item.tenant_id,
            })
        output.seek(0)
        return Response(output.getvalue(), mimetype="text/csv", headers={"Content-Disposition": "attachment; filename=pesaguard-export.csv"})
    finally:
        session.close()


@bp.route("/customers/<tenant_id>/deadletters", methods=["GET"])
def customer_deadletters(tenant_id: str):
    """Return dead-letter entries for a tenant."""
    from app_2 import SessionLocal

    session = SessionLocal()
    try:
        rows = session.query(DeadLetter).filter(DeadLetter.tenant_id == tenant_id).order_by(DeadLetter.received_at.desc()).all()
        items = [{
            "id": r.id,
            "reason": r.reason,
            "error_detail": r.error_detail,
            "processed": r.processed,
            "received_at": r.received_at.isoformat() if r.received_at else None,
        } for r in rows]
        return jsonify({"items": items}), 200
    finally:
        session.close()


@bp.route("/customers/<tenant_id>/reports", methods=["GET"])
def customer_reports(tenant_id: str):
    """List generated reports for a tenant."""
    from app_2 import SessionLocal

    session = SessionLocal()
    try:
        rows = session.query(Report).filter(Report.tenant_id == tenant_id).order_by(Report.period_start.desc()).all()
        items = [{
            "id": r.id,
            "report_type": r.report_type,
            "period_start": r.period_start.isoformat() if r.period_start else None,
            "period_end": r.period_end.isoformat() if r.period_end else None,
            "status": r.status,
        } for r in rows]
        return jsonify({"items": items}), 200
    finally:
        session.close()


@bp.route("/customers/<tenant_id>/audit", methods=["GET"])
def customer_audit(tenant_id: str):
    """Return audit action entries for a tenant."""
    from app_2 import SessionLocal

    session = SessionLocal()
    try:
        rows = session.query(ActionAuditEntry).filter(ActionAuditEntry.tenant_id == tenant_id).order_by(ActionAuditEntry.created_at.desc()).limit(200).all()
        items = [{
            "id": a.id,
            "actor": a.actor,
            "action": a.action,
            "details": a.details,
            "created_at": a.created_at.isoformat() if a.created_at else None,
        } for a in rows]
        return jsonify({"items": items}), 200
    finally:
        session.close()


@bp.route("/customers/<tenant_id>/transactions", methods=["GET"])
def customer_transactions(tenant_id: str):
    """Return recent transactions related to the tenant. Filtering is basic for pilot."""
    from app_2 import SessionLocal

    since = request.args.get("since")
    session = SessionLocal()
    try:
        rows = session.query(Transaction).order_by(Transaction.created_at.desc())
        # For pilot, allow optional time filtering
        if since:
            try:
                from datetime import datetime
                cutoff = datetime.fromisoformat(since)
                rows = rows.filter(Transaction.created_at >= cutoff)
            except Exception:
                pass
        items = [{
            "trans_id": t.trans_id,
            "trans_amount": t.trans_amount,
            "msisdn": t.msisdn,
            "business_short_code": t.business_short_code,
            "trans_time": t.trans_time,
            "created_at": t.created_at.isoformat() if t.created_at else None,
        } for t in rows.limit(200).all()]
        return jsonify({"items": items}), 200
    finally:
        session.close()
