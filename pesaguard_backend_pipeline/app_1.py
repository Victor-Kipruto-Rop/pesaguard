"""
Minimal read-only API for viewing reconciliation status.
For the MVP pilot, skip building a full frontend — this can be
consumed directly, or wired into Retool/Django admin.
"""
import os

from flask import Flask, jsonify, request, abort
from sqlalchemy import create_engine, select, func
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import sys
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "..", "storage", "models"))
from pesaguard_backend_pipeline.models import Base, Transaction, Discrepancy  # noqa: E402

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://pesaguard:pesaguard@localhost:5432/pesaguard")

from pesaguard_backend_pipeline.app import app


def _create_engine(url: str):
    if url.startswith("sqlite:///:memory:") or url.startswith("sqlite:"):
        return create_engine(
            url,
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
    return create_engine(url, pool_pre_ping=True)


engine = _create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine, expire_on_commit=False)
Base.metadata.create_all(bind=engine)


def _legacy_request_id() -> str:
    return request.headers.get("X-Request-ID") or request.headers.get("X-Correlation-ID") or request.headers.get("X-Trace-Id") or os.getenv("REQUEST_ID") or "unknown-request"


def _legacy_success(payload: dict, status_code: int = 200, meta: dict | None = None):
    body = {
        "status": "success",
        "data": payload,
        "request_id": _legacy_request_id(),
        "tenant_id": request.headers.get("X-Tenant-ID") or os.getenv("TENANT_ID", "default"),
    }
    if meta is not None:
        body["meta"] = meta
    return jsonify(body), status_code


def _legacy_error(code: str, message: str, status_code: int = 400, details: dict | None = None):
    body = {
        "status": "error",
        "error": {"code": code, "message": message},
        "request_id": _legacy_request_id(),
        "tenant_id": request.headers.get("X-Tenant-ID") or os.getenv("TENANT_ID", "default"),
        "ResultCode": 1,
        "ResultDesc": message,
    }
    if details:
        body["error"]["details"] = details
    return jsonify(body), status_code

# Statuses that represent a genuinely unresolved reconciliation problem for a
# transaction. A "matched" transaction can still carry a Discrepancy row for a
# non-blocking anomaly (e.g. late_arriving_event) — that must NOT count against
# the reconciliation rate, or the metric misrepresents actual match quality.
BLOCKING_STATUSES = {"needs_review", "missing_payment"}


def _require_dashboard_auth():
    """Same pattern as the admin routes in app.py — this endpoint serves real
    customer transaction data (phone numbers, amounts via Discrepancy.details)
    and must not be reachable without a token."""
    token = request.headers.get("X-Admin-Token") or request.args.get("admin_token")
    admin_api_token = os.getenv("PESAGUARD_ADMIN_API_TOKEN")
    if not admin_api_token or token != admin_api_token:
        return _legacy_error("forbidden", "Forbidden: Missing or invalid admin token.", 403)
    return None


def _enforce_auth():
    """Only enforce auth on /api/ routes; allow other paths to pass through."""
    if not request.path.startswith("/api/"):
        return None
    auth_error = _require_dashboard_auth()
    if auth_error is not None:
        return auth_error
    return None


if not getattr(app, "_got_first_request", False):
    app.before_request(_enforce_auth)


@app.route("/api/discrepancies", methods=["GET"])
def list_discrepancies():
    """Paginated list of unresolved discrepancies, most recent first.

    Query params:
      limit  — max rows to return (default 50, capped at 200)
      offset — pagination offset (default 0)
      severity — optional filter, e.g. ?severity=critical
    """
    try:
        limit = min(int(request.args.get("limit", 50)), 200)
        offset = max(int(request.args.get("offset", 0)), 0)
    except ValueError:
        return _legacy_error("invalid_query", "limit and offset must be integers", 400, {"limit": request.args.get("limit"), "offset": request.args.get("offset")})

    severity = request.args.get("severity")

    session = Session()
    try:
        Base.metadata.create_all(bind=engine)
        query = select(Discrepancy).where(Discrepancy.resolved.is_(False))
        if severity:
            query = query.where(Discrepancy.severity == severity)
        query = query.order_by(Discrepancy.detected_at.desc()).offset(offset).limit(limit)

        rows = session.execute(query).scalars().all()
        total_open = session.query(Discrepancy).filter_by(resolved=False).count()

        return _legacy_success({
            "results": [
                {
                    "id": r.id,
                    "trans_id": r.trans_id,
                    "anomaly_type": r.anomaly_type,
                    "severity": r.severity,
                    "details": r.details,
                    "detected_at": r.detected_at.isoformat() if r.detected_at else None,
                }
                for r in rows
            ],
            "total_open": total_open,
            "limit": limit,
            "offset": offset,
        }, meta={"resource": "discrepancies"})
    finally:
        session.close()


@app.route("/api/stats/summary", methods=["GET"])
def summary():
    """Summary stats. reconciliation_rate reflects the share of DISTINCT
    transactions with no blocking discrepancy (needs_review / missing_payment),
    not raw discrepancy row count — a transaction can carry a non-blocking
    discrepancy (e.g. late arrival) while still being correctly matched, and
    must not be counted as unreconciled."""
    session = Session()
    try:
        Base.metadata.create_all(bind=engine)
        total_transactions = session.query(Transaction).count()

        blocked_transaction_count = (
            session.query(func.count(func.distinct(Discrepancy.trans_id)))
            .filter(
                Discrepancy.resolved.is_(False),
                Discrepancy.anomaly_type.in_(BLOCKING_STATUSES),
            )
            .scalar()
        ) or 0

        open_discrepancies_total = session.query(Discrepancy).filter_by(resolved=False).count()

        return _legacy_success({
            "total_transactions": total_transactions,
            "open_discrepancies_total": open_discrepancies_total,
            "blocked_transactions": blocked_transaction_count,
            "reconciliation_rate": (
                round(1 - (blocked_transaction_count / total_transactions), 4)
                if total_transactions else None
            ),
        }, meta={"resource": "summary"})
    finally:
        session.close()


