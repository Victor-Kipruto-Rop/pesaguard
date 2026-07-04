"""Additional feature endpoints for PesaGuard dashboard."""

import logging
import os
from datetime import datetime, timedelta, timezone
from io import StringIO
import csv

from flask import Flask, jsonify, request, send_file
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from models import Base, Discrepancy

logger = logging.getLogger("pesaguard.features")

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://pesaguard:pesaguard@localhost:5432/pesaguard")
engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)


def create_features_app(app: Flask):
    """Register feature endpoints to the Flask app."""

    @app.route("/discrepancies/export/csv", methods=["GET"])
    def export_discrepancies_csv():
        """Export incidents as CSV."""
        status = request.args.get("status", "").strip()
        severity = request.args.get("severity", "").strip()
        resolved = request.args.get("resolved", "").strip()
        
        session = SessionLocal()
        try:
            rows = session.query(Discrepancy)
            
            if status:
                rows = rows.filter((Discrepancy.anomaly_type == status) | (Discrepancy.status == status))
            if severity:
                rows = rows.filter(Discrepancy.severity == severity)
            if resolved == "open":
                rows = rows.filter(Discrepancy.resolved.is_(False))
            elif resolved == "resolved":
                rows = rows.filter(Discrepancy.resolved.is_(True))
            
            items = rows.order_by(Discrepancy.detected_at.desc()).all()
            
            output = StringIO()
            writer = csv.DictWriter(output, fieldnames=[
                "id", "trans_id", "anomaly_type", "severity", "status", "resolved",
                "tenant_id", "assignee", "detected_at", "resolved_at", "notes"
            ])
            writer.writeheader()
            
            for item in items:
                writer.writerow({
                    "id": item.id,
                    "trans_id": item.trans_id,
                    "anomaly_type": item.anomaly_type,
                    "severity": item.severity,
                    "status": item.status,
                    "resolved": "Yes" if item.resolved else "No",
                    "tenant_id": item.tenant_id or "N/A",
                    "assignee": item.assignee or "Unassigned",
                    "detected_at": item.detected_at.isoformat() if item.detected_at else "",
                    "resolved_at": item.resolved_at.isoformat() if item.resolved_at else "",
                    "notes": item.notes or "",
                })
            
            output.seek(0)
            return send_file(
                StringIO(output.getvalue()),
                mimetype="text/csv",
                as_attachment=True,
                download_name=f"pesaguard_incidents_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            )
        finally:
            session.close()

    @app.route("/analytics/incident-trends", methods=["GET"])
    def analytics_incident_trends():
        """Returns weekly and monthly trend comparisons."""
        session = SessionLocal()
        try:
            now = datetime.now(timezone.utc)
            
            # Weekly data (last 4 weeks)
            weekly_data = []
            for week_offset in range(3, -1, -1):
                week_start = now - timedelta(days=7 * (week_offset + 1))
                week_end = now - timedelta(days=7 * week_offset)
                count = session.query(Discrepancy).filter(
                    Discrepancy.detected_at >= week_start,
                    Discrepancy.detected_at < week_end,
                ).count()
                resolved = session.query(Discrepancy).filter(
                    Discrepancy.detected_at >= week_start,
                    Discrepancy.detected_at < week_end,
                    Discrepancy.resolved.is_(True),
                ).count()
                weekly_data.append({
                    "week": f"W{4-week_offset}",
                    "incidents": count,
                    "resolved": resolved,
                    "open": count - resolved,
                })
            
            # Monthly data (last 12 months)
            monthly_data = []
            for month_offset in range(11, -1, -1):
                month_start = (now.replace(day=1) - timedelta(days=month_offset * 30)).replace(day=1)
                month_end = (month_start + timedelta(days=32)).replace(day=1)
                count = session.query(Discrepancy).filter(
                    Discrepancy.detected_at >= month_start,
                    Discrepancy.detected_at < month_end,
                ).count()
                resolved = session.query(Discrepancy).filter(
                    Discrepancy.detected_at >= month_start,
                    Discrepancy.detected_at < month_end,
                    Discrepancy.resolved.is_(True),
                ).count()
                month_name = month_start.strftime("%b")
                monthly_data.append({
                    "month": month_name,
                    "incidents": count,
                    "resolved": resolved,
                    "open": count - resolved,
                })
            
            return jsonify({
                "weekly": weekly_data,
                "monthly": monthly_data,
            }), 200
        finally:
            session.close()

    @app.route("/incidents/filters/presets", methods=["GET", "POST"])
    def filter_presets():
        """Manage saved filter presets (stored in memory for MVP)."""
        # In production, store in database or file
        if not hasattr(app, 'filter_presets'):
            app.filter_presets = {
                "critical_open": {"severity": "critical", "resolved": "open"},
                "warning_assigned": {"severity": "warning", "status": "assigned"},
                "needs_review": {"status": "needs_review", "resolved": "open"},
            }
        
        if request.method == "GET":
            return jsonify({"presets": app.filter_presets}), 200
        
        # POST: Save new preset
        payload = request.get_json(silent=True) or {}
        preset_name = payload.get("name", "custom")
        preset_filters = payload.get("filters", {})
        app.filter_presets[preset_name] = preset_filters
        return jsonify({"status": "saved", "presets": app.filter_presets}), 201

    @app.route("/incidents/auto-escalate", methods=["POST"])
    def auto_escalate_incidents():
        """Escalate old unresolved critical incidents and assign to lead."""
        escalation_minutes = int(request.args.get("escalation_minutes", "45"))
        session = SessionLocal()
        try:
            threshold = datetime.now(timezone.utc) - timedelta(minutes=escalation_minutes)
            old_critical = session.query(Discrepancy).filter(
                Discrepancy.severity == "critical",
                Discrepancy.resolved.is_(False),
                Discrepancy.detected_at < threshold,
            ).all()
            
            escalated = 0
            for incident in old_critical:
                if not incident.assignee:
                    incident.assignee = "On-Call Lead"
                    incident.timeline = incident.timeline or []
                    incident.timeline.append({
                        "ts": datetime.now(timezone.utc).isoformat(),
                        "event": "auto_escalated",
                        "message": f"Auto-escalated after {escalation_minutes} minutes (critical SLA breach)",
                    })
                    escalated += 1
            
            session.commit()
            return jsonify({
                "status": "escalated",
                "count": escalated,
                "threshold_minutes": escalation_minutes,
            }), 200
        finally:
            session.close()

    @app.route("/analytics/reconciliation-report", methods=["GET"])
    def reconciliation_report():
        """Generate reconciliation summary report."""
        days = int(request.args.get("days", "7"))
        session = SessionLocal()
        try:
            cutoff = datetime.now(timezone.utc) - timedelta(days=days)
            
            all_items = session.query(Discrepancy).filter(
                Discrepancy.detected_at >= cutoff
            ).all()
            
            total = len(all_items)
            resolved = sum(1 for item in all_items if item.resolved)
            open_count = total - resolved
            
            by_severity = {}
            by_status = {}
            
            for item in all_items:
                sev = item.severity or "unknown"
                by_severity[sev] = by_severity.get(sev, 0) + 1
                
                stat = item.status or "unknown"
                by_status[stat] = by_status.get(stat, 0) + 1
            
            # Calculate resolution time stats
            resolution_times = []
            for item in all_items:
                if item.resolved and item.detected_at and item.resolved_at:
                    time_minutes = int((item.resolved_at - item.detected_at).total_seconds() // 60)
                    resolution_times.append(time_minutes)
            
            avg_resolution_time = 0
            if resolution_times:
                avg_resolution_time = sum(resolution_times) // len(resolution_times)
            
            return jsonify({
                "report_period_days": days,
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "summary": {
                    "total_incidents": total,
                    "resolved": resolved,
                    "open": open_count,
                    "resolution_rate": round(resolved / max(total, 1), 3),
                    "average_resolution_minutes": avg_resolution_time,
                },
                "by_severity": by_severity,
                "by_status": by_status,
                "critical_count": by_severity.get("critical", 0),
                "sla_compliant_percentage": round((resolved / max(total, 1)) * 100, 1),
            }), 200
        finally:
            session.close()

    @app.route("/incidents/bulk-assign", methods=["POST"])
    def bulk_assign_incidents():
        """Bulk assign multiple incidents to an operator."""
        session = SessionLocal()
        try:
            payload = request.get_json(silent=True) or {}
            ids = payload.get("ids", [])
            assignee = payload.get("assignee", "")
            note = payload.get("note", "Bulk assigned")
            
            updated = 0
            for incident_id in ids:
                incident = session.get(Discrepancy, incident_id)
                if not incident:
                    continue
                incident.assignee = assignee
                incident.timeline = incident.timeline or []
                incident.timeline.append({
                    "ts": datetime.now(timezone.utc).isoformat(),
                    "event": "bulk_assigned",
                    "message": f"Bulk assigned to {assignee}: {note}",
                })
                updated += 1
            
            session.commit()
            return jsonify({"status": "assigned", "updated": updated}), 200
        finally:
            session.close()

    @app.route("/incidents/search", methods=["GET"])
    def search_incidents():
        """Advanced full-text search across incidents."""
        query_text = request.args.get("q", "").strip()
        severity = request.args.get("severity", "").strip()
        assignee = request.args.get("assignee", "").strip()
        page = int(request.args.get("page", "1"))
        per_page = int(request.args.get("per_page", "20"))
        
        session = SessionLocal()
        try:
            rows = session.query(Discrepancy)
            
            if query_text:
                like_term = f"%{query_text}%"
                rows = rows.filter(
                    (Discrepancy.trans_id.like(like_term)) |
                    (Discrepancy.anomaly_type.like(like_term)) |
                    (Discrepancy.details.like(like_term)) |
                    (Discrepancy.notes.like(like_term))
                )
            
            if severity:
                rows = rows.filter(Discrepancy.severity == severity)
            
            if assignee:
                rows = rows.filter(Discrepancy.assignee == assignee)
            
            total = rows.count()
            items = rows.order_by(Discrepancy.detected_at.desc()).offset((page - 1) * per_page).limit(per_page).all()
            
            return jsonify({
                "query": query_text,
                "page": page,
                "per_page": per_page,
                "total": total,
                "items": [{
                    "id": item.id,
                    "trans_id": item.trans_id,
                    "anomaly_type": item.anomaly_type,
                    "severity": item.severity,
                    "assignee": item.assignee,
                    "detected_at": item.detected_at.isoformat() if item.detected_at else None,
                } for item in items],
            }), 200
        finally:
            session.close()
