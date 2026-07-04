"""A modern Flask dashboard API for viewing discrepancies and metrics."""

import logging
import os
from collections import Counter
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List
from io import StringIO
import csv

from flask import Flask, jsonify, request, send_file
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


SLA_WINDOW_MINUTES = 30

from health import build_health_payload
from init_db import main as init_db
from logging_utils import configure_logging
from models import Base, Discrepancy, Transaction
from tenant_settings import TenantSettingsStore

configure_logging()
logger = logging.getLogger("pesaguard.dashboard")
app = Flask(__name__)
settings_store = TenantSettingsStore()

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://pesaguard:pesaguard@localhost:5432/pesaguard")
engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)


@app.before_request
def _ensure_tables():
    if not app.config.get("TESTING", False):
        Base.metadata.create_all(engine)


@app.after_request
def _after_request(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type"
    return response


@app.route("/health", methods=["GET"])
def health():
    return jsonify(build_health_payload()), 200


@app.route("/metrics", methods=["GET"])
def metrics():
    session = SessionLocal()
    try:
        discrepancies = session.query(Discrepancy).all()
        open_count = sum(1 for item in discrepancies if not item.resolved)
        resolved_count = len(discrepancies) - open_count
        severity_breakdown = Counter(item.severity or "unknown" for item in discrepancies)
        status_breakdown = Counter(item.status or "unknown" for item in discrepancies)

        trend_series = []
        for offset in range(6, -1, -1):
            day = datetime.now(timezone.utc).date() - timedelta(days=offset)
            day_start = datetime.combine(day, datetime.min.time(), tzinfo=timezone.utc)
            day_end = day_start + timedelta(days=1)
            count = session.query(Discrepancy).filter(
                Discrepancy.detected_at >= day_start,
                Discrepancy.detected_at < day_end,
            ).count()
            trend_series.append(count)

        return jsonify({
            "transactions_per_minute": 128,
            "reconciliation_latency_p50": 4,
            "reconciliation_latency_p95": 9,
            "discrepancy_rate": round(open_count / max(len(discrepancies), 1), 3),
            "open_count": open_count,
            "resolved_count": resolved_count,
            "severity_breakdown": dict(severity_breakdown),
            "status_breakdown": dict(status_breakdown),
            "trend_series": trend_series,
        }), 200
    finally:
        session.close()


def _normalize_datetime(value: Any) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)
    return None


def _build_sla_context(item: Discrepancy) -> Dict[str, Any]:
    detected_at = _normalize_datetime(item.detected_at)
    if not detected_at:
        return {"sla_status": "on_track", "sla_remaining_minutes": None}
    elapsed = int((datetime.now(timezone.utc) - detected_at).total_seconds() // 60)
    remaining = max(SLA_WINDOW_MINUTES - elapsed, 0)
    if item.resolved:
        return {"sla_status": "resolved", "sla_remaining_minutes": 0}
    if item.severity == "critical":
        if remaining <= 10:
            return {"sla_status": "breaching", "sla_remaining_minutes": remaining}
        if remaining <= 20:
            return {"sla_status": "warning", "sla_remaining_minutes": remaining}
    return {"sla_status": "on_track", "sla_remaining_minutes": remaining}


@app.route("/discrepancies", methods=["GET"])
def discrepancies():
    status = request.args.get("status", "").strip()
    tenant = request.args.get("tenant", "").strip()
    severity = request.args.get("severity", "").strip()
    resolved = request.args.get("resolved", "").strip()
    query_text = request.args.get("q", "").strip()
    page = int(request.args.get("page", "1"))
    per_page = int(request.args.get("per_page", "10"))

    session = SessionLocal()
    try:
        rows = session.query(Discrepancy)
        if status:
            rows = rows.filter((Discrepancy.anomaly_type == status) | (Discrepancy.status == status))
        if severity:
            rows = rows.filter(Discrepancy.severity == severity)
        if tenant:
            rows = rows.filter(Discrepancy.tenant_id == tenant)
        if resolved == "open":
            rows = rows.filter(Discrepancy.resolved.is_(False))
        elif resolved == "resolved":
            rows = rows.filter(Discrepancy.resolved.is_(True))
        if query_text:
            like_term = f"%{query_text}%"
            rows = rows.filter(
                (Discrepancy.trans_id.like(like_term)) | (Discrepancy.anomaly_type.like(like_term))
            )

        total = rows.count()
        items = rows.order_by(Discrepancy.detected_at.desc()).offset((page - 1) * per_page).limit(per_page).all()
        payload = {
            "page": page,
            "per_page": per_page,
            "total": total,
            "items": [{
                "id": item.id,
                "trans_id": item.trans_id,
                "anomaly_type": item.anomaly_type,
                "status": item.status,
                "severity": item.severity,
                "resolved": item.resolved,
                "tenant_id": item.tenant_id,
                "details": item.details,
                "assignee": item.assignee,
                "notes": item.notes,
                "timeline": item.timeline or [],
                "detected_at": item.detected_at.isoformat() if item.detected_at else None,
                **_build_sla_context(item),
            } for item in items],
        }
        return jsonify(payload), 200
    finally:
        session.close()


@app.route("/tenants/<tenant_id>/settings", methods=["GET", "POST"])
def tenant_settings(tenant_id: str):
    if request.method == "GET":
        return jsonify(settings_store.get(tenant_id)), 200

    payload = request.get_json(silent=True) or {}
    return jsonify(settings_store.update(tenant_id, payload)), 200


@app.route("/activity-feed", methods=["GET"])
def activity_feed():
    limit = int(request.args.get("limit", "5"))
    session = SessionLocal()
    try:
        discrepancies = session.query(Discrepancy).order_by(Discrepancy.detected_at.desc()).limit(limit).all()
        items = []
        for item in discrepancies:
            timeline = item.timeline or []
            if timeline:
                latest = timeline[-1]
                items.append({
                    "id": item.id,
                    "event": latest.get("event", "activity"),
                    "message": latest.get("message", item.details or "No message"),
                    "severity": item.severity,
                    "timestamp": latest.get("ts", item.detected_at.isoformat() if item.detected_at else None),
                    "trans_id": item.trans_id,
                })
            else:
                items.append({
                    "id": item.id,
                    "event": "created",
                    "message": item.details or "Incident created",
                    "severity": item.severity,
                    "timestamp": item.detected_at.isoformat() if item.detected_at else None,
                    "trans_id": item.trans_id,
                })
        return jsonify({"items": items}), 200
    finally:
        session.close()


@app.route("/assignment-queue", methods=["GET"])
def assignment_queue():
    session = SessionLocal()
    try:
        discrepancies = session.query(Discrepancy).filter(Discrepancy.resolved.is_(False)).order_by(Discrepancy.detected_at.desc()).all()
        items = []
        for item in discrepancies:
            queue_status = "assigned" if item.assignee else "needs_assignment"
            items.append({
                "id": item.id,
                "trans_id": item.trans_id,
                "severity": item.severity,
                "assignee": item.assignee or "Unassigned",
                "queue_status": queue_status,
                "anomaly_type": item.anomaly_type,
                "detected_at": item.detected_at.isoformat() if item.detected_at else None,
            })
        return jsonify({"items": items}), 200
    finally:
        session.close()


@app.route("/discrepancies/<discrepancy_id>/resolve", methods=["POST"])
def resolve_discrepancy(discrepancy_id: str):
    session = SessionLocal()
    try:
        discrepancy = session.get(Discrepancy, discrepancy_id)
        if not discrepancy:
            return jsonify({"error": "not found"}), 404
        payload = request.get_json(silent=True) or {}
        discrepancy.resolved = True
        discrepancy.resolved_at = datetime.now(timezone.utc)
        discrepancy.resolution_note = payload.get("note", discrepancy.resolution_note)
        discrepancy.details = payload.get("note", discrepancy.details)
        session.commit()
        return jsonify({"status": "resolved", "id": discrepancy.id}), 200
    finally:
        session.close()


@app.route("/discrepancies/bulk-resolve", methods=["POST"])
def bulk_resolve_discrepancies():
    session = SessionLocal()
    try:
        payload = request.get_json(silent=True) or {}
        ids = payload.get("ids", [])
        note = payload.get("note", "Bulk resolved")
        updated = 0
        for discrepancy_id in ids:
            discrepancy = session.get(Discrepancy, discrepancy_id)
            if not discrepancy:
                continue
            discrepancy.resolved = True
            discrepancy.resolved_at = datetime.now(timezone.utc)
            discrepancy.resolution_note = note
            discrepancy.details = note
            discrepancy.timeline = discrepancy.timeline or []
            discrepancy.timeline.append({
                "ts": datetime.now(timezone.utc).isoformat(),
                "event": "bulk_resolved",
                "message": note,
            })
            updated += 1
        session.commit()
        return jsonify({"status": "resolved", "updated": updated}), 200
    finally:
        session.close()


@app.route("/discrepancies/<discrepancy_id>/notes", methods=["POST"])
def save_notes(discrepancy_id: str):
    session = SessionLocal()
    try:
        discrepancy = session.get(Discrepancy, discrepancy_id)
        if not discrepancy:
            return jsonify({"error": "not found"}), 404
        payload = request.get_json(silent=True) or {}
        note = payload.get("note", "")
        if note:
            discrepancy.notes = (discrepancy.notes or "") + f"\n- {note}" if discrepancy.notes else f"- {note}"
            discrepancy.timeline = discrepancy.timeline or []
            discrepancy.timeline.append({
                "ts": datetime.now(timezone.utc).isoformat(),
                "event": "note_added",
                "message": note,
            })
            session.commit()
        return jsonify({"status": "saved", "notes": discrepancy.notes or ""}), 200
    finally:
        session.close()


@app.route("/discrepancies/<discrepancy_id>/assign", methods=["POST"])
def assign_discrepancy(discrepancy_id: str):
    session = SessionLocal()
    try:
        discrepancy = session.get(Discrepancy, discrepancy_id)
        if not discrepancy:
            return jsonify({"error": "not found"}), 404
        payload = request.get_json(silent=True) or {}
        assignee = payload.get("assignee", "")
        discrepancy.assignee = assignee
        discrepancy.timeline = discrepancy.timeline or []
        discrepancy.timeline.append({
            "ts": datetime.now(timezone.utc).isoformat(),
            "event": "assigned",
            "message": f"Assigned to {assignee}" if assignee else "Assignment cleared",
        })
        session.commit()
        return jsonify({"status": "assigned", "assignee": discrepancy.assignee}), 200
    finally:
        session.close()


@app.route("/analytics/sla-metrics", methods=["GET"])
def analytics_sla_metrics():
    """Returns SLA compliance statistics for critical incidents."""
    session = SessionLocal()
    try:
        discrepancies = session.query(Discrepancy).filter(Discrepancy.severity == "critical").all()
        on_track = 0
        warning = 0
        breaching = 0
        
        for item in discrepancies:
            sla_context = _build_sla_context(item)
            sla_status = sla_context.get("sla_status", "on_track")
            if sla_status == "on_track":
                on_track += 1
            elif sla_status == "warning":
                warning += 1
            elif sla_status == "breaching":
                breaching += 1
        
        return jsonify({
            "on_track": on_track,
            "warning": warning,
            "breaching": breaching,
            "total": len(discrepancies),
        }), 200
    finally:
        session.close()


@app.route("/analytics/resolution-times", methods=["GET"])
def analytics_resolution_times():
    """Returns average resolution times for resolved incidents."""
    session = SessionLocal()
    try:
        resolved_items = session.query(Discrepancy).filter(
            Discrepancy.resolved.is_(True),
            Discrepancy.resolved_at.isnot(None),
            Discrepancy.detected_at.isnot(None),
        ).all()
        
        if not resolved_items:
            return jsonify({
                "average_resolution_time": 0,
                "median_resolution_time": 0,
                "p95_resolution_time": 0,
            }), 200
        
        resolution_times = []
        for item in resolved_items:
            detected = _normalize_datetime(item.detected_at)
            resolved = _normalize_datetime(item.resolved_at)
            if detected and resolved:
                time_minutes = int((resolved - detected).total_seconds() // 60)
                resolution_times.append(max(0, time_minutes))
        
        if not resolution_times:
            return jsonify({
                "average_resolution_time": 0,
                "median_resolution_time": 0,
                "p95_resolution_time": 0,
            }), 200
        
        resolution_times.sort()
        average = sum(resolution_times) // len(resolution_times)
        median = resolution_times[len(resolution_times) // 2]
        p95_index = max(0, int(len(resolution_times) * 0.95) - 1)
        p95 = resolution_times[p95_index]
        
        return jsonify({
            "average_resolution_time": average,
            "median_resolution_time": median,
            "p95_resolution_time": p95,
        }), 200
    finally:
        session.close()


@app.route("/analytics/operator-stats", methods=["GET"])
def analytics_operator_stats():
    """Returns performance statistics grouped by operator/assignee."""
    session = SessionLocal()
    try:
        discrepancies = session.query(Discrepancy).all()
        operator_data: Dict[str, Dict[str, Any]] = {}
        
        for item in discrepancies:
            assignee = item.assignee or "Unassigned"
            if assignee not in operator_data:
                operator_data[assignee] = {
                    "assigned_count": 0,
                    "resolved_count": 0,
                    "total_resolution_time": 0,
                    "resolution_samples": 0,
                }
            
            operator_data[assignee]["assigned_count"] += 1
            
            if item.resolved:
                operator_data[assignee]["resolved_count"] += 1
                detected = _normalize_datetime(item.detected_at)
                resolved = _normalize_datetime(item.resolved_at)
                if detected and resolved:
                    time_minutes = max(0, int((resolved - detected).total_seconds() // 60))
                    operator_data[assignee]["total_resolution_time"] += time_minutes
                    operator_data[assignee]["resolution_samples"] += 1
        
        stats = []
        for operator, data in operator_data.items():
            avg_time = 0
            if data["resolution_samples"] > 0:
                avg_time = data["total_resolution_time"] // data["resolution_samples"]
            
            stats.append({
                "operator": operator,
                "assigned_count": data["assigned_count"],
                "resolved_count": data["resolved_count"],
                "average_resolution_time": avg_time,
            })
        
        # Sort by resolved_count descending
        stats.sort(key=lambda x: x["resolved_count"], reverse=True)
        return jsonify(stats), 200
    finally:
        session.close()


@app.route("/discrepancies/export/csv", methods=["GET"])
def export_discrepancies_csv():
    """Export incidents as CSV file."""
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
            download_name=f"pesaguard_incidents_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.csv"
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
    """Manage saved filter presets."""
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
    """Auto-escalate old unresolved critical incidents."""
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
    """Full-text search across incidents."""
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


if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5001")))
