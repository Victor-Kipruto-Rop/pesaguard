# Provider Routing

## Overview

The provider router manages message delivery across multiple providers with circuit-breaker-aware failover. It ensures that only infrastructure-level degradation triggers failover, while permanent errors (invalid recipient, auth misconfiguration) are raised immediately.

## Router Architecture

```
NotificationRequest
       │
       ▼
ProviderRouter.send()
       │
       ├── For each provider in priority order:
       │   │
       │   ├── CircuitBreaker.allow() → check if provider is healthy
       │   │
       │   ├── If allowed:
       │   │   ├── Call provider.send()
       │   │   ├── On success: record metrics, return result
       │   │   └── On failure:
       │   │       ├── Classify error (internal category)
       │   │       ├── If failover-eligible: try next provider
       │   │       └── If permanent: raise immediately
       │   │
       │   └── If not allowed (circuit open): skip to next provider
       │
       └── If all providers failed: raise last error
```

## Provider Priority

Providers are ordered per channel in `communication_provider_routes`:

```python
order = {
    CommunicationChannel.SMS: ["africas_talking", "backup_sms_provider"],
    CommunicationChannel.EMAIL: ["smtp_email", "backup_email"],
}
```

Priority is determined by the `priority` column (lower = higher priority). Only enabled providers (`enabled=1`) are considered.

## Smart Failover Rules

### Failover Eligible (Infrastructure Degradation)
- `TIMEOUT` - Provider request timed out
- `NETWORK_ERROR` - Connection/DNS failure
- `PROVIDER_UNAVAILABLE` - 503 or service down
- `RATE_LIMITED` - 429 or throttling

### Failover NOT Eligible (Permanent Errors)
- `INVALID_RECIPIENT` - Bad phone/email
- `AUTHENTICATION_ERROR` - Bad credentials
- `AUTHORIZATION_ERROR` - Insufficient permissions
- `INSUFFICIENT_BALANCE` - Need top-up
- `MESSAGE_REJECTED` - Invalid request format
- `VALIDATION_ERROR` - Schema validation failed

Permanent errors are raised immediately so bad traffic is never retried against a healthy backup provider.

## Circuit Breaker Integration

Each provider has its own circuit breaker:

| State | Behavior |
|-------|----------|
| CLOSED | Normal operation, requests allowed |
| OPEN | Requests blocked, waiting for recovery |
| HALF_OPEN | Limited test requests allowed |

### Circuit Breaker Transitions

```
CLOSED ──[consecutive_failures >= threshold]──> OPEN
OPEN ──[recovery_seconds elapsed]──> HALF_OPEN
HALF_OPEN ──[test request succeeds]──> CLOSED
HALF_OPEN ──[test request fails]──> OPEN
```

### Configuration

- `failure_threshold`: Consecutive failures before opening (default: 3-5)
- `recovery_seconds`: Wait time before half-open (default: 60)
- `half_open_max_calls`: Test requests in half-open (default: 2-3)

## Error Classification

All provider responses are mapped to internal error categories:

| Category | Description | Retryable |
|----------|-------------|-----------|
| `VALIDATION_ERROR` | Invalid request | No |
| `AUTHENTICATION_ERROR` | Bad credentials | No |
| `AUTHORIZATION_ERROR` | Insufficient permissions | No |
| `RATE_LIMITED` | Throttled | Yes |
| `TIMEOUT` | Request timed out | Yes |
| `NETWORK_ERROR` | Connection failed | Yes |
| `PROVIDER_UNAVAILABLE` | Service down | Yes |
| `INVALID_RECIPIENT` | Bad recipient | No |
| `INSUFFICIENT_BALANCE` | Need top-up | No |
| `MESSAGE_REJECTED` | Rejected by provider | No |
| `PERMANENT_FAILURE` | Permanent failure | No |
| `UNKNOWN` | Unclassified | Yes |

## Health-Based Routing

Provider health scores (0-100) influence routing decisions:

| Score | Level | Action |
|-------|-------|--------|
| 90-100 | HEALTHY | Normal routing |
| 70-89 | DEGRADED | Increased monitoring |
| 50-69 | CRITICAL | Prefer backup providers |
| 0-49 | OUTAGE | Skip provider |

Health is calculated from: success rate, failure rate, latency, timeout rate, delivery rate, webhook health, and recent incidents.

## Adding a New Provider

1. Implement the `ProviderAdapter` base class
2. Map provider-specific errors to internal categories
3. Register in `communication_provider_routes`
4. Configure priority and failover order

Example:

```python
class MySmsProvider(ProviderAdapter):
    name = "my_sms_provider"
    supported_channels = frozenset({CommunicationChannel.SMS})

    def _send(self, request: NotificationRequest) -> ProviderMessage:
        # Map provider errors to internal categories
        try:
            result = self.client.send(...)
        except TimeoutError:
            raise TransientCommunicationError("timeout", code="PROVIDER_TIMEOUT")
        except ConnectionError:
            raise TransientCommunicationError("network", code="PROVIDER_REQUEST_ERROR")
        # ...
```