# Communications Troubleshooting

## Queue backlog
Inspect outbox status, oldest `available_at`, worker health, database connectivity, and provider circuit state. Do not pause financial processing to recover communications.

## Provider failures
Check provider credentials, sandbox/production environment, rate limits, balance, timeout/error metrics, and dead-letter entries. Permanent errors are not retried; correct the cause before replay.

## Webhook failures
Verify HTTPS routing, the canonical webhook secret, signature header, body limit, provider message ID, and duplicate-event records. Never bypass signature checks in production.
