"""Data access layer for Discrepancy records.

Used by reconciliation_engine.py and reconciliation_job.py as part of an
atomic transaction alongside the idempotency ledger write — see both files'
_persist_atomically / reconcile_with_idempotency functions.

CRITICAL: functions here NEVER call session.commit() or session.rollback()
themselves. The caller owns the transaction boundary — both existing
callers already commit once, after this DAO's write succeeds alongside the
idempotency ledger write, so that both succeed or fail together. If this
DAO committed on its own, it would silently break that atomicity guarantee.
"""

import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from models import Discrepancy

logger = logging.getLogger("pesaguard.discrepancy_dao")


def _serialize_details(details: Any) -> str:
    """Discrepancy.details is a Text column, not JSON, so callers passing a
    dict (the full reconciliation evaluation) need it serialized here.

    default=str is a deliberate safety net: the evaluation dict can contain
    the raw Daraja event payload, which should already be plain
    JSON-serializable primitives, but falling back to str() for anything
    unexpected (e.g. a stray datetime object) means this never raises and
    blocks the whole atomic write over a serialization edge case — it just
    degrades that one field to a string representation instead.
    """
    if details is None:
        return ""
    if isinstance(details, str):
        return details
    try:
        return json.dumps(details, default=str)
    except (TypeError, ValueError):
        logger.warning("Failed to JSON-serialize discrepancy details, falling back to str()")
        return str(details)


class DiscrepancyDAO:
    """Session-participating DAO — every method takes the caller's session
    and writes to it, but never commits or rolls back."""

    def save_discrepancy(
        self,
        session,
        id: str,
        trans_id: str,
        tenant_id: Optional[str],
        anomaly_type: str,
        severity: str,
        details: Any,
        status: Optional[str] = None,
        assignee: Optional[str] = None,
    ) -> Discrepancy:
        """Create or update a Discrepancy record on the given session.

        id is expected to be deterministic per (trans_id, status) — e.g.
        f"{trans_id}-{status}" — so re-flagging the same transaction/status
        combination (a retry, a re-evaluation after new data arrives) UPDATES
        the existing row instead of failing on a duplicate primary key.

        Does not commit. Does not flush unless the caller's later flush/
        commit triggers it — this keeps the write fully inside whatever
        transaction the caller is managing.
        """
        existing = session.get(Discrepancy, id)
        serialized_details = _serialize_details(details)

        if existing is not None:
            existing.anomaly_type = anomaly_type
            existing.severity = severity
            existing.details = serialized_details
            if status is not None:
                existing.status = status
            if tenant_id is not None:
                existing.tenant_id = tenant_id
            if assignee is not None:
                existing.assignee = assignee
            self._append_timeline(existing, event="updated", message=f"Re-flagged as {anomaly_type}")
            return existing

        record = Discrepancy(
            id=id,
            trans_id=trans_id,
            tenant_id=tenant_id,
            anomaly_type=anomaly_type,
            status=status or anomaly_type or "needs_review",
            severity=severity,
            details=serialized_details,
            resolved=False,
            detected_at=datetime.now(timezone.utc),
            assignee=assignee,
            timeline=[{
                "ts": datetime.now(timezone.utc).isoformat(),
                "event": "created",
                "message": f"Flagged as {anomaly_type}",
            }],
        )
        session.add(record)
        return record

    @staticmethod
    def _append_timeline(record: Discrepancy, event: str, message: str) -> None:
        timeline = record.timeline or []
        timeline.append({
            "ts": datetime.now(timezone.utc).isoformat(),
            "event": event,
            "message": message,
        })
        record.timeline = timeline

    def get_by_id(self, session, id: str, tenant_id: Optional[str] = None) -> Optional[Discrepancy]:
        """Tenant-scoped fetch — mirrors the tenant-isolation pattern already
        applied elsewhere (dashboard.py's _tenant_scoped_get, etc.). Pass
        tenant_id whenever the caller has an authenticated tenant context;
        omit it only for internal/system use (e.g. within reconciliation_job.py,
        which already knows the correct tenant_id for the event it's processing).
        """
        record = session.get(Discrepancy, id)
        if record is None:
            return None
        if tenant_id is not None and record.tenant_id != tenant_id:
            return None
        return record


# Default singleton instance, matching the import/usage style already used
# elsewhere in the codebase (e.g. `event_store = EventStore()` in event_store.py).
discrepancy_dao = DiscrepancyDAO()
