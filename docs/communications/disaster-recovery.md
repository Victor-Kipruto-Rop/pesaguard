# Communications Disaster Recovery

Back up communication tables with the primary database and include them in point-in-time recovery. Restore into an isolated environment before production recovery. After restore, verify notification idempotency constraints, outbox leases, provider credentials, webhook routing, and worker connectivity.

For an Africa's Talking outage, stop or drain provider delivery, preserve queued records, communicate degraded status, and replay only after provider health is confirmed. Communication recovery must not block transaction ingestion, reconciliation, fraud detection, or core financial writes.
