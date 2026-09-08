# Provider Failover

## Overview

The failover system ensures reliable message delivery by automatically switching to backup providers when the primary provider experiences infrastructure degradation. Failover is governed by circuit breakers, error classification, and provider health scores.

## Failover Architecture

```
Primary Provider (Africa's Talking)
       │
       ├── Success → Deliver message
       │
       └── Failure
              │
              ├── Classify error
              │
              ├── Permanent error → Raise immediately (no failover)
              │   ├── INVALID_RECIPIENT
              │   ├── AUTHENTICATION_ERROR
              │   ├── INSUFFICIENT_BALANCE
              │   └── MESSAGE_REJECTED
              │
              └── Transient error → Failover to backup
                  ├── TIMEOUT
                  ├── NETWORK_ERROR
                  ├── PROVIDER_UNAVAILABLE
                  └── RATE_LIMITED
                         │
                         ▼
                  Backup Provider
                         │
                         ├── Success → Deliver message
                         └── Failure → Try next backup / Dead letter
```

## Failover Triggers

Failover occurs ONLY for infrastructure-level degradation:

| Trigger | Description |
|---------|-------------|
| Circuit OPEN | Too many consecutive failures |
| Timeout | Provider request exceeded timeout |
| Network error | Connection/DNS failure |
| Provider unavailable | 503 or service down |
| Rate limited | 429 or throttling |

## Failover Does NOT Trigger On

Permanent errors are raised immediately without failover:

| Error | Reason |
|-------|--------|
| Invalid recipient | Backup will also fail |
| Auth misconfiguration | Backup uses same config |
| Insufficient balance | Need top-up, not failover |
| Invalid request | Bad data, not provider issue |

## Circuit Breaker States

```
┌─────────┐     consecutive      ┌─────────┐
│ CLOSED  │─────failures >= ─────>│  OPEN   │
│         │     threshold         │         │
└─────────┘                       └─────────┘
     ^                                 │
     │                                 │ recovery_seconds
     │ success                         │ elapsed
     │                                 v
     │                           ┌─────────────┐
     │                           │  HALF_OPEN  │
     │                           │             │
     │                           └─────────────┘
     │                                 │
     │                                 │ test request
     │                                 │ fails
     │                                 │
     └─────────────────────────────────┘
```

### State Transitions

1. **CLOSED → OPEN**: When consecutive failures reach `failure_threshold`
2. **OPEN → HALF_OPEN**: After `recovery_seconds` elapsed
3. **HALF_OPEN → CLOSED**: When a test request succeeds
4. **HALF_OPEN → OPEN**: When a test request fails

## Retry Strategy

Within a single provider, retries use exponential backoff with jitter:

| Attempt | Delay |
|---------|-------|
| 1 | Immediate |
| 2 | 5 seconds |
| 3 | 30 seconds |
| 4 | 2 minutes |
| 5 | 10 minutes |

After max attempts, the message is dead-lettered.

## Provider Health Score

Real-time health scoring (0-100) based on:

| Factor | Weight | Source |
|--------|--------|--------|
| Success rate | High | Attempt outcomes |
| Failure rate | High | Attempt outcomes |
| Latency | Medium | Provider response time |
| Timeout rate | Medium | Timeout count |
| Delivery rate | High | Webhook confirmations |
| Webhook health | Low | Processed/received ratio |
| Recent incidents | Low | Open incidents |

## Failover Configuration

Configure provider priority in `communication_provider_routes`:

```sql
INSERT INTO communication_provider_routes (tenant_id, channel, provider, priority, enabled)
VALUES ('tenant-a', 'sms', 'africas_talking', 100, 1);

INSERT INTO communication_provider_routes (tenant_id, channel, provider, priority, enabled)
VALUES ('tenant-a', 'sms', 'backup_sms', 200, 1);
```

Lower priority value = higher preference.

## Monitoring Failover

Key metrics to track:

- **Failover rate**: How often failover occurs
- **Failover success rate**: How often backup succeeds
- **Circuit breaker state**: Current state per provider
- **Provider health score**: Real-time health per provider
- **Time to failover**: How quickly failover triggers

## Troubleshooting Failover

| Symptom | Cause | Action |
|---------|-------|--------|
| Frequent failover | Primary provider degraded | Check provider health, consider permanent switch |
| Failover not triggering | Error classified as permanent | Verify error classification logic |
| Both providers failing | Infrastructure issue | Check network, DNS, credentials |
| Circuit stuck OPEN | Recovery timeout too long | Adjust `recovery_seconds` |