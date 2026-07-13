from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any
from zoneinfo import ZoneInfo

_MISSING = object()
_EAT = ZoneInfo("Africa/Nairobi")


def _resolve_path(locale_data: dict[str, Any], key: str, *, allow_camel_case: bool = False) -> Any:
    current: Any = locale_data
    parts = key.split('.')

    for index, part in enumerate(parts):
        if not isinstance(current, dict):
            return _MISSING

        if part in current:
            current = current[part]
            continue

        if allow_camel_case and index < len(parts) - 1:
            combined = part + ''.join(segment[:1].upper() + segment[1:] for segment in parts[index + 1 :])
            if combined in current:
                return current[combined]

        return _MISSING

    return current


def resolve_translation(locale_data: dict[str, Any], key: str, fallback_locale: dict[str, Any] | None = None) -> Any:
    """Resolve a translation key, falling back to English when missing."""
    value = _resolve_path(locale_data, key)
    if value is not _MISSING:
        return value

    if fallback_locale is None or fallback_locale is locale_data:
        return key

    fallback_value = _resolve_path(fallback_locale, key, allow_camel_case=True)
    if fallback_value is not _MISSING:
        return fallback_value

    return key


def normalise_locale(locale: str | None) -> str:
    if not locale:
        return "en"
    value = str(locale).strip().lower()
    return "sw" if value.startswith("sw") else "en"


def format_ke_currency(amount: Any) -> str:
    try:
        value = Decimal(str(amount))
    except (ArithmeticError, TypeError, ValueError):
        return str(amount)
    return f"KES {value:,.2f}"


def format_ke_datetime(value: Any) -> str:
    if isinstance(value, datetime):
        dt = value
    else:
        text = str(value).strip()
        if not text:
            return ""
        if text.endswith("Z"):
            text = text[:-1] + "+00:00"
        try:
            dt = datetime.fromisoformat(text)
        except ValueError:
            return text

    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=ZoneInfo("UTC"))

    local_dt = dt.astimezone(_EAT)
    return local_dt.strftime("%d %b %Y, %H:%M EAT")
