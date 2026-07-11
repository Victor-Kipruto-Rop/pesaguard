import csv
import io
import os
import sys
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from flask import Blueprint, Response, jsonify, request

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from models import Discrepancy

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
