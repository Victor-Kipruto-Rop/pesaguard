# Communications Setup

1. Apply migrations with `alembic upgrade head`.
2. Configure `AFRICASTALKING_USERNAME`, `AFRICASTALKING_API_KEY`, `AFRICASTALKING_ENVIRONMENT`, and `AFRICASTALKING_WEBHOOK_SECRET` in the deployment secret store.
3. Set `PESAGUARD_COMMUNICATION_RETRY_BASE_SECONDS`, `PESAGUARD_COMMUNICATION_RETRY_MAX_SECONDS`, and `PESAGUARD_COMMUNICATION_RETRY_JITTER` for worker backoff.
4. Register `/api/v1/webhooks/africastalking/delivery` with the provider and require HTTPS at the edge.
5. Run the communications worker separately from financial transaction workers.

Use sandbox credentials outside production. Never place provider keys in source, logs, notification bodies, or frontend bundles.
