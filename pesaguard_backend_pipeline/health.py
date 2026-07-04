"""Health-check helpers shared by the web services."""

from typing import Any, Dict


def build_health_payload(status: str = "ok") -> Dict[str, Any]:
    return {"status": status, "service": "pesaguard"}
