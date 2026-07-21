"""Load alert templates from alerting/templates/*.md files."""

from __future__ import annotations

import re
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict

from localization_utils import normalise_locale

TEMPLATES_DIR = Path(__file__).resolve().parents[1] / "alerting" / "templates"

DEFAULT_FIELDS_EN: Dict[str, str] = {
    "title": "PesaGuard discrepancy detected",
    "transaction": "Transaction",
    "severity": "Severity",
    "status": "Status",
    "issues": "Issues",
    "no_issues": "No additional details",
    "detected_at": "Detected at",
    "amount": "Amount",
}

DEFAULT_FIELDS_SW: Dict[str, str] = {
    "title": "PesaGuard imegundua tofauti",
    "transaction": "Muamala",
    "severity": "Ukali",
    "status": "Hali",
    "issues": "Mambo yaliyotokea",
    "no_issues": "Hakuna maandishi ya ziada",
    "detected_at": "Iligunduliwa saa",
    "amount": "Kiasi",
}


def _parse_frontmatter(content: str) -> Dict[str, str]:
    match = re.match(r"^---\s*\n(.*?)\n---", content, re.DOTALL)
    if not match:
        return {}

    fields: Dict[str, str] = {}
    for line in match.group(1).splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        fields[key.strip()] = value.strip()
    return fields


def _template_body(content: str) -> str:
    return re.sub(r"^---\s*\n.*?\n---\s*\n?", "", content, count=1, flags=re.DOTALL).strip()


@lru_cache(maxsize=8)
def _read_template_file(name: str) -> str:
    path = TEMPLATES_DIR / name
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def load_alert_fields(locale: str) -> Dict[str, str]:
    locale_code = normalise_locale(locale)
    fallback = DEFAULT_FIELDS_EN if locale_code == "en" else DEFAULT_FIELDS_SW
    filename = f"alert_fields_{locale_code}.md"
    content = _read_template_file(filename)
    if not content:
        return dict(fallback)

    parsed = _parse_frontmatter(content)
    merged = dict(fallback)
    merged.update(parsed)
    return merged


def render_message_template(template_name: str, context: Dict[str, Any]) -> str:
    content = _read_template_file(template_name)
    if not content:
        return ""

    body = _template_body(content)
    rendered = body
    for key, value in context.items():
        rendered = rendered.replace(f"{{{{{key}}}}}", str(value if value is not None else ""))
    return rendered.strip()
