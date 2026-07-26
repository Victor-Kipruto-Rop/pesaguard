"""A lightweight durable event store for idempotency and replay.

Uses ProcessedTransaction table as the idempotency source of truth.
Each webhook callback from Daraja is recorded exactly once via unique constraint.
"""

from __future__ import annotations

import logging
import os
import threading
import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Optional

from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

from models import Base, ProcessedTransaction, Transaction

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
        self.isolation_level = isolation_level
        self.engine = None
        self.Session = None
        self._initialized = False
        self._init_lock = threading.Lock()

    def _ensure_ready(self) -> None:
        """Thread-safe lazy initialization of the database engine and session factory."""
        if self._initialized:
            return

        with self._init_lock:
            if self._initialized:
                return

            connect_args = {}
            if "postgresql" in self.database_url:
                connect_args["connect_timeout"] = int(os.getenv("DB_CONNECT_TIMEOUT", "5"))

            self.engine = create_engine(
                self.database_url,
                pool_pre_ping=True,
                pool_size=int(os.getenv("DB_POOL_SIZE", "10")),
                max_overflow=int(os.getenv("DB_MAX_OVERFLOW", "20")),
                isolation_level=self.isolation_level if "postgresql" in self.database_url else None,
                connect_args=connect_args,
            )
            Base.metadata.create_all(self.engine)
            self.Session = sessionmaker(bind=self.engine, expire_on_commit=False)
            self._initialized = True

    def already_processed(self, trans_id: str, source_ip: Optional[str] = None) -> bool:
        """Check if a webhook callback has already been processed (idempotency gate).

        This is an optimization only — the real guarantee is the unique constraint
        enforced in mark_processed(). Conservative: returns True on DB errors, so a
        transient read failure doesn't cause reprocessing.

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
        payload: Dict[str, Any],
        tenant_id: Optional[str] = None,
        source_ip: Optional[str] = None,
        signature_verified: bool = False,
    ) -> ProcessResult:
        """Atomically record that a webhook callback has been processed.

        Creates a ProcessedTransaction record with a unique constraint on
        daraja_trans_id. Distinguishes an expected duplicate (unique constraint
        violation) from a genuine error (connection failure, etc.) — callers must
        NOT treat these the same way.

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
        trans_id = str(payload.get("TransID", "")).strip()
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
                    tenant_id=tenant_id or "default",
                    status="received",
                    source_ip=source_ip,
                    signature_verified=signature_verified,
                    webhook_attempt_number=int(payload.get("retry_count", 1)),
                    created_at=datetime.now(timezone.utc),
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
            logger.info("Duplicate webhook callback ignored for trans_id=%s (unique constraint)", trans_id)
            return ProcessResult.DUPLICATE

        except SQLAlchemyError:
            logger.exception(
                "mark_processed() failed for trans_id=%s due to a DB error, not a "
                "duplicate — this transaction was NOT stored and needs retry/investigation.",
                trans_id,
            )
            return ProcessResult.ERROR

    def mark_processed_in_session(
        self,
        session: Session,
        payload: Dict[str, Any],
        tenant_id: Optional[str] = None,
        source_ip: Optional[str] = None,
        signature_verified: bool = False,
    ) -> ProcessResult:
        """Same as mark_processed(), but writes using a caller-provided session and
        uses savepoints (begin_nested) to isolate flush errors without invalidating
        the caller's transaction.

        Returns:
            ProcessResult.STORED    — rows added to the session (not yet committed)
            ProcessResult.DUPLICATE — a unique-constraint conflict was detected
            ProcessResult.ERROR     — payload was invalid or unrecoverable error occurred
        """
        trans_id = str(payload.get("TransID", "")).strip()
        if not trans_id:
            logger.error("mark_processed_in_session() called with missing TransID in payload")
            return ProcessResult.ERROR

        existing = session.query(ProcessedTransaction).filter(
            ProcessedTransaction.daraja_trans_id == trans_id
        ).first()
        if existing is not None:
            logger.info("Duplicate trans_id=%s detected in pre-flight session check", trans_id)
            return ProcessResult.DUPLICATE

        try:
            # Create a savepoint to catch duplicate constraints without breaking the parent transaction
            savepoint = session.begin_nested()

            pt_record = ProcessedTransaction(
                id=f"pt_{uuid.uuid4().hex[:12]}",
                daraja_trans_id=trans_id,
                tenant_id=tenant_id or "default",
                status="received",
                source_ip=source_ip,
                signature_verified=signature_verified,
                webhook_attempt_number=int(payload.get("retry_count", 1)),
                created_at=datetime.now(timezone.utc),
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

            session.flush()
            return ProcessResult.STORED

        except IntegrityError:
            savepoint.rollback()
            logger.info(
                "Duplicate trans_id=%s caught at flush time (race window closed by unique constraint)",
                trans_id,
            )
            return ProcessResult.DUPLICATE
        except SQLAlchemyError:
            savepoint.rollback()
            logger.exception("mark_processed_in_session() encountered database error for trans_id=%s", trans_id)
            return ProcessResult.ERROR

    def update_processing_status(
        self,
        trans_id: str,
        status: str,
        error_reason: Optional[str] = None,
        processing_time_ms: Optional[int] = None,
    ) -> None:
        """Update the processing status of a webhook callback."""
        if not trans_id:
            return

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
                    logger.warning("update_processing_status() found no ProcessedTransaction for trans_id=%s", trans_id)
        except SQLAlchemyError:
            logger.exception("update_processing_status() failed for trans_id=%s", trans_id)

    def write_dead_letter(
        self,
        payload: Optional[Dict[str, Any]],
        reason: str,
        error_detail: Optional[str] = None,
        tenant_id: Optional[str] = None,
    ) -> None:
        """Persist a malformed or rejected webhook payload for later inspection and replay."""
        try:
            from models import DeadLetter

            self._ensure_ready()
            with self.Session() as session:
                dl = DeadLetter(
                    id=f"dl_{uuid.uuid4().hex[:12]}",
                    tenant_id=tenant_id or "default",
                    reason=reason,
                    payload=payload or {},
                    error_detail=str(error_detail) if error_detail else None,
                    attempts=0,
                    processed=False,
                    processed_at=None,
                    created_at=datetime.now(timezone.utc),
                )
                session.add(dl)
                session.commit()
                logger.info("Recorded dead-letter entry id=%s reason=%s", dl.id, reason)
        except SQLAlchemyError:
            logger.exception(
                "write_dead_letter() failed for reason=%s — payload could not be persisted.",
                reason,
            )


# Default singleton instance
event_store = EventStore()
