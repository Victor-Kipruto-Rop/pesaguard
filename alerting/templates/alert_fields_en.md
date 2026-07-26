"""
Multi-lingual Alert Localization Module for PesaGuard.

Provides localized field labels and templates for Slack blocks and email notifications
in English (en) and Swahili (sw) in compliance with tenant preferences.
"""

from __future__ import annotations

from typing import Any, Dict

ALERT_LABELS: Dict[str, Dict[str, str]] = {
    "en": {
        "title": "PesaGuard Discrepancy Detected",
        "transaction": "Transaction",
        "severity": "Severity",
        "status": "Status",
        "issues": "Issues",
        "no_issues": "No additional details provided",
        "detected_at": "Detected At",
        "amount": "Amount",
        "tenant": "Tenant",
        "action_required": "Action Required: Review discrepancy dashboard immediately.",
    },
    "sw": {
        "title": "Hitilafu ya PesaGuard Imegunduliwa",
        "transaction": "Muamala",
        "severity": "Kiwango cha Uzito",
        "status": "Hali",
        "issues": "Masuala",
        "no_issues": "Hakuna maelezo ya ziada yaliyotolewa",
        "detected_at": "Imegunduliwa Saa",
        "amount": "Kiasi",
        "tenant": "Mpangaji",
        "action_required": "Hatua Inahitajika: Kagua dashibodi ya hitilafu mara moja.",
    },
}


def get_alert_labels(locale: str = "en") -> Dict[str, str]:
    """Retrieve localized label dictionary for the specified ISO language code.

    Args:
        locale: Language code ('en' or 'sw'). Defaults to 'en'.

    Returns:
        Dictionary of localized string keys.
    """
    norm_locale = locale.lower().strip()
    if norm_locale.startswith("sw"):
        return ALERT_LABELS["sw"]
    return ALERT_LABELS["en"]
