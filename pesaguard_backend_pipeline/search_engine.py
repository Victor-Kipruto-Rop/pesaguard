"""Advanced search with boolean operators for incident queries."""

import logging
import re
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone, timedelta
from sqlalchemy import or_, and_
from sqlalchemy.orm import Session
from models import Discrepancy

logger = logging.getLogger("pesaguard.search")


class AdvancedSearchEngine:
    """Provides full-text and boolean search capabilities."""

    def __init__(self, session: Session):
        self.session = session

    def search(
        self,
        tenant_id: str,
        query: str,
        limit: int = 50,
        offset: int = 0,
    ) -> Dict[str, Any]:
        """Execute advanced search query with boolean operators."""
        parsed = self._parse_query(query)
        db_query = self.session.query(Discrepancy).filter(
            Discrepancy.tenant_id == tenant_id
        )

        # Apply parsed conditions
        for condition in parsed["conditions"]:
            db_query = self._apply_condition(db_query, condition)

        total = db_query.count()
        results = db_query.offset(offset).limit(limit).all()

        return {
            "query": query,
            "total": total,
            "limit": limit,
            "offset": offset,
            "results": [self._incident_to_dict(r) for r in results],
            "parsed": parsed,
        }

    def _parse_query(self, query: str) -> Dict[str, Any]:
        """Parse boolean query into conditions."""
        conditions = []
        
        # Remove extra whitespace
        query = " ".join(query.split())

        # Split by AND, OR (case insensitive)
        parts = re.split(r"\s+(AND|OR|NOT)\s+", query, flags=re.IGNORECASE)

        operator = "AND"  # default
        i = 0
        while i < len(parts):
            part = parts[i].strip()
            
            if part.upper() in ["AND", "OR", "NOT"]:
                operator = part.upper()
            elif part:
                condition = self._parse_condition(part)
                if condition:
                    condition["operator"] = operator
                    conditions.append(condition)

            i += 1

        return {"query": query, "conditions": conditions}

    def _parse_condition(self, condition_str: str) -> Optional[Dict[str, Any]]:
        """Parse individual condition (e.g., 'severity:critical', 'status:open')."""
        # Format: field:value, field>value, field<value, field~value
        match = re.match(r"(\w+)([:><=~])(.+)", condition_str.strip())
        if not match:
            # Free-text search
            return {
                "type": "text",
                "value": condition_str.strip(),
            }

        field, operator, value = match.groups()
        value = value.strip('"\'')  # Remove quotes

        return {
            "type": "field",
            "field": field.lower(),
            "operator": operator,
            "value": value,
        }

    def _apply_condition(self, query, condition: Dict[str, Any]):
        """Apply a condition to the database query."""
        condition_type = condition.get("type")
        operator = condition.get("operator", "AND")

        if condition_type == "text":
            # Free-text search in multiple fields
            text_value = f"%{condition['value']}%"
            text_query = or_(
                Discrepancy.anomaly_type.ilike(text_value),
                Discrepancy.details.ilike(text_value),
                Discrepancy.notes.ilike(text_value),
            )
            return query.filter(text_query) if operator == "AND" else query.filter(~text_query)

        field = condition.get("field")
        field_value = condition.get("value")
        op = condition.get("operator", ":")

        # Field-specific filtering
        if field == "severity":
            filter_clause = Discrepancy.severity == field_value
        elif field == "status":
            filter_clause = Discrepancy.status == field_value
        elif field == "anomaly_type":
            filter_clause = Discrepancy.anomaly_type == field_value
        elif field == "resolved":
            filter_clause = Discrepancy.resolved == (field_value.lower() == "true")
        elif field == "age":
            # age>30 means older than 30 minutes
            minutes = int(field_value) if field_value.isdigit() else 0
            cutoff = datetime.now(timezone.utc) - timedelta(minutes=minutes)
            if op == ">":
                filter_clause = Discrepancy.detected_at < cutoff
            elif op == "<":
                filter_clause = Discrepancy.detected_at > cutoff
            else:
                filter_clause = True
        elif field == "assignee":
            filter_clause = Discrepancy.assignee == field_value
        elif field == "trans_id":
            filter_clause = Discrepancy.trans_id == field_value
        else:
            return query

        if operator == "NOT":
            return query.filter(~filter_clause)
        else:
            return query.filter(filter_clause)

    def search_by_filters(
        self,
        tenant_id: str,
        severity: str = None,
        status: str = None,
        anomaly_type: str = None,
        resolved: bool = None,
        assignee: str = None,
        days_back: int = 30,
        limit: int = 50,
        offset: int = 0,
    ) -> Dict[str, Any]:
        """Search using structured filters."""
        query = self.session.query(Discrepancy).filter(
            Discrepancy.tenant_id == tenant_id
        )

        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days_back)
        query = query.filter(Discrepancy.detected_at >= cutoff_date)

        if severity:
            query = query.filter(Discrepancy.severity == severity)
        if status:
            query = query.filter(Discrepancy.status == status)
        if anomaly_type:
            query = query.filter(Discrepancy.anomaly_type == anomaly_type)
        if resolved is not None:
            query = query.filter(Discrepancy.resolved == resolved)
        if assignee:
            query = query.filter(Discrepancy.assignee == assignee)

        total = query.count()
        results = query.offset(offset).limit(limit).all()

        return {
            "total": total,
            "limit": limit,
            "offset": offset,
            "filters": {
                "severity": severity,
                "status": status,
                "anomaly_type": anomaly_type,
                "resolved": resolved,
                "assignee": assignee,
                "days_back": days_back,
            },
            "results": [self._incident_to_dict(r) for r in results],
        }

    def suggest_filters(self, tenant_id: str) -> Dict[str, List[str]]:
        """Get available filter values for a tenant."""
        incidents = (
            self.session.query(Discrepancy)
            .filter(Discrepancy.tenant_id == tenant_id)
            .all()
        )

        severities = set()
        statuses = set()
        anomaly_types = set()
        assignees = set()

        for incident in incidents:
            if incident.severity:
                severities.add(incident.severity)
            if incident.status:
                statuses.add(incident.status)
            if incident.anomaly_type:
                anomaly_types.add(incident.anomaly_type)
            if incident.assignee:
                assignees.add(incident.assignee)

        return {
            "severities": sorted(list(severities)),
            "statuses": sorted(list(statuses)),
            "anomaly_types": sorted(list(anomaly_types)),
            "assignees": sorted(list(assignees)),
        }

    def save_search_preset(
        self,
        tenant_id: str,
        preset_name: str,
        query: str,
    ) -> Dict[str, Any]:
        """Save a search query as a reusable preset."""
        # This would typically be saved to a SearchPreset table
        return {
            "preset_id": f"preset_{tenant_id}_{preset_name}",
            "name": preset_name,
            "query": query,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

    def _incident_to_dict(self, incident: Discrepancy) -> Dict[str, Any]:
        """Convert incident to dictionary."""
        return {
            "id": incident.id,
            "trans_id": incident.trans_id,
            "anomaly_type": incident.anomaly_type,
            "severity": incident.severity,
            "status": incident.status,
            "resolved": incident.resolved,
            "assignee": incident.assignee,
            "detected_at": incident.detected_at.isoformat() if incident.detected_at else None,
            "resolved_at": incident.resolved_at.isoformat() if incident.resolved_at else None,
            "details": incident.details,
        }
