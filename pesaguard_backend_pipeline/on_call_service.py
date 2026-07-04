"""On-call rotation tracking and management."""

import logging
import uuid
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session
from models import OnCallRotation

logger = logging.getLogger("pesaguard.on_call")


class OnCallService:
    """Manages operator on-call rotations."""

    def __init__(self, session: Session):
        self.session = session

    def create_rotation(
        self,
        tenant_id: str,
        operator_id: str,
        operator_name: str,
        operator_email: str,
        operator_phone: str,
        shift_start: datetime,
        shift_end: datetime,
        escalation_level: int = 1,
    ) -> Dict[str, Any]:
        """Create a new on-call rotation."""
        rotation_id = f"rotation_{uuid.uuid4().hex[:12]}"
        
        # Auto-activate if shift has started
        now = datetime.now(timezone.utc)
        is_active = shift_start <= now < shift_end

        rotation = OnCallRotation(
            id=rotation_id,
            tenant_id=tenant_id,
            operator_id=operator_id,
            operator_name=operator_name,
            operator_email=operator_email,
            operator_phone=operator_phone,
            shift_start=shift_start,
            shift_end=shift_end,
            is_active=is_active,
            escalation_level=escalation_level,
        )
        self.session.add(rotation)
        self.session.commit()
        logger.info(f"Created rotation {rotation_id} for {operator_id}")
        return self._rotation_to_dict(rotation)

    def get_active_rotations(
        self,
        tenant_id: str,
        escalation_level: int = None,
    ) -> List[Dict[str, Any]]:
        """Get active on-call rotations for a tenant."""
        now = datetime.now(timezone.utc)
        query = (
            self.session.query(OnCallRotation)
            .filter(
                OnCallRotation.tenant_id == tenant_id,
                OnCallRotation.shift_start <= now,
                OnCallRotation.shift_end > now,
            )
        )
        if escalation_level:
            query = query.filter(
                OnCallRotation.escalation_level == escalation_level
            )
        rotations = query.order_by(OnCallRotation.escalation_level).all()
        return [self._rotation_to_dict(r) for r in rotations]

    def get_upcoming_rotations(
        self,
        tenant_id: str,
        hours_ahead: int = 24,
    ) -> List[Dict[str, Any]]:
        """Get upcoming on-call rotations."""
        now = datetime.now(timezone.utc)
        future = now + timedelta(hours=hours_ahead)
        rotations = (
            self.session.query(OnCallRotation)
            .filter(
                OnCallRotation.tenant_id == tenant_id,
                OnCallRotation.shift_start > now,
                OnCallRotation.shift_start <= future,
            )
            .order_by(OnCallRotation.shift_start)
            .all()
        )
        return [self._rotation_to_dict(r) for r in rotations]

    def get_rotation_history(
        self,
        tenant_id: str,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """Get past on-call rotations."""
        now = datetime.now(timezone.utc)
        rotations = (
            self.session.query(OnCallRotation)
            .filter(
                OnCallRotation.tenant_id == tenant_id,
                OnCallRotation.shift_end <= now,
            )
            .order_by(OnCallRotation.shift_end.desc())
            .limit(limit)
            .all()
        )
        return [self._rotation_to_dict(r) for r in rotations]

    def get_operator_schedule(
        self,
        tenant_id: str,
        operator_id: str,
        days_ahead: int = 30,
    ) -> List[Dict[str, Any]]:
        """Get operator's on-call schedule."""
        now = datetime.now(timezone.utc)
        future = now + timedelta(days=days_ahead)
        rotations = (
            self.session.query(OnCallRotation)
            .filter(
                OnCallRotation.tenant_id == tenant_id,
                OnCallRotation.operator_id == operator_id,
                OnCallRotation.shift_start >= now,
                OnCallRotation.shift_start <= future,
            )
            .order_by(OnCallRotation.shift_start)
            .all()
        )
        return [self._rotation_to_dict(r) for r in rotations]

    def update_rotation(self, rotation_id: str, **kwargs) -> Dict[str, Any]:
        """Update a rotation."""
        rotation = (
            self.session.query(OnCallRotation)
            .filter(OnCallRotation.id == rotation_id)
            .first()
        )
        if not rotation:
            return {"error": "rotation_not_found"}

        # Check if shift should be active
        now = datetime.now(timezone.utc)
        if "shift_start" in kwargs or "shift_end" in kwargs:
            shift_start = kwargs.get("shift_start", rotation.shift_start)
            shift_end = kwargs.get("shift_end", rotation.shift_end)
            kwargs["is_active"] = shift_start <= now < shift_end

        for key, value in kwargs.items():
            if hasattr(rotation, key):
                setattr(rotation, key, value)

        self.session.commit()
        logger.info(f"Updated rotation {rotation_id}")
        return self._rotation_to_dict(rotation)

    def delete_rotation(self, rotation_id: str) -> Dict[str, Any]:
        """Delete a rotation."""
        rotation = (
            self.session.query(OnCallRotation)
            .filter(OnCallRotation.id == rotation_id)
            .first()
        )
        if not rotation:
            return {"error": "rotation_not_found"}

        self.session.delete(rotation)
        self.session.commit()
        logger.info(f"Deleted rotation {rotation_id}")
        return {"status": "deleted"}

    def get_coverage_status(self, tenant_id: str) -> Dict[str, Any]:
        """Get on-call coverage status for tenant."""
        active_rotations = self.get_active_rotations(tenant_id)
        upcoming_rotations = self.get_upcoming_rotations(tenant_id, hours_ahead=4)

        coverage_by_level = {}
        for rotation in active_rotations:
            level = rotation["escalation_level"]
            if level not in coverage_by_level:
                coverage_by_level[level] = []
            coverage_by_level[level].append(rotation)

        return {
            "tenant_id": tenant_id,
            "currently_covered": len(active_rotations) > 0,
            "active_operators": len(active_rotations),
            "coverage_by_level": coverage_by_level,
            "upcoming_shifts": len(upcoming_rotations),
            "next_shift": (
                upcoming_rotations[0] if upcoming_rotations else None
            ),
        }

    def bulk_create_rotations(
        self,
        tenant_id: str,
        rotations_data: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Bulk create multiple rotations."""
        created = []
        errors = []

        for data in rotations_data:
            try:
                shift_start = datetime.fromisoformat(data["shift_start"])
                shift_end = datetime.fromisoformat(data["shift_end"])
                
                result = self.create_rotation(
                    tenant_id=tenant_id,
                    operator_id=data["operator_id"],
                    operator_name=data.get("operator_name", ""),
                    operator_email=data.get("operator_email", ""),
                    operator_phone=data.get("operator_phone", ""),
                    shift_start=shift_start,
                    shift_end=shift_end,
                    escalation_level=data.get("escalation_level", 1),
                )
                created.append(result)
            except Exception as e:
                errors.append({"data": data, "error": str(e)})

        return {
            "created": len(created),
            "errors": len(errors),
            "rotations": created,
            "failed": errors,
        }

    def _rotation_to_dict(self, rotation: OnCallRotation) -> Dict[str, Any]:
        """Convert rotation object to dictionary."""
        return {
            "id": rotation.id,
            "tenant_id": rotation.tenant_id,
            "operator_id": rotation.operator_id,
            "operator_name": rotation.operator_name,
            "operator_email": rotation.operator_email,
            "operator_phone": rotation.operator_phone,
            "shift_start": rotation.shift_start.isoformat(),
            "shift_end": rotation.shift_end.isoformat(),
            "is_active": rotation.is_active,
            "escalation_level": rotation.escalation_level,
            "created_at": rotation.created_at.isoformat(),
        }
