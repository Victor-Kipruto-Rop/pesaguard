import hmac
import ipaddress
import logging
import os
from flask import Request

logger = logging.getLogger("pesaguard.security_helpers")


def get_client_ip(request: Request) -> str:
    """Get the client IP from the incoming request.

    FIXED: previously trusted X-Forwarded-For unconditionally — any client
    can set that header themselves, so an attacker could spoof a value like
    "X-Forwarded-For: <an allowlisted Safaricom IP>" and have this function
    report that spoofed IP as "the client," completely defeating the IP
    allowlist in is_allowed_source() below.

    Now: X-Forwarded-For is only trusted if PESAGUARD_TRUSTED_PROXY_COUNT is
    explicitly set to a positive integer, matching the number of trusted
    reverse proxies actually in front of this app (e.g. 1 if there's exactly
    one load balancer that appends to the header before forwarding). In that
    case, the trustworthy client IP is the Nth-from-the-right entry (the
    proxy closest to the app appends last, so entries further left could
    still be attacker-supplied if the attacker also sets the header). If
    PESAGUARD_TRUSTED_PROXY_COUNT is unset or 0 (the safe default), X-Forwarded-For
    is ignored entirely and only the direct TCP peer (request.remote_addr) is used.
    """
    trusted_proxy_count = int(os.getenv("PESAGUARD_TRUSTED_PROXY_COUNT", "0"))

    if trusted_proxy_count > 0:
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            hops = [h.strip() for h in forwarded_for.split(",") if h.strip()]
            # The rightmost `trusted_proxy_count` entries were appended by
            # proxies we trust; the one just before them is the real client.
            # If there aren't enough hops, fall back to remote_addr rather
            # than guessing.
            if len(hops) >= trusted_proxy_count:
                index = len(hops) - trusted_proxy_count
                if index > 0:
                    return hops[index - 1]

    return request.remote_addr or ""


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
    """Validate the incoming webhook source using shared secret and IP allowlist.

    FIXED: previously returned True (allow) whenever neither
    DARAJA_SHARED_SECRET nor DARAJA_ALLOWED_IPS was configured — an
    unconfigured security control silently allowed every source through, with
    no validation at all. For a webhook that triggers real financial
    reconciliation, an unconfigured check should fail closed, not open.

    Now: if neither mechanism is configured, the request is REJECTED, and a
    loud warning is logged so misconfiguration is visible immediately rather
    than discovered later. Set PESAGUARD_ALLOW_UNRESTRICTED_WEBHOOK_SOURCE=1
    to explicitly opt into the old permissive behavior for local dev only —
    never set this where real Daraja traffic is received.
    """
    shared_secret = os.getenv("DARAJA_SHARED_SECRET")
    configured_ips = _parse_allowed_ips()

    if not shared_secret and not configured_ips:
        if os.getenv("PESAGUARD_ALLOW_UNRESTRICTED_WEBHOOK_SOURCE") == "1":
            logger.warning(
                "Webhook source validation is fully unconfigured (no "
                "DARAJA_SHARED_SECRET, no DARAJA_ALLOWED_IPS) and "
                "PESAGUARD_ALLOW_UNRESTRICTED_WEBHOOK_SOURCE=1 is set — "
                "accepting requests from ANY source. This must never be set "
                "in an environment receiving real Daraja traffic."
            )
            return True
        logger.error(
            "Webhook source validation is fully unconfigured (no "
            "DARAJA_SHARED_SECRET, no DARAJA_ALLOWED_IPS) — rejecting all "
            "webhook requests. Configure at least one before real traffic "
            "can be accepted."
        )
        return False

    if shared_secret:
        header_secret = request.headers.get("X-Daraja-Shared-Secret", "")
        # FIXED: was a plain `!=` string comparison, which leaks timing
        # information about how many leading characters matched. Using
        # hmac.compare_digest for a constant-time comparison.
        if not hmac.compare_digest(header_secret, shared_secret):
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

    # Shared secret was configured and matched, and no IP allowlist was
    # configured — shared secret alone is sufficient in that case.
    return True


def sanitize_error_message(error: object) -> str:
    """Return a generic client-safe error message for external responses."""
    return "Invalid request"
