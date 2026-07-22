"""
Advanced Features API for PesaGuard - Webhooks, Auth, Email, Escalations, On-Call, Search, Rate Limiting.
Integrates webhook notifications, email distribution, custom escalation rules, on-call rotation tracking,
historical trends, advanced boolean search, rate limiting, and API authentication/RBAC.

NOTE ON CONSOLIDATION: this file replaces the old separate `features.py`
(create_features_app). That file only duplicated routes already implemented
correctly (with auth + tenant scoping) in dashboard.py:
/discrepancies/export/csv, /analytics/incident-trends, /incidents/filters/presets,
/incidents/auto-escalate, /analytics/reconciliation-report, /incidents/bulk-assign,
/incidents/search. Delete features.py and its registration call — nothing in
it is unique. Everything below is functionality that exists ONLY here
(auth/tokens, webhooks, escalation rules, on-call, email, advanced search,
public customer endpoints, rate-limited bulk ops).
"""

import hashlib
import hmac
import json
import logging
import os
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from flask import Flask, jsonify, request, g
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from webhook_manager import WebhookManager
from auth_rbac import AuthRBAC, require_auth, require_tenant_access, get_current_user
from rate_limiter import rate_limit, get_rate_limit_status
from email_service import EmailService
from escalation_engine import EscalationEngine
from on_call_service import OnCallService
from search_engine import AdvancedSearchEngine
from action_audit import ActionAuditEntry
from models import Base, Discrepancy, Report, DeadLetter
from tenant_settings import TenantSettingsStore

configure_logging = lambda: None  # Import from logging_utils if available
logger = logging.getLogger("pesaguard.advanced_features")

app = Flask(__name__)
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://pesaguard:pesaguard@localhost:5432/pesaguard")


def create_db_engine(url: str):
    if url.startswith("sqlite:///:memory:"):
        return create_engine(
            url,
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )

    return create_engine(url, pool_pre_ping=True)


engine = create_db_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)

email_service = EmailService(
    smtp_server=os.getenv("SMTP_SERVER", "localhost"),
    smtp_port=int(os.getenv("SMTP_PORT", 587)),
    from_email=os.getenv("SMTP_FROM_EMAIL", "noreply@pesaguard.local"),
)
settings_store = TenantSettingsStore()


def resolve_email_locale(tenant_id: str | None, user_id: str | None = None, settings_path=None) -> str:
    """Resolve the locale to use for email notifications based on tenant settings."""
    if not tenant_id:
        tenant_id = "default"
    if settings_path is not None:
        store = TenantSettingsStore(str(settings_path))
    else:
        store = settings_store
    return store.resolve_locale(str(tenant_id), user_id=user_id, fallback_locale="en")


def _record_action_audit(session, tenant_id: str, actor: str, action: str, details: dict | None = None) -> None:
    try:
        # FIXED: `uuid` was used here but never imported anywhere in the file.
        # Every call to this function raised NameError, which was silently
        # swallowed by the except below — meaning NO action audit entries
        # were ever actually being recorded, for any action, in the entire
        # advanced-features API. Audit logging was completely non-functional.
        entry = ActionAuditEntry(
            id=f"audit_{uuid.uuid4().hex[:12]}",
            tenant_id=tenant_id,
            actor=actor,
            action=action,
            details=details or {},
        )
        session.add(entry)
        session.commit()
    except Exception:
        logger.exception("Failed to persist audit entry")


def _incident_belongs_to_tenant(session, incident_id: str, tenant_id: str) -> Optional[Discrepancy]:
    """Fetch a Discrepancy by ID, but only if it belongs to tenant_id.

    Replaces the previous pattern of `session.query(Discrepancy).filter(Discrepancy.id == incident_id).first()`
    with no tenant filter — @require_tenant_access() only confirms the caller
    is allowed to act on the tenant_id THEY PASSED IN; it never confirms the
    fetched record actually belongs to that tenant. Without this check, a
    valid token for tenant A could bulk-assign or bulk-escalate tenant B's
    incidents just by supplying tenant B's incident IDs.
    """
    return (
        session.query(Discrepancy)
        .filter(Discrepancy.id == incident_id, Discrepancy.tenant_id == tenant_id)
        .first()
    )


@app.before_request
def _ensure_tables():
    Base.metadata.create_all(engine)


@app.after_request
def _after_request(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
    return response


# ============================================================================
# AUTHENTICATION & TOKENS
# ============================================================================

# ----------------------------------------------------------------------------
# INTERIM credential store. There is no User table in models.py yet, so this
# is a real but temporary fix: credentials live in an environment variable as
# JSON, passwords are checked with a proper salted hash (stdlib hashlib,
# pbkdf2_hmac — no new dependency needed), and comparison is constant-time.
# This replaces the previous code, which accepted ANY non-empty password for
# ANY username and handed out a real signed token for whatever tenant_id the
# caller supplied in the request body — i.e. no authentication at all.
#
# This is NOT a long-term solution. Before onboarding more than a couple of
# pilot customers, replace this with a real `User` table (hashed passwords,
# one row per user, proper account management, password reset flow, etc.)
# and swap out `_verify_credentials` for a DB lookup. Keeping this as an env
# var is fine for a single pilot customer; it does not scale to self-serve
# signup.
#
# Expected env var PESAGUARD_AUTH_USERS_JSON, a JSON array like:
# [
#   {
#     "username": "admin",
#     "tenant_id": "pilot_customer_1",
#     "roles": ["admin"],
#     "salt_hex": "<hex salt, generate with os.urandom(16).hex()>",
#     "password_hash_hex": "<pbkdf2_hmac('sha256', password.encode(), salt, 200000).hex()>"
#   }
# ]
# ----------------------------------------------------------------------------

_PBKDF2_ITERATIONS = 200_000


def _hash_password(password: str, salt_hex: str) -> str:
    salt = bytes.fromhex(salt_hex)
    return hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, _PBKDF2_ITERATIONS).hex()


def _load_auth_users() -> Dict[str, Dict[str, Any]]:
    raw = os.getenv("PESAGUARD_AUTH_USERS_JSON", "")
    if not raw:
        logger.error(
            "PESAGUARD_AUTH_USERS_JSON is not set — no users can log in. "
            "This is intentional: without it, login must fail closed, not "
            "fall back to accepting anything."
        )
        return {}
    try:
        users = json.loads(raw)
        return {u["username"]: u for u in users if "username" in u}
    except (json.JSONDecodeError, TypeError, KeyError):
        logger.exception("PESAGUARD_AUTH_USERS_JSON is malformed — no users can log in")
        return {}


def _verify_credentials(username: str, password: str) -> Optional[Dict[str, Any]]:
    """Returns the matching user record if username/password are correct, else None.

    Fails closed: any missing config, malformed record, or mismatch returns
    None. Uses hmac.compare_digest for constant-time comparison so response
    timing doesn't leak whether a partial hash matched.
    """
    users = _load_auth_users()
    user = users.get(username)
    if not user:
        return None
    try:
        computed = _hash_password(password, user["salt_hex"])
    except (KeyError, ValueError):
        logger.exception("Malformed auth record for username=%s", username)
        return None
    if not hmac.compare_digest(computed, user.get("password_hash_hex", "")):
        return None
    return user


@app.route("/auth/login", methods=["POST"])
def login():
    """Generate authentication token.

    FIXED: previously accepted ANY non-empty password for ANY username, and
    trusted a tenant_id supplied directly in the request body with no check
    that the credentials actually belonged to that tenant. That meant anyone
    could obtain a valid, signed token for any tenant/role by guessing a
    username. Now requires a real password match against the interim
    credential store above.
    """
    data = request.json or {}
    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return jsonify({"error": "missing_credentials"}), 400

    user = _verify_credentials(username, password)
    if not user:
        # Deliberately generic error — do not reveal whether the username
        # exists, only that the login attempt failed.
        logger.warning("Failed login attempt for username=%s", username)
        return jsonify({"error": "invalid_credentials"}), 401

    token = AuthRBAC.generate_token(
        user_id=f"user_{username}",
        username=username,
        tenant_id=user["tenant_id"],  # from the verified record, never from the request body
        roles=user.get("roles", ["operator"]),
    )

    return jsonify({
        "token": token,
        "user_id": f"user_{username}",
        "username": username,
        "tenant_id": user["tenant_id"],
        "roles": user.get("roles", ["operator"]),
        "expires_in": 86400,
    }), 200


@app.route("/auth/verify", methods=["GET"])
@require_auth()
def verify_token():
    """Verify current authentication token."""
    user = get_current_user()
    if not user:
        return jsonify({"error": "not_authenticated"}), 401

    return jsonify({
        "user_id": user.user_id,
        "username": user.username,
        "tenant_id": user.tenant_id,
        "roles": user.roles,
        "permissions": user.permissions,
    }), 200


@app.route("/auth/revoke", methods=["POST"])
@require_auth("manage:users")
def revoke_token():
    """Revoke an active authentication token."""
    payload = request.json or {}
    token = payload.get("token")
    if not token:
        return jsonify({"error": "missing_token"}), 400

    AuthRBAC.revoke_token(token)
    return jsonify({"status": "revoked"}), 200


# ============================================================================
# WEBHOOK MANAGEMENT
# ============================================================================

@app.route("/webhooks", methods=["POST"])
@require_auth("manage:webhooks")
@require_tenant_access()
def create_webhook():
    """Register a new webhook for a tenant."""
    data = request.json or {}
    tenant_id = data.get("tenant_id")
    session = SessionLocal()

    try:
        webhook_mgr = WebhookManager(session)
        result = webhook_mgr.register_webhook(
            tenant_id=tenant_id,
            url=data.get("url"),
            event_types=data.get("event_types", ["escalation"]),
            retry_attempts=data.get("retry_attempts", 3),
            timeout_seconds=data.get("timeout_seconds", 10),
        )
        _record_action_audit(
            session,
            tenant_id=tenant_id,
            actor=get_current_user().user_id if get_current_user() else "system",
            action="create_webhook",
            details={"webhook_id": result.get("id"), "url": data.get("url"), "event_types": result.get("event_types")},
        )
        return jsonify(result), 201
    finally:
        session.close()


@app.route("/webhooks", methods=["GET"])
@require_auth("manage:webhooks")
@require_tenant_access()
def list_webhooks():
    """List all webhooks for a tenant."""
    tenant_id = request.args.get("tenant_id")
    session = SessionLocal()

    try:
        webhook_mgr = WebhookManager(session)
        webhooks = webhook_mgr.get_webhooks(tenant_id)
        return jsonify({
            "tenant_id": tenant_id,
            "webhooks": [
                {
                    "id": w.id,
                    "url": w.url,
                    "event_types": w.event_types,
                    "active": w.active,
                    "created_at": w.created_at.isoformat(),
                }
                for w in webhooks
            ],
        }), 200
    finally:
        session.close()


@app.route("/webhooks/<webhook_id>", methods=["PUT"])
@require_auth("manage:webhooks")
def update_webhook(webhook_id):
    """Update webhook configuration."""
    data = request.json or {}
    session = SessionLocal()

    try:
        webhook_mgr = WebhookManager(session)
        result = webhook_mgr.update_webhook(webhook_id, **data)
        _record_action_audit(
            session,
            tenant_id=data.get("tenant_id", get_current_user().tenant_id if get_current_user() else "default"),
            actor=get_current_user().user_id if get_current_user() else "system",
            action="update_webhook",
            details={"webhook_id": webhook_id, **data},
        )
        return jsonify(result), 200
    finally:
        session.close()


@app.route("/webhooks/<webhook_id>/deliveries", methods=["GET"])
@require_auth("manage:webhooks")
def get_webhook_deliveries(webhook_id):
    """Get delivery history for a webhook."""
    limit = request.args.get("limit", 50, type=int)
    session = SessionLocal()

    try:
        webhook_mgr = WebhookManager(session)
        deliveries = webhook_mgr.get_delivery_history(webhook_id, limit=limit)
        return jsonify({
            "webhook_id": webhook_id,
            "deliveries": deliveries,
        }), 200
    finally:
        session.close()


# ============================================================================
# ESCALATION RULES
# ============================================================================

@app.route("/escalation-rules", methods=["POST"])
@require_auth("write:escalation_rules")
@require_tenant_access()
def create_escalation_rule():
    """Create a custom escalation rule for a tenant."""
    data = request.json or {}
    tenant_id = data.get("tenant_id")
    session = SessionLocal()

    try:
        engine = EscalationEngine(session)
        result = engine.create_rule(
            tenant_id=tenant_id,
            name=data.get("name"),
            description=data.get("description"),
            condition_field=data.get("condition_field"),
            condition_operator=data.get("condition_operator"),
            condition_value=data.get("condition_value"),
            action=data.get("action"),
            target=data.get("target"),
            webhook_url=data.get("webhook_url"),
            priority=data.get("priority", 0),
        )
        _record_action_audit(
            session,
            tenant_id=tenant_id,
            actor=get_current_user().user_id if get_current_user() else "system",
            action="create_escalation_rule",
            details={"rule_id": result.get("id"), "name": data.get("name")},
        )
        return jsonify(result), 201
    finally:
        session.close()


@app.route("/escalation-rules", methods=["GET"])
@require_auth("read:discrepancies")
@require_tenant_access()
def list_escalation_rules():
    """List escalation rules for a tenant."""
    tenant_id = request.args.get("tenant_id")
    session = SessionLocal()

    try:
        engine = EscalationEngine(session)
        rules = engine.get_rules(tenant_id)
        return jsonify({
            "tenant_id": tenant_id,
            "rules": rules,
        }), 200
    finally:
        session.close()


@app.route("/escalation-rules/<rule_id>", methods=["PUT"])
@require_auth("write:escalation_rules")
def update_escalation_rule(rule_id):
    """Update an escalation rule."""
    data = request.json or {}
    session = SessionLocal()

    try:
        engine = EscalationEngine(session)
        result = engine.update_rule(rule_id, **data)
        return jsonify(result), 200
    finally:
        session.close()


# ============================================================================
# ON-CALL ROTATIONS
# ============================================================================

@app.route("/on-call/rotations", methods=["POST"])
@require_auth("manage:on_call")
@require_tenant_access()
def create_on_call_rotation():
    """Create an on-call rotation."""
    data = request.json or {}
    tenant_id = data.get("tenant_id")
    session = SessionLocal()

    try:
        service = OnCallService(session)
        shift_start = datetime.fromisoformat(data.get("shift_start"))
        shift_end = datetime.fromisoformat(data.get("shift_end"))

        result = service.create_rotation(
            tenant_id=tenant_id,
            operator_id=data.get("operator_id"),
            operator_name=data.get("operator_name"),
            operator_email=data.get("operator_email"),
            operator_phone=data.get("operator_phone"),
            shift_start=shift_start,
            shift_end=shift_end,
            escalation_level=data.get("escalation_level", 1),
        )
        _record_action_audit(
            session,
            tenant_id=tenant_id,
            actor=get_current_user().user_id if get_current_user() else "system",
            action="create_on_call_rotation",
            details={"operator_id": data.get("operator_id"), "shift_start": shift_start.isoformat(), "shift_end": shift_end.isoformat()},
        )
        return jsonify(result), 201
    finally:
        session.close()


@app.route("/on-call/rotations/active", methods=["GET"])
@require_auth("read:discrepancies")
@require_tenant_access()
def get_active_on_call():
    """Get active on-call operators for a tenant."""
    tenant_id = request.args.get("tenant_id")
    session = SessionLocal()

    try:
        service = OnCallService(session)
        rotations = service.get_active_rotations(tenant_id)
        coverage = service.get_coverage_status(tenant_id)

        return jsonify({
            "tenant_id": tenant_id,
            "coverage": coverage,
            "active_rotations": rotations,
        }), 200
    finally:
        session.close()


@app.route("/on-call/schedule/<operator_id>", methods=["GET"])
@require_auth("read:discrepancies")
def get_operator_schedule(operator_id):
    """Get operator's on-call schedule."""
    tenant_id = request.args.get("tenant_id")
    days = request.args.get("days", 30, type=int)
    session = SessionLocal()

    try:
        service = OnCallService(session)
        schedule = service.get_operator_schedule(tenant_id, operator_id, days)
        return jsonify({
            "operator_id": operator_id,
            "tenant_id": tenant_id,
            "days": days,
            "schedule": schedule,
        }), 200
    finally:
        session.close()


@app.route("/on-call/bulk", methods=["POST"])
@require_auth("manage:on_call")
@require_tenant_access()
def bulk_create_on_call():
    """Bulk create on-call rotations."""
    data = request.json or {}
    tenant_id = data.get("tenant_id")
    rotations_data = data.get("rotations", [])
    session = SessionLocal()

    try:
        service = OnCallService(session)
        result = service.bulk_create_rotations(tenant_id, rotations_data)
        _record_action_audit(
            session,
            tenant_id=tenant_id,
            actor=get_current_user().user_id if get_current_user() else "system",
            action="bulk_create_on_call_rotations",
            details={"created": result.get("created", 0)},
        )
        return jsonify(result), 201
    finally:
        session.close()


# ============================================================================
# EMAIL NOTIFICATIONS
# ============================================================================

@app.route("/emails/reconciliation", methods=["POST"])
@require_auth("write:discrepancies")
@require_tenant_access()
def send_reconciliation_email():
    """Send reconciliation report via email."""
    data = request.json or {}
    tenant_id = data.get("tenant_id")
    recipient = data.get("recipient_email")
    report_data = data.get("report_data", {})
    session = SessionLocal()

    try:
        current_user = get_current_user()
        locale = resolve_email_locale(
            tenant_id,
            user_id=current_user.user_id if current_user else data.get("user_id") or request.args.get("user_id"),
        )
        result = email_service.send_reconciliation_report(
            session, tenant_id, recipient, report_data, locale=locale
        )
        _record_action_audit(
            session,
            tenant_id=tenant_id,
            actor=get_current_user().user_id if get_current_user() else "system",
            action="send_reconciliation_email",
            details={"recipient": recipient, "report_data": report_data},
        )
        return jsonify(result), 200
    finally:
        session.close()


@app.route("/emails/escalation", methods=["POST"])
@require_auth("write:discrepancies")
@require_tenant_access()
def send_escalation_email():
    """Send escalation notification."""
    data = request.json or {}
    tenant_id = data.get("tenant_id")
    recipient = data.get("recipient_email")
    incident = data.get("incident_data", {})
    session = SessionLocal()

    try:
        current_user = get_current_user()
        locale = resolve_email_locale(
            tenant_id,
            user_id=current_user.user_id if current_user else data.get("user_id") or request.args.get("user_id"),
        )
        result = email_service.send_escalation_notification(
            session, tenant_id, recipient, incident, locale=locale
        )
        _record_action_audit(
            session,
            tenant_id=tenant_id,
            actor=get_current_user().user_id if get_current_user() else "system",
            action="send_escalation_email",
            details={"recipient": recipient, "incident": incident},
        )
        return jsonify(result), 200
    finally:
        session.close()


@app.route("/emails/history", methods=["GET"])
@require_auth("read:discrepancies")
@require_tenant_access()
def get_email_history():
    """Get email notification history for a tenant."""
    tenant_id = request.args.get("tenant_id")
    limit = request.args.get("limit", 50, type=int)
    session = SessionLocal()

    try:
        history = email_service.get_email_history(session, tenant_id, limit)
        return jsonify({
            "tenant_id": tenant_id,
            "emails": history,
        }), 200
    finally:
        session.close()


# ============================================================================
# ADVANCED SEARCH
# ============================================================================

@app.route("/search", methods=["GET"])
@require_auth("read:discrepancies")
@require_tenant_access()
def advanced_search():
    """Execute advanced search with boolean operators."""
    tenant_id = request.args.get("tenant_id")
    query = request.args.get("q", "")
    limit = request.args.get("limit", 50, type=int)
    offset = request.args.get("offset", 0, type=int)
    session = SessionLocal()

    try:
        search = AdvancedSearchEngine(session)
        result = search.search(tenant_id, query, limit=limit, offset=offset)
        return jsonify(result), 200
    finally:
        session.close()


@app.route("/search/filters", methods=["GET"])
@require_auth("read:discrepancies")
@require_tenant_access()
def search_filters():
    """Get available filter values for search."""
    tenant_id = request.args.get("tenant_id")
    session = SessionLocal()

    try:
        search = AdvancedSearchEngine(session)
        filters = search.suggest_filters(tenant_id)
        return jsonify({
            "tenant_id": tenant_id,
            "available_filters": filters,
        }), 200
    finally:
        session.close()


@app.route("/search/structured", methods=["GET"])
@require_auth("read:discrepancies")
@require_tenant_access()
def structured_search():
    """Search using structured filters."""
    tenant_id = request.args.get("tenant_id")
    session = SessionLocal()

    try:
        search = AdvancedSearchEngine(session)
        result = search.search_by_filters(
            tenant_id=tenant_id,
            severity=request.args.get("severity"),
            status=request.args.get("status"),
            anomaly_type=request.args.get("anomaly_type"),
            resolved=request.args.get("resolved", type=lambda x: x.lower() == "true"),
            assignee=request.args.get("assignee"),
            days_back=request.args.get("days_back", 30, type=int),
            limit=request.args.get("limit", 50, type=int),
            offset=request.args.get("offset", 0, type=int),
        )
        return jsonify(result), 200
    finally:
        session.close()


# Public/customer-facing endpoints for tenants to pull their own data
@app.route("/public/customers/<tenant_id>/reconciliations", methods=["GET"])
@require_auth("read:discrepancies")
@require_tenant_access()
def public_get_reconciliations(tenant_id: str):
    """Return recent reconciliation outcomes for the tenant."""
    limit = request.args.get("limit", 50, type=int)
    offset = request.args.get("offset", 0, type=int)
    session = SessionLocal()

    try:
        q = (
            session.query(Discrepancy)
            .filter(Discrepancy.tenant_id == tenant_id)
            .order_by(Discrepancy.detected_at.desc())
            .limit(limit)
            .offset(offset)
        )
        rows = q.all()
        return jsonify({
            "tenant_id": tenant_id,
            "count": len(rows),
            "reconciliations": [
                {
                    "id": r.id,
                    "trans_id": r.trans_id,
                    "anomaly_type": r.anomaly_type,
                    "status": r.status,
                    "severity": r.severity,
                    "details": r.details,
                    "detected_at": r.detected_at.isoformat() if r.detected_at else None,
                    "resolved": bool(r.resolved),
                }
                for r in rows
            ],
        }), 200
    finally:
        session.close()


@app.route("/public/customers/<tenant_id>/reports", methods=["GET"])
@require_auth("read:analytics")
@require_tenant_access()
def public_get_reports(tenant_id: str):
    """Return generated reports for the tenant (daily/weekly)."""
    limit = request.args.get("limit", 50, type=int)
    offset = request.args.get("offset", 0, type=int)
    session = SessionLocal()

    try:
        q = (
            session.query(Report)
            .filter(Report.tenant_id == tenant_id)
            .order_by(Report.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        rows = q.all()
        return jsonify({
            "tenant_id": tenant_id,
            "count": len(rows),
            "reports": [
                {
                    "id": r.id,
                    "report_type": r.report_type,
                    "period_start": r.period_start.isoformat() if r.period_start else None,
                    "period_end": r.period_end.isoformat() if r.period_end else None,
                    "status": r.status,
                    "created_at": r.created_at.isoformat() if r.created_at else None,
                    "content": r.content,
                }
                for r in rows
            ],
        }), 200
    finally:
        session.close()


# ============================================================================
# RATE LIMITED BULK OPERATIONS
# ============================================================================

@app.route("/bulk/assign", methods=["POST"])
@require_auth("bulk:operations")
@rate_limit(max_requests_per_minute=5, tokens_per_request=1, endpoint_name="bulk_assign")
@require_tenant_access()
def bulk_assign_incidents():
    """Bulk assign incidents with rate limiting."""
    data = request.json or {}
    tenant_id = data.get("tenant_id")
    incident_ids = data.get("incident_ids", [])
    assignee = data.get("assignee")
    session = SessionLocal()

    try:
        updated = 0
        skipped_ids = []
        for incident_id in incident_ids[:100]:  # Cap at 100 per request
            # FIXED: previously fetched by ID with NO tenant filter — a valid
            # token for tenant A could assign tenant B's incidents just by
            # knowing/guessing their IDs. require_tenant_access() only checks
            # the tenant_id param the caller supplied, not the fetched row.
            incident = _incident_belongs_to_tenant(session, incident_id, tenant_id)
            if incident:
                incident.assignee = assignee
                updated += 1
            else:
                skipped_ids.append(incident_id)

        session.commit()
        _record_action_audit(
            session,
            tenant_id=tenant_id,
            actor=get_current_user().user_id if get_current_user() else "system",
            action="bulk_assign_incidents",
            details={"updated": updated, "skipped_ids": skipped_ids, "assignee": assignee},
        )
        return jsonify({
            "updated": updated,
            "skipped_ids": skipped_ids,
            "rate_limit": get_rate_limit_status(),
        }), 200
    finally:
        session.close()


@app.route("/bulk/escalate", methods=["POST"])
@require_auth("bulk:operations")
@rate_limit(max_requests_per_minute=3, tokens_per_request=2, endpoint_name="bulk_escalate")
@require_tenant_access()
def bulk_escalate_incidents():
    """Bulk escalate incidents with rate limiting."""
    data = request.json or {}
    tenant_id = data.get("tenant_id")
    incident_ids = data.get("incident_ids", [])
    session = SessionLocal()

    try:
        escalated = []
        skipped_ids = []
        engine = EscalationEngine(session)

        for incident_id in incident_ids[:50]:  # Cap at 50 per request
            # FIXED: same tenant-filter gap as bulk_assign_incidents above —
            # a valid token for tenant A could previously escalate tenant B's
            # incidents by ID.
            incident = _incident_belongs_to_tenant(session, incident_id, tenant_id)
            if incident:
                result = engine.evaluate_and_escalate(tenant_id, incident)
                escalated.append(result)
            else:
                skipped_ids.append(incident_id)

        _record_action_audit(
            session,
            tenant_id=tenant_id,
            actor=get_current_user().user_id if get_current_user() else "system",
            action="bulk_escalate_incidents",
            details={"escalated_count": len(escalated), "skipped_ids": skipped_ids},
        )
        return jsonify({
            "escalated": len(escalated),
            "details": escalated,
            "skipped_ids": skipped_ids,
            "rate_limit": get_rate_limit_status(),
        }), 200
    finally:
        session.close()


if __name__ == "__main__":
    debug_mode = os.getenv("FLASK_DEBUG", "0") == "1"
    if debug_mode:
        logger.warning("Running with debug=True — never do this in production (exposes the interactive debugger)")
    app.run(debug=debug_mode, host="0.0.0.0", port=int(os.getenv("PORT", 5002)))
