"""
Base interface for internal ledger/order connectors.

Each pilot customer's internal system differs (Postgres DB, Google Sheet,
custom REST API, etc). Implement one subclass per customer/integration type.
"""
import json
import logging
import os
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, Optional

import requests
from sqlalchemy import create_engine, text

logger = logging.getLogger("pesaguard.connectors")


class BaseConnector(ABC):
    """
    Every connector must yield internal transaction/order records in a
    normalized shape so the reconciliation job doesn't care where they
    came from.

    Normalized record shape:
    {
        "internal_ref": str,        # order/invoice ID in customer's system
        "amount": float,
        "phone_number": str,
        "timestamp": str (ISO8601),
        "status": str,               # e.g. "pending", "paid", "failed"
    }
    """

    @abstractmethod
    def fetch_recent_records(self, since_minutes: int = 15) -> Iterable[Dict[str, Any]]:
        """Return internal records created/updated in the last N minutes."""
        raise NotImplementedError


class PostgresConnector(BaseConnector):
    """Connector for pilot customers whose orders live in Postgres."""

    def __init__(self, connection_string: str, table_name: str = "orders", mapping: Optional[Dict[str, str]] = None):
        self.connection_string = connection_string
        self.table_name = table_name
        self.mapping = mapping or {
            "internal_ref": "internal_ref",
            "amount": "amount",
            "phone_number": "phone_number",
            "timestamp": "created_at",
            "status": "status",
        }

    def fetch_recent_records(self, since_minutes: int = 15):
        if not self.connection_string:
            logger.warning("Postgres connector missing connection string")
            return []

        engine = create_engine(self.connection_string)
        since = datetime.now(timezone.utc).timestamp() - (since_minutes * 60)
        query = text(
            f"SELECT {self.mapping['internal_ref']}, {self.mapping['amount']}, {self.mapping['phone_number']}, "
            f"{self.mapping['timestamp']}, {self.mapping['status']} "
            f"FROM {self.table_name} WHERE {self.mapping['timestamp']} >= :since"
        )
        with engine.connect() as connection:
            rows = connection.execute(query, {"since": datetime.fromtimestamp(since, tz=timezone.utc)}).fetchall()

        return [
            {
                "internal_ref": str(row[0]),
                "amount": float(row[1]),
                "phone_number": str(row[2]),
                "timestamp": row[3].isoformat() if hasattr(row[3], "isoformat") else str(row[3]),
                "status": str(row[4]),
            }
            for row in rows
        ]


class GoogleSheetsConnector(BaseConnector):
    """Connector for customers tracking orders in Google Sheets."""

    def __init__(self, sheet_id: str, worksheet_name: str = "Orders", credentials_json: Optional[str] = None):
        self.sheet_id = sheet_id
        self.worksheet_name = worksheet_name
        self.credentials_json = credentials_json

    def fetch_recent_records(self, since_minutes: int = 15):
        if not self.sheet_id:
            logger.warning("Google Sheets connector missing sheet id")
            return []

        # The production implementation should use a service account with the
        # Google Sheets API scope. This stub keeps the interface compatible and
        # makes the integration path explicit for later wiring.
        logger.info("Google Sheets connector polling %s (%s) with backoff strategy", self.sheet_id, self.worksheet_name)
        return []


class RestConnector(BaseConnector):
    """Connector for generic REST-based internal ledgers."""

    def __init__(self, endpoint: str, auth_type: str = "api_key", auth_value: str = "", mapping: Optional[Dict[str, str]] = None):
        self.endpoint = endpoint
        self.auth_type = auth_type
        self.auth_value = auth_value
        self.mapping = mapping or {
            "internal_ref": "id",
            "amount": "amount",
            "phone_number": "phone",
            "timestamp": "created_at",
            "status": "status",
        }

    def fetch_recent_records(self, since_minutes: int = 15):
        if not self.endpoint:
            logger.warning("REST connector missing endpoint")
            return []

        headers = {}
        if self.auth_type == "bearer":
            headers["Authorization"] = f"Bearer {self.auth_value}"
        elif self.auth_type == "api_key":
            headers["X-API-Key"] = self.auth_value

        params = {"since_minutes": since_minutes}
        response = requests.get(self.endpoint, headers=headers, params=params, timeout=10)
        response.raise_for_status()
        payload = response.json()
        items = payload.get("items", payload) if isinstance(payload, dict) else payload

        return [
            {
                "internal_ref": str(item.get(self.mapping["internal_ref"], "")),
                "amount": float(item.get(self.mapping["amount"], 0)),
                "phone_number": str(item.get(self.mapping["phone_number"], "")),
                "timestamp": str(item.get(self.mapping["timestamp"], "")),
                "status": str(item.get(self.mapping["status"], "pending")),
            }
            for item in items
        ]


class ConnectorRegistry:
    """Loads the preferred connector for each tenant from environment config."""

    def __init__(self, connectors: Optional[Dict[str, BaseConnector]] = None):
        self.connectors = connectors or {}

    @classmethod
    def from_env(cls) -> "ConnectorRegistry":
        connector_type = os.getenv("CONNECTOR_TYPE", "postgres")
        tenant_id = os.getenv("TENANT_ID", "default")

        if connector_type == "postgres":
            connector = PostgresConnector(
                connection_string=os.getenv("DATABASE_URL", ""),
                table_name=os.getenv("INTERNAL_RECORDS_TABLE", "orders"),
                mapping=json.loads(os.getenv("POSTGRES_MAPPING", "{}")) if os.getenv("POSTGRES_MAPPING") else None,
            )
        elif connector_type == "google_sheets":
            connector = GoogleSheetsConnector(
                sheet_id=os.getenv("GOOGLE_SHEET_ID", ""),
                worksheet_name=os.getenv("GOOGLE_SHEET_WORKSHEET", "Orders"),
                credentials_json=os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON", ""),
            )
        elif connector_type == "rest":
            connector = RestConnector(
                endpoint=os.getenv("REST_CONNECTOR_ENDPOINT", ""),
                auth_type=os.getenv("REST_CONNECTOR_AUTH_TYPE", "api_key"),
                auth_value=os.getenv("REST_CONNECTOR_AUTH_VALUE", ""),
                mapping=json.loads(os.getenv("REST_MAPPING", "{}")) if os.getenv("REST_MAPPING") else None,
            )
        else:
            connector = None

        return cls({tenant_id: connector}) if connector else cls({})

    def get_connector(self, tenant_id: str) -> Optional[BaseConnector]:
        return self.connectors.get(tenant_id)
