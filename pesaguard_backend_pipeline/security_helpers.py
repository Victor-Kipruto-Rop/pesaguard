import ipaddress
import os
from flask import Request


def get_client_ip(request: Request) -> str:
    """Get the client IP from the incoming request.

    Supports X-Forwarded-For if the request is behind a proxy.
    """
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        client_ip = forwarded_for.split(",")[0].strip()
    else:
        client_ip = request.remote_addr or ""
    return client_ip


def _parse_allowed_ips() -> list[str]:
    raw = os.getenv("DARAJA_ALLOWED_IPS", "")
    if not raw:
        return []
    return [ip.strip() for ip in raw.split(",") if ip.strip()]


def is_payload_within_limit(request: Request) -> bool:
    """Guard against large requests before application logic runs."""
    max_body_bytes = int(
        os.getenv("PESAGUARD_API_MAX_BODY_BYTES", os.getenv("PESAGUARD_WEBHOOK_MAX_BODY_BYTES", "1048576"))
    )
    content_length = request.content_length
    if content_length is not None:
        return content_length <= max_body_bytes

    body = request.get_data(cache=False, as_text=False)
    return len(body or b"") <= max_body_bytes


def is_allowed_source(client_ip: str, request: Request) -> bool:
    """Validate the incoming webhook source using shared secret and IP allowlist."""
    shared_secret = os.getenv("DARAJA_SHARED_SECRET")
    configured_ips = _parse_allowed_ips()
    if shared_secret:
        header_secret = request.headers.get("X-Daraja-Shared-Secret", "")
        if header_secret != shared_secret:
            return False

    if configured_ips:
        try:
            parsed_ip = ipaddress.ip_address(client_ip)
        except ValueError:
            return False

        for allowed in configured_ips:
            try:
                if parsed_ip == ipaddress.ip_address(allowed):
                    return True
                if "/" in allowed:
                    network = ipaddress.ip_network(allowed, strict=False)
                    if parsed_ip in network:
                        return True
            except ValueError:
                continue
        return False

    return True


def sanitize_error_message(error: object) -> str:
    """Return a generic client-safe error message for external responses."""
    return "Invalid request"
