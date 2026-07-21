"""A lightweight durable event store for idempotency and replay.

Uses ProcessedTransaction table as the idempotency source of truth.
Each webhook callback from Daraja is recorded exactly once via unique constraint.
"""

import os
import uuid
from datetime import datetime, timezone
from typing import Optional
import time

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from models import Base, Transaction, ProcessedTransaction


class EventStore:
    """Persist processed transactions so duplicate callbacks can be ignored safely.
    
    Uses ProcessedTransaction table as explicit idempotency ledger. This table tracks
    which webhook callbacks (identified by Daraja TransID) have been received and processed.
    The unique constraint on daraja_trans_id ensures database-level idempotency.
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

        # Use serializable isolation to prevent phantom reads during concurrent duplicate detection
        self.engine = create_engine(
            self.database_url,
            isolation_level=self.isolation_level if self.database_url.startswith("postgresql") else None,
        )
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
        self._initialized = True

    def already_processed(self, trans_id: str, source_ip: str = None) -> bool:
        """Check if a webhook callback has already been processed (idempotency gate).
        
        Checks the ProcessedTransaction table using the Daraja TransID as key.
        Conservative: returns True on DB errors to prevent duplicate processing.
        
        Args:
            trans_id: Daraja M-Pesa TransID
            source_ip: Optional IP address of callback source (for audit)
            
        Returns:
            True if this callback has been seen before (idempotent), False if new
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
        except Exception as e:
            # If DB check fails, assume already processed (conservative)
            # to prevent duplicate processing on transient DB errors
            return True

    def mark_processed(self, payload: dict, tenant_id: str = None, source_ip: str = None, signature_verified: bool = False) -> bool:
        """Atomically record that a webhook callback has been processed.
        
        Creates a ProcessedTransaction record with unique constraint on daraja_trans_id.
        Silently ignores duplicates (expected behavior). Records both in ProcessedTransaction
        (idempotency ledger) and Transaction (audit trail).
        
        Args:
            payload: Daraja webhook payload dict
            tenant_id: Optional tenant identifier
            source_ip: Optional IP address of callback source
            signature_verified: Whether HMAC signature was valid
            
        Returns:
            True if successfully recorded, False if duplicate (idempotency catch)
        """
        try:
            self._ensure_ready()
            trans_id = str(payload.get("TransID", ""))
            if not trans_id:
                return False
                
            with self.Session() as session:
                # Record in ProcessedTransaction (idempotency ledger)
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
                
                # Also record in Transaction (audit trail / reconciliation source)
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
                return True
        except Exception as e:
            # Silently ignore: either duplicate (expected) or transient DB error (will retry on next callback)
            # Duplicates expected due to Daraja retries or network issues
            return False

    def update_processing_status(self, trans_id: str, status: str, error_reason: str = None, processing_time_ms: int = None) -> None:
        """Update the processing status of a webhook callback.
        
        Called after successful/failed processing to record the outcome.
        
        Args:
            trans_id: Daraja M-Pesa TransID
            status: New status (validated, stored, failed)
            error_reason: If status=failed, brief reason for failure
            processing_time_ms: Latency from webhook receipt to final store
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
        except Exception:
            # Best-effort status update; don't raise in hot path
            pass

    def write_dead_letter(self, payload: dict | None, reason: str, error_detail: str | None = None, tenant_id: str | None = None) -> None:
        """Persist a malformed or rejected webhook payload to the dead-letter table for later inspection.

        This is intentionally best-effort and must not raise in the webhook hot path.
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
        except Exception:
            # Never raise from the hot path; best-effort logging only
            return
