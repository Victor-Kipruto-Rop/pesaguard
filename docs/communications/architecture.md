# Communications Architecture

Communication requests are tenant-scoped records written to `communication_notifications` with a unique `(tenant_id, idempotency_key)`. Queueable sends create a durable `communication_outbox_entries` row in the same database transaction. `communications_worker` leases entries, calls a provider adapter, records attempts, and applies bounded retries/dead-letter behavior.

Provider callbacks enter through the authenticated delivery endpoint, are deduplicated by provider event identity, and update the notification using the lifecycle validator. Communication failures must remain isolated from transaction ingestion, reconciliation, and fraud processing.

The current implementation is an SMS/Africa's Talking foundation. Provider routing, secondary providers, async inbox processing, and the complete policy engine remain follow-up work.
