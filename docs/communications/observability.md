# Communications Observability

## Overview

Every communication request is traceable from creation through delivery. The platform emits structured lifecycle events, computes health scores, tracks incidents, and monitors SLA compliance.

## Golden Signals

| Signal | Metric | Source |
|--------|--------|--------|
| Latency | Queue time, provider response, delivery time | `communication_notifications`, `communication_attempts` |
| Traffic | Messages per hour/day, cost per period | `communication_notifications`, `communication_attempts` |
| Errors | Failure rate, dead-letter count, retry rate | `communication_notifications`, `communication_outbox_entries` |
| Saturation | Queue depth, lease age, worker backlog | `communication_outbox_entries` |

## Lifecycle Events

The platform emits `notification.*` events to Kafka topic `notification.status`:

| Event | Meaning |
|-------|---------|
| `notification.created` | Notification record created |
| `notification.queued` | Added to outbox |
| `notification.provider_accepted` | Provider accepted the request |
| `notification.submitted` | Provider accepted for delivery |
| `notification.delivered` | Delivery confirmed via webhook |
| `notification.failed` | Permanent failure |
| `notification.retrying` | Transient failure, scheduled retry |
| `notification.dead_lettered` | Max attempts reached |
| `notification.expired` | Message expired |
| `notification.rejected` | Rejected by provider |

Each event includes `notification_id`, `tenant_id`, `provider`, `correlation_id`, and `trace_id` for distributed tracing.

## Provider Health Score

Real-time health (0-100) computed from:

| Factor | Weight |
|--------|--------|
| Success rate | High |
| Failure rate | High |
| Average latency | Medium |
| Timeout rate | Medium |
| Delivery rate | High |
| Webhook health | Low |
| Recent incidents | Low |

Endpoint: `GET /api/v1/communications/providers/health`

Levels: `HEALTHY` (90+), `DEGRADED` (70-89), `CRITICAL` (50-69), `OUTAGE` (0-49)

## Circuit Breaker State

Per-provider state: `CLOSED` / `OPEN` / `HALF_OPEN`

Exposed in provider health endpoint alongside:
- Consecutive failures
- Failure threshold
- Recovery seconds
- Last error category

## SLA Monitoring

Priority-based queue latency targets:

| Priority | Target |
|----------|--------|
| critical | 5 seconds |
| high | 30 seconds |
| normal | 120 seconds |
| low | 600 seconds |

Configurable via `PESAGUARD_COMMUNICATION_SLA_TARGETS`. SLA breaches create incidents automatically.

## Incidents

Automatic incident creation for:

| Category | Trigger | Severity |
|----------|---------|----------|
| Provider | Consecutive failures ≥ threshold | HIGH |
| SLA | Queue latency > target | MEDIUM-HIGH |
| OTP abuse | Recipient flood / IP enumeration | HIGH-CRITICAL |

Incidents are deduplicated by fingerprint with occurrence counters.

## Cost Analytics

Endpoint: `GET /api/v1/communications/analytics/costs`

| Metric | Description |
|--------|-------------|
| Daily spend | Last 24h total |
| Weekly spend | Last 7 days total |
| Monthly spend | Last 30 days total |
| Projected monthly | Run-rate extrapolation |
| Cost by channel | Per-channel breakdown |
| Wallet health | Balance vs burn rate + runway |

## Metrics to Monitor

### API Layer
- Request rate
- Response time (P95/P99)
- Error rate (4xx/5xx)
- Auth failures

### Worker Layer
- Queue depth (pending + retrying)
- Lease age (stale leases)
- Throughput (messages/sec)
- Retry rate
- Dead-letter rate

### Provider Layer
- Response time
- Success rate
- Timeout rate
- Error category distribution
- Circuit breaker state

### Webhook Layer
- Received rate
- Processed rate
- Duplicate rate
- Auth failure rate
- Pending review count

## Alerts

| Alert | Threshold | Action |
|-------|-----------|--------|
| Queue age growing | > 5 min for critical | Scale workers |
| Dead-letter increase | > 10% of sends | Investigate provider |
| Delivery rate drop | < 95% of accepted | Check provider health |
| Provider timeout spike | > 5% of attempts | Open failover |
| Webhook auth failures | > 1/min | Check secret rotation |
| Low provider balance | Runway < 7 days | Top up wallet |
| SLA breach | Critical > 5s | Create incident |
| Anomaly detected | Z-score > 3 | Investigate cause |

## Tracing

- `trace_id`: End-to-end request trace (API → Kafka → Worker → Provider)
- `correlation_id`: Business correlation (transaction, fraud finding)
- Propagated through lifecycle events and notification records

Search API: `GET /api/v1/communications/messages?trace_id=...`