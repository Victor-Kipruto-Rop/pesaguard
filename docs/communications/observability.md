# Communications Observability

Track traffic, latency, errors, and saturation for API requests, outbox queue depth, lease age, retry/dead-letter counts, provider response time, delivery rate, webhook failures, and worker health. Propagate `trace_id` and `correlation_id` into logs and lifecycle events.

Minimum alerts: growing queue age, dead-letter increase, provider timeout/error spike, delivery-rate drop, webhook authentication failures, and low provider balance when balance telemetry is available.
