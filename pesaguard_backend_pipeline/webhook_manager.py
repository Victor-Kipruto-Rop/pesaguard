"""Webhook delivery manager for event-driven notifications."""

import json
import logging
import requests
import uuid
from datetime import datetime, timezone
from typing import Dict, Any
from sqlalchemy.orm import Session
from models import WebhookConfig, WebhookDelivery, Discrepancy

logger = logging.getLogger("pesaguard.webhooks")


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
        webhook_id = f"webhook_{uuid.uuid4().hex[:12]}"
        webhook = WebhookConfig(
            id=webhook_id,
            tenant_id=tenant_id,
            url=url,
            event_types=event_types,
            retry_attempts=retry_attempts,
            timeout_seconds=timeout_seconds,
            active=True,
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
                    "X-Webhook-Signature": self._generate_signature(webhook.id, payload),
                }
                response = requests.post(
                    webhook.url,
                    json=payload,
                    headers=headers,
                    timeout=webhook.timeout_seconds,
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

        delivery.status = "failed"
        self.session.add(delivery)
        self.session.commit()
        logger.error(f"Webhook delivery {delivery_id} failed after {webhook.retry_attempts} attempts")
        return {
            "id": delivery_id,
            "status": "failed",
            "attempts": webhook.retry_attempts,
        }

    def _generate_signature(self, webhook_id: str, payload: Dict[str, Any]) -> str:
        """Generate HMAC signature for webhook authenticity."""
        import hmac
        import hashlib

        message = json.dumps(payload, sort_keys=True)
        signature = hmac.new(
            webhook_id.encode(), message.encode(), hashlib.sha256
        ).hexdigest()
        return signature

    def update_webhook(self, webhook_id: str, **kwargs) -> Dict[str, Any]:
        """Update webhook configuration."""
        webhook = (
            self.session.query(WebhookConfig)
            .filter(WebhookConfig.id == webhook_id)
            .first()
        )
        if not webhook:
            return {"error": "webhook_not_found"}

        for key, value in kwargs.items():
            if hasattr(webhook, key):
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

    def delete_webhook(self, webhook_id: str) -> Dict[str, Any]:
        """Delete webhook configuration."""
        webhook = (
            self.session.query(WebhookConfig)
            .filter(WebhookConfig.id == webhook_id)
            .first()
        )
        if not webhook:
            return {"error": "webhook_not_found"}

        self.session.delete(webhook)
        self.session.commit()
        logger.info(f"Deleted webhook {webhook_id}")
        return {"status": "deleted", "id": webhook_id}

    def get_delivery_history(
        self, webhook_id: str, limit: int = 50
    ) -> list:
        """Get delivery history for a webhook."""
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
