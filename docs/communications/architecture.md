# Communications Architecture

## Overview

The PesaGuard communications platform is a provider-independent, event-driven notification system deeply integrated with the PesaGuard financial ecosystem. It transforms business events (transactions, fraud alerts, reconciliation exceptions) into multi-channel customer communications (SMS, email, voice, WhatsApp, USSD) through an intelligent policy engine.

## Core Principles

1. **Financial integrity first** - Communications failures never block transaction ingestion, reconciliation, or fraud detection
2. **Provider independence** - Business logic uses internal error categories, not provider-specific strings
3. **Event-driven** - Services publish events; the notification engine decides channels/timing
4. **Durable & observable** - Every message is traceable from creation through delivery
5. **Tenant-scoped** - All communications are isolated per tenant with configurable policies

## Architecture Diagram

```
PesaGuard Services
       │
       ├── Transaction Service ──────────┐
       ├── Reconciliation Service ───────┤
       ├── Fraud/Risk Engine ────────────┤
       └── Security Service ─────────────┤
                                         ▼
                              Event Streaming (Kafka)
                                         │
                                         ▼
                              Notification Intelligence
                                         │
                              ┌──────────┴──────────┐
                              ▼                     ▼
                     Policy Engine            Quiet Hours
                     ├─ Channel selection    ├─ Timezone-aware
                     ├─ Priority             ├─ Critical override
                     ├─ Template             └─ Marketing delay
                     ├─ Delay/fallback
                     └─ Incident trigger
                                         │
                                         ▼
                              Communication Router
                                         │
                              ┌──────────┴──────────┐
                              ▼                     ▼
                     Circuit Breaker          Provider Health
                     ├─ CLOSED/OPEN/HALF      ├─ Success rate
                     ├─ Recovery timeout      ├─ Latency
                     └─ Half-open tests       └─ Delivery rate
                                         │
                                         ▼
                              Durable Outbox
                                         │
                              ┌──────────┴──────────┐
                              ▼                     ▼
                     Worker Pool            Dead Letter Queue
                     ├─ Priority-aware      ├─ Permanent failures
                     ├─ Lease-based         └─ Admin replay
                     └─ Bounded retries
                                         │
                                         ▼
                              Provider Adapters
                                         │
                    ┌────────────┬───────┴────────┬────────────┐
                    ▼            ▼                ▼            ▼
              Africa's       SMTP Email       Generic       Future
              Talking       (SmtpEmail       Channel       Providers
              (SMS)         Provider)        Provider
                                         │
                                         ▼
                              Delivery Intelligence
                                         │
                              ┌──────────┴──────────┐
                              ▼                     ▼
                     Delivery Reports          Webhook Inbox
                     ├─ Status updates         ├─ Replay protection
                     ├─ Cost attribution       ├─ Payload hashing
                     └─ Latency tracking       └─ Admin replay
```

## Data Flow

### Outbound (Send)
1. Business service publishes event to Kafka `notification.events`
2. Notification worker consumes event, applies policy engine
3. Policy engine decides: channels, priority, template, delay, fallback
4. For each channel, create `CommunicationNotification` + `CommunicationOutboxEntry`
5. Worker leases entries (priority-aware), calls provider adapter
6. Provider adapter maps to internal error categories
7. On success: record attempt, cost, latency, emit lifecycle event
8. On failure: classify error, retry with backoff or dead-letter

### Inbound (Delivery)
1. Provider calls `/api/v1/webhooks/africastalking/delivery`
2. Verify HMAC-SHA256 signature
3. Validate timestamp (replay protection)
4. Parse and validate payload
5. Deduplicate by provider event ID
6. Store in webhook inbox (async processing)
7. Apply delivery status to notification
8. Emit lifecycle event

## State Machine

```
CREATED → QUEUED → PROCESSING → ACCEPTED → SUBMITTED → DELIVERED
                         │
                         ↓
                      FAILED → RETRYING → PROCESSING
                         │
                         ↓
                      DEAD_LETTER → QUEUED (admin replay)
```

Terminal states: DELIVERED, OPENED, CLICKED, BOUNCED, COMPLAINED, REJECTED, EXPIRED, CANCELLED.

## Database Tables

| Table | Purpose |
|-------|---------|
| `communication_notifications` | Core message records with lifecycle status |
| `communication_outbox_entries` | Durable queue with leasing |
| `communication_attempts` | Provider attempt history with cost/latency |
| `communication_delivery_reports` | Provider delivery callbacks |
| `communication_webhook_events` | Inbox for webhook processing |
| `communication_templates` | Versioned message templates |
| `communication_preferences` | Customer channel/quiet-hours preferences |
| `communication_consents` | Customer consent records |
| `communication_otp_challenges` | OTP issuance and verification |
| `communication_campaigns` | Bulk campaign management |
| `communication_campaign_recipients` | Per-recipient campaign state |
| `communication_provider_routes` | Configured provider priority |
| `communication_incidents` | Operational incidents |
| `communication_saved_filters` | User-saved search filters |
| `communication_tenant_quotas` | Tenant usage quotas |

## Key Components

### Policy Engine (`policy.py`)
Pure decision engine: event + context → channels/priority/delay/fallback. Supports tenant configuration, quiet hours, risk classification, and reconciliation escalation.

### Circuit Breaker (`providers/router.py`)
Per-provider circuit breaker with CLOSED/OPEN/HALF_OPEN states. Prevents cascade failures and enables smart failover.

### Rate Governor (`governor.py`)
Token-bucket rate limiter per provider with queue backpressure. Automatically slows traffic when providers or queues are saturated.

### Incident Manager (`incidents.py`)
Fingerprint-based incident deduplication and aggregation. SLA breach detection with automatic incident creation.

### Anomaly Detection (`anomaly.py`)
Statistical baselines for message volume, failure rate, and OTP patterns. Detects spikes, drops, and abuse.
