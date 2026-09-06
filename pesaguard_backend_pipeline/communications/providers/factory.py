from __future__ import annotations

from typing import Any

from .africas_talking import AfricasTalkingProvider


def build_africas_talking_provider(client: Any | None = None) -> AfricasTalkingProvider:
    if client is None:
        from ..africas_talking import AfricasTalkingClient

        client = AfricasTalkingClient()
    return AfricasTalkingProvider(client)
