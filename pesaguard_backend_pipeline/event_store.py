"""A lightweight durable event store for idempotency and replay.

Uses ProcessedTransaction table as the idempotency source of truth.
Each webhook callback from Daraja is recorded exactly once via unique constraint.
"""

import os
import uuid
import logging
from datetime import datetime, timezone
from typing import Optional
from enum import Enum

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from models import Base, Transaction, ProcessedTransaction

logger = logging.getLogger("pesaguard.event_store")


class ProcessResult(str, Enum):
    """Outcome of attempting to record a webhook callback.

    The webhook handler MUST branch on this, not treat it as a plain boolean —
    STORED and DUPLICATE both mean "return 200 to Daraja, no retry needed".
    ERROR means "return 5xx so Daraja retries" — a genuine failure must never
    be indistinguishable from a benign duplicate, or real transactions can be
    silently dropped.
    """
    STORED = "stored"        # new transaction, successfully recorded
    DUPLICATE = "duplicate"  # already processed before — safe no-op
    ERROR = "error"          # genuine failure — caller should signal retry


class EventStore:
    """Persist processed transactions so duplicate callbacks can be ignored safely.

    Uses ProcessedTransaction table as explicit idempotency ledger. This table tracks
    which webhook callbacks (identified by Daraja TransID) have been received and processed.
    The unique constraint on daraja_trans_id is the hard guarantee against race conditions —
    the already_processed() check is just an optimization to skip needless work, not the
    actual safety mechanism.
    """

    def __init__(self, database_url: Optional[str] = None, isolation_level: str = "serializable"):
        self.database_url = database_url or os.getenv("DATABASE_URL", "postgresql://pesaguard:pesaguard@localhost:5432/pesaguard")
        self.isolation_level = isolation_level  # serializable ensures no phantom reads during idempotency checks
        self.engine = None
        self.Session = None
        self._initialized = False

    def _ensure_ready(self) -> None:
        if self._initialized:
            return

        self.engine = create_engine(
            self.database_url,
            isolation_level=self.isolation_level if self.database_url.startswith("postgresql") else None,
        )
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
        self._initialized = True

    def already_processed(self, trans_id: str, source_ip: str = None) -> bool:
        """Check if a webhook callback has already been processed (idempotency gate).

        This is an optimization only — the real guarantee is the unique constraint
        enforced in mark_processed(). Conservative: returns True on DB errors, so a
        transient read failure doesn't cause reprocessing (mark_processed's own
        unique constraint would catch a true duplicate anyway; returning True here
        just avoids the extra work and logs the situation for visibility).

        Args:
            trans_id: Daraja M-Pesa TransID
            source_ip: Optional IP address of callback source (for audit)

        Returns:
            True if this callback has been seen before, or if the check itself
            failed (conservative fallback). False only on a confirmed "not seen".
        """
        if not trans_id:
            return False
        try:
            self._ensure_ready()
            with self.Session() as session:
                existing = session.query(ProcessedTransaction).filter(
                    ProcessedTransaction.daraja_trans_id == str(trans_id)
                ).first()
                return existing is not None
        except SQLAlchemyError:
            logger.exception(
                "already_processed() check failed for trans_id=%s — assuming processed "
                "(conservative fallback); mark_processed's unique constraint remains the "
                "real safety net.",
                trans_id,
            )
            return True

    def mark_processed(
        self,
        payload: dict,
        tenant_id: str = None,
        source_ip: str = None,
        signature_verified: bool = False,
    ) -> ProcessResult:
        """Atomically record that a webhook callback has been processed.

        Creates a ProcessedTransaction record with a unique constraint on
        daraja_trans_id. Distinguishes an expected duplicate (unique constraint
        violation) from a genuine error (connection failure, etc.) — callers must
        NOT treat these the same way. A genuine error should cause the webhook
        handler to return a non-200 so Daraja retries; a duplicate should return
        200 since it's already safely stored.

        Args:
            payload: Daraja webhook payload dict
            tenant_id: Optional tenant identifier
            source_ip: Optional IP address of callback source
            signature_verified: Whether HMAC signature was valid

        Returns:
            ProcessResult.STORED    — new transaction, recorded successfully
            ProcessResult.DUPLICATE — already recorded, safe no-op
            ProcessResult.ERROR     — genuine failure, caller should signal retry
        """
        trans_id = str(payload.get("TransID", ""))
        if not trans_id:
            logger.error("mark_processed() called with missing TransID in payload")
            return ProcessResult.ERROR

        try:
            self._ensure_ready()
        except SQLAlchemyError:
            logger.exception("EventStore failed to initialize DB engine")
            return ProcessResult.ERROR

        try:
            with self.Session() as session:
                pt_record = ProcessedTransaction(
                    id=f"pt_{uuid.uuid4().hex[:12]}",
                    daraja_trans_id=trans_id,
                    tenant_id=tenant_id,
                    status="received",
                    source_ip=source_ip,
                    signature_verified=signature_verified,
                    webhook_attempt_number=int(payload.get("retry_count", 1)),
                )
                session.add(pt_record)

                t_record = Transaction(
                    trans_id=trans_id,
                    trans_amount=float(payload.get("TransAmount", 0)),
                    msisdn=str(payload.get("MSISDN", "")),
                    business_short_code=str(payload.get("BusinessShortCode", "")),
                    trans_time=str(payload.get("TransTime", "")),
                    raw_payload=payload,
                    created_at=datetime.now(timezone.utc),
                )
                session.add(t_record)

                session.commit()
                return ProcessResult.STORED

        except IntegrityError:
            # Expected path: unique constraint on daraja_trans_id (or Transaction.trans_id
            # primary key) rejected a row we've already stored. This is the hard guarantee
            # against race conditions — two near-simultaneous callbacks for the same
            # transaction will have exactly one winner here.
            logger.info(
                "Duplicate webhook callback ignored for trans_id=%s (unique constraint)",
                trans_id,
            )
            return ProcessResult.DUPLICATE

        except SQLAlchemyError:
            # Genuine failure — connection drop, deadlock, disk full, etc. Must NOT be
            # treated like a duplicate. Log loudly and let the caller decide to retry.
            logger.exception(
                "mark_processed() failed for trans_id=%s due to a DB error, not a "
                "duplicate — this transaction was NOT stored and needs retry/investigation.",
                trans_id,
            )
            return ProcessResult.ERROR

    def mark_processed_in_session(
        self,
        session,
        payload: dict,
        tenant_id: str = None,
        source_ip: str = None,
        signature_verified: bool = False,
    ) -> ProcessResult:
        """Same as mark_processed(), but writes using a session YOU provide and pass control
        of committing back to you.

        Use this instead of mark_processed() whenever the idempotency write must be atomic
        with another write (e.g. a Discrepancy record) — pass the same session to both, and
        commit once, after both succeed. This function does NOT commit or roll back; the
        caller owns the transaction boundary.

        Returns:
            ProcessResult.STORED    — rows added to the session (not yet committed)
            ProcessResult.DUPLICATE — a unique-constraint conflict was detected; caller
                                       should skip committing any related writes for this
                                       trans_id
            ProcessResult.ERROR     — payload was invalid (e.g. missing TransID); caller
                                       should not proceed
        """
        trans_id = str(payload.get("TransID", ""))
        if not trans_id:
            logger.error("mark_processed_in_session() called with missing TransID in payload")
            return ProcessResult.ERROR

        # Pre-flight check using the SAME session/transaction, so it sees any prior
        # writes made earlier in this same transaction. This does not fully close the
        # race window by itself (that's what the unique constraint + flush below is
        # for) — it just avoids doing unnecessary work when we already know it's a dup.
        existing = session.query(ProcessedTransaction).filter(
            ProcessedTransaction.daraja_trans_id == trans_id
        ).first()
        if existing is not None:
            logger.info("Duplicate trans_id=%s detected in pre-flight session check", trans_id)
            return ProcessResult.DUPLICATE

        pt_record = ProcessedTransaction(
            id=f"pt_{uuid.uuid4().hex[:12]}",
            daraja_trans_id=trans_id,
            tenant_id=tenant_id,
            status="received",
            source_ip=source_ip,
            signature_verified=signature_verified,
            webhook_attempt_number=int(payload.get("retry_count", 1)),
        )
        session.add(pt_record)

        t_record = Transaction(
            trans_id=trans_id,
            trans_amount=float(payload.get("TransAmount", 0)),
            msisdn=str(payload.get("MSISDN", "")),
            business_short_code=str(payload.get("BusinessShortCode", "")),
            trans_time=str(payload.get("TransTime", "")),
            raw_payload=payload,
            created_at=datetime.now(timezone.utc),
        )
        session.add(t_record)

        try:
            # Flush (not commit) to surface a unique-constraint violation now, while
            # we can still recover cleanly, rather than at the final commit — this is
            # the hard guarantee against the race the pre-flight check above can't close.
            session.flush()
        except IntegrityError:
            logger.info(
                "Duplicate trans_id=%s caught at flush time (race window closed by "
                "unique constraint)",
                trans_id,
            )
            return ProcessResult.DUPLICATE

        return ProcessResult.STORED

    def update_processing_status(
        self, trans_id: str, status: str, error_reason: str = None, processing_time_ms: int = None
    ) -> None:
        """Update the processing status of a webhook callback.

        Best-effort: failures here are logged but never raised, since this is a
        secondary status update, not the idempotency guarantee itself.
        """
        try:
            self._ensure_ready()
            with self.Session() as session:
                pt_record = session.query(ProcessedTransaction).filter(
                    ProcessedTransaction.daraja_trans_id == str(trans_id)
                ).first()
                if pt_record:
                    pt_record.status = status
                    if error_reason:
                        pt_record.error_reason = error_reason
                    if processing_time_ms is not None:
                        pt_record.processing_time_ms = processing_time_ms
                    session.commit()
                else:
                    logger.warning(
                        "update_processing_status() found no ProcessedTransaction for trans_id=%s",
                        trans_id,
                    )
        except SQLAlchemyError:
            logger.exception("update_processing_status() failed for trans_id=%s", trans_id)

    def write_dead_letter(
        self, payload: dict | None, reason: str, error_detail: str | None = None, tenant_id: str | None = None
    ) -> None:
        """Persist a malformed or rejected webhook payload for later inspection/replay.

        Intentionally best-effort and must not raise in the webhook hot path —
        but genuine failures here are logged, not silently swallowed.
        """
        try:
            from models import DeadLetter

            self._ensure_ready()
            with self.Session() as session:
                dl = DeadLetter(
                    id=f"dl_{uuid.uuid4().hex[:12]}",
                    tenant_id=tenant_id,
                    reason=reason,
                    payload=payload,
                    error_detail=str(error_detail) if error_detail else None,
                    attempts=0,
                    processed=False,
                    processed_at=None,
                )
                session.add(dl)
                session.commit()
        except SQLAlchemyError:
            logger.exception(
                "write_dead_letter() itself failed for reason=%s — payload may be lost, "
                "check DB health.",
                reason,
            )

