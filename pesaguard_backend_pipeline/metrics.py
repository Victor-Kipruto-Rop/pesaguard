from typing import Any, Dict


def build_metrics_payload() -> str:
    lines = [
        "# HELP pesaguard_transactions_total Total transactions seen by PesaGuard",
        "# TYPE pesaguard_transactions_total counter",
        "pesaguard_transactions_total 128",
        "# HELP pesaguard_alerts_total Total alerts emitted",
        "# TYPE pesaguard_alerts_total counter",
        "pesaguard_alerts_total 3",
        "# HELP pesaguard_open_discrepancies Current unresolved discrepancies",
        "# TYPE pesaguard_open_discrepancies gauge",
        "pesaguard_open_discrepancies 2",
    ]
    return "\n".join(lines) + "\n"
