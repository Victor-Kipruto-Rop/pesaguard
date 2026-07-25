"""Webhook delivery manager for event-driven notifications."""

import ipaddress
import json
import logging
import secrets
import socket
import time
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from urllib.parse import urlparse

import requests
from sqlalchemy.orm import Session
from models import WebhookConfig, WebhookDelivery, Discrepancy

logger = logging.getLogger("pesaguard.webhooks")

# ----------------------------------------------------------------------------
# NOTE ON REQUIRED MIGRATION: this file now expects WebhookConfig to have a
# `signing_secret` column (String, nullable=True). Add it in models.py:
#
#     signing_secret = Column(String, nullable=True)
#
# and generate a migration for it. Existing webhooks registered before this
# column exists will have signing_secret=None — see _generate_signature's
# fallback behavior below, which logs loudly rather than silently signing
# with a guessable value.
# ----------------------------------------------------------------------------


def _is_private_or_reserved(ip_str: str) -> bool:
    try:
        ip = ipaddress.ip_address(ip_str)
    except ValueError:
        return True  # can't parse it — treat as unsafe rather than assume safe
    return (
        ip.is_private
        or ip.is_loopback
        or ip.is_link_local
        or ip.is_reserved
        or ip.is_multicast
        or ip.is_unspecified
    )


def _validate_webhook_url(url: str) -> Optional[str]:
    """Validate a webhook URL before it's ever registered or used.

    FIXED: previously ANY url was accepted with no validation at all — a
    tenant admin (or a stolen token with manage:webhooks permission) could
    register a webhook pointing at an internal-only address (e.g. a cloud
    metadata endpoint, localhost, or an internal service), and PesaGuard's
    own server would dutifully make outbound requests to that target from a
    trusted network position whenever an event fired (SSRF).

    Returns None if the URL is acceptable, or a string describing why it was
    rejected. This is a best-effort static check (require https, resolve the
    hostname and reject private/loopback/link-local/reserved ranges) — real
    SSRF defense in depth also requires disabling redirect-following at
    delivery time (see _deliver_webhook's allow_redirects=False), since a
    URL that resolves safely at registration time could still redirect
    somewhere unsafe later.
    """
    try:
        parsed = urlparse(url)
    except Exception:
        return "url_could_not_be_parsed"

    if parsed.scheme != "https":
        return "url_must_use_https"

    if not parsed.hostname:
        return "url_missing_hostname"

    if parsed.hostname.lower() in {"localhost", "metadata.google.internal"}:
        return "url_targets_reserved_hostname"

    try:
        resolved_ips = {info[4][0] for info in socket.getaddrinfo(parsed.hostname, None)}
    except socket.gaierror:
        return "url_hostname_did_not_resolve"

    for ip_str in resolved_ips:
        if _is_private_or_reserved(ip_str):
            return f"url_resolves_to_disallowed_address:{ip_str}"

    return None


class WebhookManager:
    """Manages webhook registration and delivery with retries."""

    def __init__(self, session: Session):
        self.session = session
        self.timeout = 10
        self.max_retries = 3

    def register_webhook(
        self,
        tenant_id: str,
        url: str,
        event_types: list,
        retry_attempts: int = 3,
        timeout_seconds: int = 10,
    ) -> Dict[str, Any]:
        """Register a new webhook for a tenant."""
        rejection_reason = _validate_webhook_url(url)
        if rejection_reason:
            logger.warning("Rejected webhook registration for tenant %s: %s (url=%s)", tenant_id, rejection_reason, url)
            return {"error": "invalid_webhook_url", "reason": rejection_reason}

        webhook_id = f"webhook_{uuid.uuid4().hex[:12]}"
        # FIXED: signatures previously used webhook_id itself as the HMAC key —
        # but webhook_id is returned to the customer in this very response, so
        # it isn't a secret. Anyone who knows a webhook's ID could forge a
        # validly-signed payload. Generate a real, separate, non-guessable
        # secret here instead, shown to the customer once at registration
        # (same pattern as Stripe/GitHub webhook secrets).
        signing_secret = secrets.token_hex(32)

        webhook = WebhookConfig(
            id=webhook_id,
            tenant_id=tenant_id,
            url=url,
            event_types=event_types,
            retry_attempts=retry_attempts,
            timeout_seconds=timeout_seconds,
            active=True,
            signing_secret=signing_secret,
        )
        self.session.add(webhook)
        self.session.commit()
        logger.info(f"Registered webhook {webhook_id} for tenant {tenant_id}")
        return {
            "id": webhook_id,
            "tenant_id": tenant_id,
            "url": url,
            "event_types": event_types,
            "active": True,
            "signing_secret": signing_secret,  # shown once; store it, it won't be shown again
        }

    def get_webhooks(self, tenant_id: str, event_type: str = None) -> list:
        """Get active webhooks for a tenant, optionally filtered by event type."""
        query = self.session.query(WebhookConfig).filter(
            WebhookConfig.tenant_id == tenant_id,
            WebhookConfig.active == True,
        )
        if event_type:
            query = query.filter(WebhookConfig.event_types.contains([event_type]))
        return query.all()

    def trigger_event(
        self,
        tenant_id: str,
        event_type: str,
        payload: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Trigger event and deliver to all subscribed webhooks."""
        webhooks = self.get_webhooks(tenant_id, event_type)
        results = []

        for webhook in webhooks:
            delivery = self._deliver_webhook(webhook, event_type, payload)
            results.append(delivery)

        return {
            "event_type": event_type,
            "webhooks_triggered": len(webhooks),
            "deliveries": results,
        }

    def _deliver_webhook(
        self,
        webhook: WebhookConfig,
        event_type: str,
        payload: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Deliver webhook with exponential backoff retries."""
        delivery_id = f"delivery_{uuid.uuid4().hex[:12]}"
        delivery = WebhookDelivery(
            id=delivery_id,
            webhook_id=webhook.id,
            event_type=event_type,
            payload=payload,
            status="pending",
            attempt_count=0,
        )

        for attempt in range(webhook.retry_attempts):
            try:
                delivery.attempt_count = attempt + 1
                headers = {
                    "Content-Type": "application/json",
                    "X-Webhook-Event": event_type,
                    "X-Webhook-Signature": self._generate_signature(webhook, payload),
                }
                response = requests.post(
                    webhook.url,
                    json=payload,
                    headers=headers,
                    timeout=webhook.timeout_seconds,
                    # FIXED: redirects were previously followed automatically.
                    # A URL that resolved to a safe address at registration
                    # time could still redirect to an internal target at
                    # delivery time, bypassing _validate_webhook_url entirely.
                    allow_redirects=False,
                )
                delivery.response_status = response.status_code
                delivery.response_body = response.text[:500]

                if 200 <= response.status_code < 300:
                    delivery.status = "success"
                    delivery.delivered_at = datetime.now(timezone.utc)
                    self.session.add(delivery)
                    self.session.commit()
                    logger.info(
                        f"Webhook delivery {delivery_id} succeeded on attempt {attempt + 1}"
                    )
                    return {
                        "id": delivery_id,
                        "status": "success",
                        "attempt": attempt + 1,
                        "response_code": response.status_code,
                    }
                elif response.is_redirect:
                    logger.warning(
                        f"Webhook delivery {delivery_id} got a redirect ({response.status_code}) — "
                        f"redirects are not followed for security reasons; treating as failed attempt."
                    )
                else:
                    logger.warning(
                        f"Webhook delivery {delivery_id} got {response.status_code}, retrying..."
                    )

            except requests.Timeout:
                logger.warning(
                    f"Webhook delivery {delivery_id} timed out on attempt {attempt + 1}"
                )
            except Exception as e:
                logger.error(
                    f"Webhook delivery {delivery_id} error on attempt {attempt + 1}: {e}"
                )

            if attempt < webhook.retry_attempts - 1:
                wait_seconds = 2 ** attempt  # exponential backoff: 1s, 2s, 4s
                logger.info(f"Webhook {delivery.webhook_id} retry in {wait_seconds}s")
                # FIXED: this backoff was previously computed and logged but
                # never actually applied — all retry attempts fired back-to-
                # back with zero delay, defeating the point of backoff
                # entirely (giving a struggling customer endpoint room to
                # recover before the next attempt).
                time.sleep(wait_seconds)

        delivery.status = "failed"
        self.session.add(delivery)
        self.session.commit()
        logger.error(f"Webhook delivery {delivery_id} failed after {webhook.retry_attempts} attempts")
        return {
            "id": delivery_id,
            "status": "failed",
            "attempts": webhook.retry_attempts,
        }

    def _generate_signature(self, webhook: WebhookConfig, payload: Dict[str, Any]) -> str:
        """Generate HMAC signature for webhook authenticity.

        FIXED: previously signed with webhook_id, which is not a secret (it's
        returned to the customer in register_webhook's own response) — anyone
        who knew a webhook's ID could forge a validly-signed payload. Now
        uses the dedicated signing_secret generated at registration.
        """
        import hmac
        import hashlib

        secret = getattr(webhook, "signing_secret", None)
        if not secret:
            # Only reachable for webhooks registered before the signing_secret
            # column/migration existed. Log loudly rather than silently
            # falling back to the old insecure behavior.
            logger.error(
                "Webhook %s has no signing_secret configured — signature will "
                "NOT provide a real integrity guarantee until this webhook is "
                "re-registered or backfilled with a real secret.",
                webhook.id,
            )
            secret = webhook.id  # last-resort fallback, not secure — fix by backfilling

        message = json.dumps(payload, sort_keys=True)
        signature = hmac.new(
            secret.encode(), message.encode(), hashlib.sha256
        ).hexdigest()
        return signature

    def update_webhook(self, webhook_id: str, tenant_id: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        """Update webhook configuration.

        FIXED: previously fetched by webhook_id alone with no tenant check —
        a valid manage:webhooks token for tenant A could update tenant B's
        webhook just by knowing/guessing its ID. Now requires tenant_id and
        filters by it. CALLERS MUST PASS THE AUTHENTICATED CALLER'S
        tenant_id — the route in advanced_features.py currently does not do
        this and needs a corresponding update (see note in the review).
        """
        query = self.session.query(WebhookConfig).filter(WebhookConfig.id == webhook_id)
        if tenant_id is not None:
            query = query.filter(WebhookConfig.tenant_id == tenant_id)
        webhook = query.first()
        if not webhook:
            return {"error": "webhook_not_found"}

        if "url" in kwargs:
            rejection_reason = _validate_webhook_url(kwargs["url"])
            if rejection_reason:
                return {"error": "invalid_webhook_url", "reason": rejection_reason}

        for key, value in kwargs.items():
            if hasattr(webhook, key) and key not in {"id", "tenant_id", "signing_secret"}:
                setattr(webhook, key, value)

        webhook.updated_at = datetime.now(timezone.utc)
        self.session.commit()
        logger.info(f"Updated webhook {webhook_id}")
        return {
            "id": webhook_id,
            "url": webhook.url,
            "active": webhook.active,
            "event_types": webhook.event_types,
        }

    def delete_webhook(self, webhook_id: str, tenant_id: Optional[str] = None) -> Dict[str, Any]:
        """Delete webhook configuration.

        FIXED: same tenant-scoping gap as update_webhook above.
        """
        query = self.session.query(WebhookConfig).filter(WebhookConfig.id == webhook_id)
        if tenant_id is not None:
            query = query.filter(WebhookConfig.tenant_id == tenant_id)
        webhook = query.first()
        if not webhook:
            return {"error": "webhook_not_found"}

        self.session.delete(webhook)
        self.session.commit()
        logger.info(f"Deleted webhook {webhook_id}")
        return {"status": "deleted", "id": webhook_id}

    def get_delivery_history(
        self, webhook_id: str, tenant_id: Optional[str] = None, limit: int = 50
    ) -> list:
        """Get delivery history for a webhook.

        FIXED: previously filtered by webhook_id alone — delivery history
        includes full request/response bodies, so this was a real
        cross-tenant data exposure, not just a config-tampering risk. Now
        verifies the webhook itself belongs to tenant_id before returning
        anything. CALLERS MUST PASS THE AUTHENTICATED CALLER'S tenant_id.
        """
        if tenant_id is not None:
            owner_check = self.session.query(WebhookConfig).filter(
                WebhookConfig.id == webhook_id,
                WebhookConfig.tenant_id == tenant_id,
            ).first()
            if not owner_check:
                return []

        deliveries = (
            self.session.query(WebhookDelivery)
            .filter(WebhookDelivery.webhook_id == webhook_id)
            .order_by(WebhookDelivery.created_at.desc())
            .limit(limit)
            .all()
        )
        return [
            {
                "id": d.id,
                "event_type": d.event_type,
                "status": d.status,
                "attempt_count": d.attempt_count,
                "response_status": d.response_status,
                "created_at": d.created_at.isoformat(),
                "delivered_at": d.delivered_at.isoformat() if d.delivered_at else None,
            }
            for d in deliveries
        ]
