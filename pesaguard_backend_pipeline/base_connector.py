"""
Base interface for internal ledger/order connectors.

Each pilot customer's internal system differs (Postgres DB, Google Sheet,
custom REST API, etc). Implement one subclass per customer/integration type.
"""
import json
import logging
import os
import re
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, Optional

import requests
from sqlalchemy import create_engine, text

logger = logging.getLogger("pesaguard.connectors")

# Identifiers (table/column names) must match this pattern. This is a
# defense-in-depth measure: these values come from environment config today,
# not directly from a web request, but they're built into SQL via string
# interpolation (table/column names can't be bound as normal query
# parameters), and this codebase already has a pattern (TenantSettingsStore)
# for making similar config tenant-configurable later — if that ever
# extends to these values, an allowlist here is what stands between that and
# SQL injection.
_SAFE_IDENTIFIER = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def _validate_identifier(name: str, kind: str) -> str:
    if not _SAFE_IDENTIFIER.match(name):
        raise ValueError(
            f"Unsafe {kind} name rejected: {name!r}. Only letters, digits, "
            f"and underscores are allowed, and it must not start with a digit."
        )
    return name


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


# Default field mapping shared by connectors that map from column names.
_DEFAULT_MAPPING = {
    "internal_ref": "internal_ref",
    "amount": "amount",
    "phone_number": "phone_number",
    "timestamp": "created_at",
    "status": "status",
}


def _merge_mapping(defaults: Dict[str, str], override: Optional[Dict[str, str]]) -> Dict[str, str]:
    """Merge a partial custom mapping over defaults, key by key.

    FIXED: previously `mapping or defaults` replaced the ENTIRE default dict
    the moment any custom mapping was supplied — so a customer config that
    only overrode one field (e.g. just "amount") silently ended up missing
    the other four expected keys, raising KeyError at query time instead of
    at startup with a clear error.
    """
    merged = dict(defaults)
    if override:
        merged.update(override)
    return merged


class PostgresConnector(BaseConnector):
    """Connector for pilot customers whose orders live in Postgres."""

    def __init__(self, connection_string: str, table_name: str = "orders", mapping: Optional[Dict[str, str]] = None):
        self.connection_string = connection_string
        self.table_name = table_name
        self.mapping = _merge_mapping(_DEFAULT_MAPPING, mapping)
        self._engine = None  # created lazily, reused — see _get_engine

    def _get_engine(self):
        """Reuse one engine/connection pool for the lifetime of this connector
        instance, instead of creating a new one on every call.

        FIXED: previously create_engine(self.connection_string) was called
        fresh inside fetch_recent_records() — and reconciliation_job.py calls
        fetch_recent_records() inside the per-message consumer loop, i.e. once
        per incoming M-Pesa transaction. At any real transaction volume this
        leaked a new connection pool per transaction, which would exhaust
        Postgres's connection limit far faster than the equivalent leak found
        in health.py's database check (that one was tied to a monitoring
        polling interval; this one is tied to transaction throughput).
        """
        if self._engine is None:
            self._engine = create_engine(self.connection_string, pool_pre_ping=True, pool_size=3, max_overflow=2)
        return self._engine

    def fetch_recent_records(self, since_minutes: int = 15):
        if not self.connection_string:
            logger.warning("Postgres connector missing connection string")
            return []

        try:
            safe_table = _validate_identifier(self.table_name, "table")
            safe_columns = {k: _validate_identifier(v, "column") for k, v in self.mapping.items()}
        except ValueError:
            logger.exception("Rejecting fetch_recent_records due to unsafe configured identifier")
            return []

        engine = self._get_engine()
        since = datetime.now(timezone.utc).timestamp() - (since_minutes * 60)
        query = text(
            f"SELECT {safe_columns['internal_ref']}, {safe_columns['amount']}, {safe_columns['phone_number']}, "
            f"{safe_columns['timestamp']}, {safe_columns['status']} "
            f"FROM {safe_table} WHERE {safe_columns['timestamp']} >= :since"
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
    """Connector for customers tracking orders in Google Sheets.

    NOT YET IMPLEMENTED. See fetch_recent_records below — this now fails
    loudly rather than silently returning an empty list.
    """

    def __init__(self, sheet_id: str, worksheet_name: str = "Orders", credentials_json: Optional[str] = None):
        self.sheet_id = sheet_id
        self.worksheet_name = worksheet_name
        self.credentials_json = credentials_json

    def fetch_recent_records(self, since_minutes: int = 15):
        # FIXED: this previously logged an INFO message that sounded like
        # real work was happening ("polling ... with backoff strategy") and
        # returned an empty list — indistinguishable from "there genuinely
        # are no matching internal records right now." If any pilot customer
        # were ever configured with CONNECTOR_TYPE=google_sheets, EVERY
        # transaction would be evaluated against zero internal records
        # forever, meaning every single transaction gets permanently flagged
        # as missing_payment/critical — a silent, total reconciliation
        # failure for that customer, with logs that look completely normal.
        #
        # Now: raises NotImplementedError, matching the abstract base's
        # contract, so this failure is loud and immediate (at connector
        # selection / first use) instead of silently corrupting every
        # subsequent reconciliation decision.
        logger.error(
            "GoogleSheetsConnector.fetch_recent_records() called for sheet_id=%s "
            "but this connector is not yet implemented. Refusing to silently "
            "return an empty result, which would make every transaction look "
            "like a missing_payment discrepancy.",
            self.sheet_id,
        )
        raise NotImplementedError(
            "GoogleSheetsConnector is not yet implemented. Do not select "
            "CONNECTOR_TYPE=google_sheets until this is built — doing so "
            "would silently flag every transaction as missing_payment."
        )


class RestConnector(BaseConnector):
    """Connector for generic REST-based internal ledgers."""

    def __init__(self, endpoint: str, auth_type: str = "api_key", auth_value: str = "", mapping: Optional[Dict[str, str]] = None):
        self.endpoint = endpoint
        self.auth_type = auth_type
        self.auth_value = auth_value
        self.mapping = _merge_mapping(
            {"internal_ref": "id", "amount": "amount", "phone_number": "phone", "timestamp": "created_at", "status": "status"},
            mapping,
        )

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
    """Loads the preferred connector for each tenant from environment config.

    NOTE: from_env() currently builds exactly ONE connector, keyed to the
    single process-wide TENANT_ID env var — so despite get_connector(tenant_id)
    taking a parameter, this is not yet genuinely multi-tenant. That's
    consistent with the current single-pilot-customer deployment stage
    (multi-tenant infrastructure was explicitly deferred), so this is left
    as-is rather than built out ahead of a second paying customer — but it
    will need real per-tenant connector configuration (e.g. reading from
    TenantSettingsStore per tenant_id rather than a single global env var)
    once that becomes real.
    """

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
