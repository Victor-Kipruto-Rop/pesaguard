# Communications Disaster Recovery

## Overview

Communications recovery must never block transaction ingestion, reconciliation, fraud detection, or core financial writes. The recovery procedures below focus on restoring messaging capacity while keeping financial integrity intact.

## Backup

Communication tables are covered by the primary database backup:

| Table | Category |
|-------|----------|
| `communication_notifications` | Operational |
| `communication_outbox_entries` | Operational (queue) |
| `communication_attempts` | Operational |
| `communication_delivery_reports` | Operational |
| `communication_webhook_events` | Operational |
| `communication_templates` | Configuration |
| `communication_preferences` | Customer data |
| `communication_consents` | Regulatory |
| `communication_otp_challenges` | Security |
| `communication_campaigns` | Operational |
| `communication_incidents` | Operational |
| `communication_saved_filters` | User data |
| `communication_tenant_quotas` | Configuration |

Include all tables in point-in-time recovery. Restore into an isolated environment before production recovery.

## Outage Scenarios

### Africa's Talking Outage

| Phase | Action |
|-------|--------|
| Detect | Monitor provider health score, error rate, circuit breaker |
| Mitigate | Stop or drain provider delivery; preserve queued records |
| Communicate | Record incident (PG-INC-xxxxx), alert operators |
| Recover | After provider health confirmed, replay dead-letter/queued |
| Verify | Check delivery rate, latency, provider health recovery |

### Database Outage

| Phase | Action |
|-------|--------|
| Detect | Connection errors, query timeouts |
| Mitigate | Fail over to replica (read); queue sends in memory (best-effort) |
| Communicate | Record incident |
| Recover | Restore from backup / point-in-time recovery |
| Verify | Idempotency constraints, outbox leases, provider credentials |

### Redis/Kafka Outage

| Phase | Action |
|-------|--------|
| Detect | Producer/consumer errors |
| Mitigate | Communications continues via direct DB enqueue (no Kafka dependency) |
| Communicate | Record incident |
| Recover | Restart consumers, verify Kafka lag |
| Verify | Notification events flow again |

### Worker Failure

| Phase | Action |
|-------|--------|
| Detect | Outbox not draining, queue growing |
| Mitigate | Start additional worker instances (leases prevent duplicates) |
| Communicate | Record incident |
| Recover | Restart failed workers |
| Verify | Queue depth decreases, SLA restored |

### Webhook Failure

| Phase | Action |
|-------|--------|
| Detect | Pending-review events, delivery rate drop |
| Mitigate | Check HTTPS, signature secret, provider registration |
| Communicate | Record incident |
| Recover | Replay authenticated inbox records (audited) |
| Verify | Delivery statuses update correctly |

## Recovery Verification Checklist

- [ ] `communication_notifications` idempotency constraints intact
- [ ] `communication_outbox_entries` leases are valid
- [ ] Provider credentials still valid
- [ ] Webhook routing works (test callback)
- [ ] Worker connectivity to DB/Kafka/Redis confirmed
- [ ] No duplicate sends (query for duplicate idempotency keys)
- [ ] Provider health score recovered to HEALTHY
- [ ] Queue latency within SLA targets

## Disaster Recovery Testing

Test the following scenarios regularly:

1. Africa's Talking outage → failover to backup provider
2. Database restore → point-in-time verification
3. Worker crash → lease recovery (no duplicate sends)
4. Webhook outage → inbox replay after recovery
5. Redis/Kafka outage → continued processing via direct enqueue

## Rollback Procedure

If a deployment introduces communication issues:

1. **Disable provider**: Set feature flag `PESAGUARD_FLAG_AFRICASTALKING_SMS=false`
2. **Enable fallback**: Configure backup provider route
3. **Disable campaigns**: `PESAGUARD_FLAG_CAMPAIGNS=false`
4. **Rollback deployment**: Use previous artifact/container
5. **Verify**: Communications healthy AND financial processing unaffected
