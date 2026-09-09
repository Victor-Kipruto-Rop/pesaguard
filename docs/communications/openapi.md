# PesaGuard Communications API — OpenAPI Specification

**Version:** 1.0.0  
**Base URL:** `/api/v1`  
**Status:** Production  
**Lifecycle:** Stable

This document describes the PesaGuard enterprise communications API. Every
endpoint is versioned, authenticated, rate-limited, and observable.

## Authentication

All endpoints require a valid API key in the `Authorization` header:

```
Authorization: Bearer <api_key>
```

API keys are tenant-scoped. Cross-tenant access is denied. Keys can be
created, rotated, and revoked from the developer portal.

## Rate Limits

| Tier | Requests/minute | Burst |
|------|-----------------|-------|
| Standard | 300 | 50 |
| Premium | 1,200 | 200 |
| Enterprise | Custom | Custom |

Rate limit headers are returned on every response:

```
X-RateLimit-Limit: 300
X-RateLimit-Remaining: 287
X-RateLimit-Reset: 1725782400
Retry-After: 60
```

## Error Response Format

All errors follow a consistent schema:

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "The request body contains invalid fields",
    "details": [
      {
        "field": "recipient.value",
        "issue": "Must be a valid E.164 phone number",
        "value": "0712345678"
      }
    ],
    "request_id": "req-789",
    "timestamp": "2026-09-08T09:31:22.145Z"
  }
}
```

### Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `VALIDATION_ERROR` | 400 | Request validation failed |
| `UNAUTHENTICATION_ERROR` | 401 | Missing or invalid credentials |
| `AUTHORIZATION_ERROR` | 403 | Insufficient permissions |
| `NOT_FOUND` | 404 | Resource not found |
| `DUPLICATE_NOTIFICATION` | 409 | Idempotency key already used |
| `INVALID_STATE_TRANSITION` | 409 | Invalid notification state change |
| `RATE_LIMITED` | 429 | Rate limit exceeded |
| `PROVIDER_UNAVAILABLE` | 503 | No healthy provider |
| `INTERNAL_ERROR` | 500 | Unexpected server error |

## Versioning

The API uses URL path versioning:

```
/api/v1/communications/notifications
/api/v2/communications/notifications  (future)
```

Version upgrades will be announced at least 90 days in advance.

---

## 1. Enqueue Notification

```
POST /api/v1/communications/notifications
```

Send a notification through the intelligent routing pipeline.

### Request

```json
{
  "tenant_id": "tenant_abc123",
  "event": "transaction.completed",
  "recipient": {
    "type": "phone",
    "value": "+254712345678"
  },
  "template": "transaction_receipt_v2",
  "template_data": {
    "transaction_id": "PG-TR-98234",
    "amount": "KES 25,000.00",
    "balance": "KES 125,000.00",
    "receipt_code": "RT-98234-XYZ"
  },
  "priority": "NORMAL",
  "idempotency_key": "PG-TR-98234-receipt-phone",
  "channel_overrides": null,
  "metadata": {
    "correlation_id": "corr-789",
    "trace_id": "trace-456"
  }
}
```

### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `tenant_id` | string | yes | Tenant identifier |
| `event` | string | yes | Business event triggering notification |
| `recipient.type` | string | yes | phone, email, whatsapp, ussd, webhook |
| `recipient.value` | string | yes | E.164 phone or email address |
| `template` | string | no | Template name |
| `template_data` | object | no | Template substitution variables |
| `priority` | string | no | CRITICAL, HIGH, NORMAL, LOW |
| `idempotency_key` | string | yes | Unique key for deduplication |
| `channel_overrides` | object | no | Force specific channel/provider |
| `metadata.correlation_id` | string | no | Correlation ID for tracing |
| `metadata.trace_id` | string | no | Trace ID for distributed tracing |

### Response 201

```json
{
  "notification_id": "PG-NTF-98234-001",
  "status": "QUEUED",
  "tenant_id": "tenant_abc123",
  "channel": "SMS",
  "provider": "africas_talking",
  "priority": "NORMAL",
  "created_at": "2026-09-08T09:31:22.145Z",
  "queued_at": "2026-09-08T09:31:22.148Z",
  "trace_id": "trace-456",
  "correlation_id": "corr-789"
}
```

### Errors

| Status | Code | Description |
|--------|------|-------------|
| 400 | VALIDATION_ERROR | Invalid request body |
| 401 | UNAUTHENTICATION_ERROR | Missing or invalid API key |
| 403 | AUTHORIZATION_ERROR | Tenant not authorized |
| 409 | DUPLICATE_NOTIFICATION | Idempotency key already processed |
| 429 | RATE_LIMITED | Rate limit exceeded |
| 503 | PROVIDER_UNAVAILABLE | No healthy provider available |

## 2. Get Notification Status

```
GET /api/v1/communications/notifications/{notification_id}
```

Retrieve the full lifecycle state of a notification.

### Response 200

```json
{
  "notification_id": "PG-NTF-98234-001",
  "tenant_id": "tenant_abc123",
  "transaction_id": "PG-TR-98234",
  "customer_id": "cust-567",
  "channel": "SMS",
  "provider": "africas_talking",
  "provider_message_id": "AT-18293041",
  "template": "transaction_receipt_v2",
  "priority": "NORMAL",
  "status": "DELIVERED",
  "status_details": {
    "state": "DELIVERED",
    "since": "2026-09-08T09:32:04.832Z",
    "attempts": 1,
    "queue_time_ms": 3,
    "provider_response_time_ms": 182,
    "delivery_time_ms": 42123,
    "total_latency_ms": 42608
  },
  "attempt_history": [
    {
      "attempt": 1,
      "status": "DELIVERED",
      "provider_response_at": "2026-09-08T09:32:04.832Z",
      "latency_ms": 182,
      "error": null
    }
  ],
  "cost": {
    "provider": "africas_talking",
    "channel": "SMS",
    "segments": 1,
    "unit_cost": 0.80,
    "total_cost": 0.80,
    "currency": "KES"
  },
  "trace_id": "trace-456",
  "correlation_id": "corr-789",
  "created_at": "2026-09-08T09:31:22.145Z",
  "delivered_at": "2026-09-08T09:32:04.832Z"
}
```

## 3. List Notifications

```
GET /api/v1/communications/notifications
```

Paginated search with advanced filters.

### Query Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| status | string | QUEUED, PROCESSING, DELIVERED, FAILED |
| channel | string | SMS, EMAIL, WHATSAPP, VOICE, USSD |
| provider | string | africastalking, smtp, etc. |
| tenant_id | string | Filter by tenant |
| customer_id | string | Filter by customer |
| template | string | Filter by template |
| priority | string | Filter by priority |
| transaction_id | string | Filter by transaction |
| provider_message_id | string | Filter by provider message ID |
| correlation_id | string | Filter by correlation ID |
| trace_id | string | Filter by trace ID |
| phone | string | Filter by phone number |
| date_from | string | ISO 8601 start date |
| date_to | string | ISO 8601 end date |
| page | integer | Page number (default 1) |
| per_page | integer | Items per page (default 25, max 100) |
| sort | string | Sort field (default created_at) |
| order | string | asc or desc (default desc) |

### Response 200

```json
{
  "data": [
    {
      "notification_id": "PG-NTF-98234-001",
      "tenant_id": "tenant_abc123",
      "status": "DELIVERED",
      "channel": "SMS",
      "provider": "africas_talking",
      "priority": "NORMAL",
      "template": "transaction_receipt_v2",
      "customer_id": "cust-567",
      "created_at": "2026-09-08T09:31:22.145Z",
      "delivered_at": "2026-09-08T09:32:04.832Z"
    }
  ],
  "pagination": {
    "page": 1,
    "per_page": 25,
    "total_items": 1847,
    "total_pages": 74
  }
}
```

## 4. Retry Notification

```
POST /api/v1/communications/notifications/{notification_id}/retry
```

Manually retry a failed notification. Requires elevated permissions.

### Request

```json
{
  "reason": "Manual retry after provider recovery",
  "attempt_count": null
}
```

### Response 200

```json
{
  "notification_id": "PG-NTF-98234-001",
  "status": "RETRYING",
  "attempt_count": 2,
  "retry_reason": "Manual retry after provider recovery",
  "queued_at": "2026-09-08T10:15:00.000Z"
}
```

## 5. Cancel Notification

```
POST /api/v1/communications/notifications/{notification_id}/cancel
```

Cancel a queued or processing notification. Requires elevated permissions.

### Response 200

```json
{
  "notification_id": "PG-NTF-98234-001",
  "status": "CANCELLED",
  "cancelled_at": "2026-09-08T10:15:00.000Z"
}
```

## 6. Webhook Delivery Endpoint

```
POST /api/v1/communications/webhooks/{channel}
```

Africa's Talking delivery webhook endpoint.

### Headers

| Header | Required | Description |
|--------|----------|-------------|
| Authorization | yes | Bearer token or API key |
| X-Timestamp | yes | Unix timestamp (replay protection) |
| X-Signature | yes | HMAC-SHA256 signature |

### Request Body

```json
{
  "status": "Delivered",
  "phoneNumber": "+254712345678",
  "amount": "1",
  "errorCode": "",
  "duration": "0",
  "messageId": "AT-18293041",
  "queueTimestamps": "1725782400",
  "reference": "PG-NTF-98234-001",
  "cost": "1",
  "recipients": [
    {
      "status": "Delivered",
      "number": "254712345678",
      "messageId": "AT-18293041",
      "cost": "1",
      "errorCode": "",
      "providerRef": "AT-18293041"
    }
  ],
  "OTPCode": null,
  "OTPIsValid": null,
  "USSDResponse": null,
  "balance": "12500.00",
  "message": null,
  "networkCode": "Safaricom"
}
```

### Response 200

```json
{
  "status": "ACKNOWLEDGED",
  "notification_id": "PG-NTF-98234-001",
  "processed_at": "2026-09-08T09:32:04.850Z",
  "inbox_event_id": "PG-INB-88234"
}
```

### Errors

| Status | Code | Description |
|--------|------|-------------|
| 400 | SIGNATURE_VERIFICATION_FAILED | Invalid webhook signature |
| 400 | REPLAY_DETECTED | Timestamp too old or in future |
| 404 | UNKNOWN_CHANNEL | Channel not configured |
| 409 | DUPLICATE_WEBHOOK | Already processed (idempotent) |

## 7. Provider Health

```
GET /api/v1/communications/providers/{provider}/health
```

Real-time provider health status.

### Response 200

```json
{
  "provider": "africas_talking",
  "status": "HEALTHY",
  "health_score": 99.72,
  "channels": {
    "SMS": {
      "status": "HEALTHY",
      "success_rate": 99.92,
      "failure_rate": 0.08,
      "delivery_rate": 99.85,
      "latency_ms": 182,
      "p95_latency_ms": 340,
      "p99_latency_ms": 520,
      "error_rate": 0.08,
      "requests_24h": 842391,
      "successes_24h": 841703,
      "failures_24h": 688,
      "circuit_breaker": "CLOSED",
      "last_failure_at": null
    },
    "USSD": {
      "status": "HEALTHY",
      "success_rate": 99.88,
      "failure_rate": 0.12,
      "delivery_rate": 99.75,
      "latency_ms": 210,
      "p95_latency_ms": 410,
      "p99_latency_ms": 680,
      "error_rate": 0.12,
      "requests_24h": 12483,
      "successes_24h": 12466,
      "failures_24h": 17,
      "circuit_breaker": "CLOSED",
      "last_failure_at": null
    },
    "Voice": {
      "status": "DEGRADED",
      "success_rate": 94.21,
      "failure_rate": 5.79,
      "delivery_rate": 93.50,
      "latency_ms": 890,
      "p95_latency_ms": 1450,
      "p99_latency_ms": 2200,
      "error_rate": 5.79,
      "requests_24h": 1842,
      "successes_24h": 1735,
      "failures_24h": 107,
      "circuit_breaker": "HALF_OPEN",
      "last_failure_at": "2026-09-08T08:23:12.000Z"
    },
    "WhatsApp": {
      "status": "HEALTHY",
      "success_rate": 99.95,
      "failure_rate": 0.05,
      "delivery_rate": 99.88,
      "latency_ms": 245,
      "p95_latency_ms": 420,
      "p99_latency_ms": 610,
      "error_rate": 0.05,
      "requests_24h": 56234,
      "successes_24h": 56204,
      "failures_24h": 30,
      "circuit_breaker": "CLOSED",
      "last_failure_at": null
    }
  },
  "balance": {
    "currency": "KES",
    "balance": 12500.00,
    "last_top_up": "2026-09-01T00:00:00.000Z",
    "daily_burn": 3200.00,
    "weekly_burn": 18500.00,
    "monthly_burn": 78400.00,
    "estimated_runway_days": 49,
    "health": "HEALTHY"
  },
  "last_updated": "2026-09-08T09:32:05.000Z"
}
```

## 8. Incident List

```
GET /api/v1/communications/incidents
```

List communication incidents.

### Query Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| status | string | OPEN, INVESTIGATING, MITIGATED, RESOLVED |
| severity | string | LOW, MEDIUM, HIGH, CRITICAL |
| provider | string | Filter by provider |
| date_from | string | ISO 8601 start |
| date_to | string | ISO 8601 end |

### Response 200

```json
{
  "data": [
    {
      "incident_id": "PG-INC-10291",
      "title": "Africa's Talking SMS degradation",
      "status": "INVESTIGATING",
      "severity": "HIGH",
      "provider": "africas_talking",
      "channel": "SMS",
      "started_at": "2026-09-08T01:42:00.000Z",
      "resolved_at": null,
      "impact": {
        "messages_affected": 182931,
        "delivery_rate": 81.2,
        "failure_rate": 18.8,
        "avg_latency_ms": 3400
      },
      "fingerprint": "at-sms-degradation-20260908-0142",
      "aggregated_events": 2931,
      "metric_anomalies": [
        {
          "metric": "delivery_rate",
          "expected": 99.9,
          "actual": 81.2,
          "deviation": -18.7
        }
      ],
      "assigned_to": "pg-oncall-01",
      "notes": "Investigating provider latency spike"
    }
  ],
  "pagination": {
    "page": 1,
    "per_page": 25,
    "total_items": 3,
    "total_pages": 1
  }
}
```

## 9. Anomaly Detection

```
GET /api/v1/communications/anomalies
```

List active anomalies.

### Response 200

```json
{
  "data": [
    {
      "anomaly_id": "PG-ANM-88234",
      "metric": "sms_delivery_rate",
      "description": "SMS delivery rate dropped below threshold",
      "severity": "HIGH",
      "detected_at": "2026-09-08T01:42:00.000Z",
      "current_value": 81.2,
      "baseline_value": 99.9,
      "deviation_percent": -18.7,
      "status": "ACTIVE",
      "trigger": "Z-SCORE",
      "z_score": -4.2,
      "provider": "africas_talking",
      "window_start": "2026-09-08T01:40:00.000Z",
      "window_end": "2026-09-08T01:45:00.000Z",
      "samples": 6,
      "observation_window_minutes": 5
    }
  ],
  "pagination": {
    "page": 1,
    "per_page": 25,
    "total_items": 1,
    "total_pages": 1
  }
}
```

## 10. OTP Request

```
POST /api/v1/communications/otp/request
```

Request an OTP with security hardening.

### Request

```json
{
  "tenant_id": "tenant_abc123",
  "phone": "+254712345678",
  "purpose": "login_verification",
  "channel": "SMS",
  "account_id": "cust-567",
  "ip_address": "192.168.1.100",
  "user_agent": "Mozilla/5.0...",
  "risk_score": 15,
  "metadata": {}
}
```

### Response 200

```json
{
  "otp_id": "PG-OTP-88234",
  "status": "PENDING",
  "expires_at": "2026-09-08T09:36:22.145Z",
  "channel": "SMS",
  "message": "OTP sent successfully"
}
```

### Rate Limit Errors

| Status | Code | Description |
|--------|------|-------------|
| 429 | OTP_RATE_LIMITED_PHONE | Too many OTPs to this phone |
| 429 | OTP_RATE_LIMITED_IP | Too many OTP requests from this IP |
| 429 | OTP_RATE_LIMITED_ACCOUNT | Too many OTP requests for this account |

## 11. OTP Verify

```
POST /api/v1/communications/otp/verify
```

Verify an OTP.

### Request

```json
{
  "tenant_id": "tenant_abc123",
  "otp_id": "PG-OTP-88234",
  "code": "123456"
}
```

### Response 200

```json
{
  "otp_id": "PG-OTP-88234",
  "valid": true,
  "attempts_used": 1,
  "verified_at": "2026-09-08T09:33:10.000Z"
}
```

## 12. Campaign Management

```
POST /api/v1/communications/campaigns
```

Create a bulk SMS campaign.

### Request

```json
{
  "tenant_id": "tenant_abc123",
  "name": "Q3 Transaction Receipts",
  "description": "Send receipts to all Q3 completed transactions",
  "channel": "SMS",
  "provider": "africas_talking",
  "recipients": {
    "query": "transaction.completed AND date >= 2026-07-01",
    "estimated_count": 1245820
  },
  "template": "q3_receipt_v3",
  "template_data": {
    "campaign_name": "Q3 Receipts"
  },
  "priority": "NORMAL",
  "rate_limit": {
    "messages_per_minute": 10000,
    "messages_per_hour": 500000
  },
  "quiet_hours": {
    "enabled": true,
    "start": "22:00",
    "end": "06:00",
    "timezone": "Africa/Nairobi",
    "critical_override": false
  },
  "confirmation_required": true
}
```

### Response 201

```json
{
  "campaign_id": "PG-CMP-88234",
  "status": "PENDING_CONFIRMATION",
  "tenant_id": "tenant_abc123",
  "channel": "SMS",
  "provider": "africas_talking",
  "recipients": {
    "count": 1245820,
    "estimated_segments": 1389221,
    "estimated_cost": {
      "amount": 1111376.80,
      "currency": "KES"
    }
  },
  "rate_limit": {
    "messages_per_minute": 10000,
    "messages_per_hour": 500000
  },
  "created_at": "2026-09-08T09:31:22.145Z",
  "requires_confirmation": true
}
```

## 13. Confirm Campaign

```
POST /api/v1/communications/campaigns/{campaign_id}/confirm
```

Confirm and start a campaign.

### Request

```json
{
  "reason": "Approved for Q3 receipt distribution",
  "acknowledged_cost": 1111376.80,
  "acknowledged_segments": 1389221
}
```

### Response 200

```json
{
  "campaign_id": "PG-CMP-88234",
  "status": "ACTIVE",
  "started_at": "2026-09-08T09:35:00.000Z",
  "progress": {
    "sent": 0,
    "delivered": 0,
    "failed": 0,
    "remaining": 1245820
  }
}
```

## 14. Pause/Resume/Cancel Campaign

```
POST /api/v1/communications/campaigns/{campaign_id}/pause
POST /api/v1/communications/campaigns/{campaign_id}/resume
POST /api/v1/communications/campaigns/{campaign_id}/cancel
```

Campaign lifecycle control. Requires elevated permissions.

### Response 200 (pause)

```json
{
  "campaign_id": "PG-CMP-88234",
  "status": "PAUSED",
  "paused_at": "2026-09-08T09:36:00.000Z",
  "progress": {
    "sent": 45231,
    "delivered": 44892,
    "failed": 339,
    "remaining": 1200589
  }
}
```

## 15. Communication Cost Reports

```
GET /api/v1/communications/costs
```

Cost attribution and forecasting.

### Query Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| tenant_id | string | Filter by tenant |
| provider | string | Filter by provider |
| channel | string | Filter by channel |
| period | string | daily, weekly, monthly |
| date_from | string | Start date |
| date_to | string | End date |

### Response 200

```json
{
  "period": "monthly",
  "date_from": "2026-09-01",
  "date_to": "2026-09-08",
  "total_cost": {
    "amount": 183000.00,
    "currency": "KES"
  },
  "by_channel": {
    "SMS": {
      "cost": 142000.00,
      "messages": 177500,
      "avg_cost_per_message": 0.80
    },
    "Email": {
      "cost": 0.00,
      "messages": 12400,
      "avg_cost_per_message": 0.00
    },
    "WhatsApp": {
      "cost": 41000.00,
      "messages": 20500,
      "avg_cost_per_message": 2.00
    }
  },
  "by_provider": {
    "africas_talking": {
      "cost": 183000.00,
      "messages": 198000
    }
  },
  "forecast": {
    "projected_monthly": 241000.00,
    "expected_increase_percent": 31.7,
    "basis": "8-day actual extrapolated to 30 days",
    "confidence": "MEDIUM"
  },
  "daily_breakdown": [
    {"date": "2026-09-01", "cost": 22000.00, "messages": 27500},
    {"date": "2026-09-02", "cost": 24000.00, "messages": 30000}
  ]
}
```

## 16. Saved Filters

```
GET    /api/v1/communications/filters
POST   /api/v1/communications/filters
DELETE /api/v1/communications/filters/{filter_id}
```

### Request (POST)

```json
{
  "tenant_id": "tenant_abc123",
  "name": "Failed SMS today",
  "query": {
    "status": "FAILED",
    "channel": "SMS",
    "date_from": "2026-09-08T00:00:00Z"
  },
  "description": "All failed SMS notifications for today"
}
```

## 17. Tenant Communication Quotas

```
GET    /api/v1/communications/quotas
PUT    /api/v1/communications/quotas/{tenant_id}
```

### Response 200

```json
{
  "tenant_id": "tenant_abc123",
  "quotas": {
    "daily_sms": {
      "limit": 50000,
      "used": 32450,
      "remaining": 17550,
      "utilization_percent": 64.9
    },
    "monthly_sms": {
      "limit": 1500000,
      "used": 892340,
      "remaining": 607660,
      "utilization_percent": 59.5
    },
    "api_requests": {
      "limit": 1000000,
      "used": 452340,
      "remaining": 547660,
      "utilization_percent": 45.2
    }
  }
}
```

## 18. Feature Flags

```
GET    /api/v1/communications/flags
PUT    /api/v1/communications/flags/{flag_name}
```

### Response 200

```json
{
  "flags": {
    "AFRICASTALKING_SMS": true,
    "AFRICASTALKING_USSD": true,
    "AFRICASTALKING_VOICE": true,
    "AFRICASTALKING_WHATSAPP": true,
    "PROVIDER_FAILOVER": true,
    "SMART_ROUTING": true,
    "AI_COMMUNICATIONS": false,
    "CAMPAIGNS": true,
    "BULK_SMS": true
  }
}
```

## 19. API Logs (Observability)

```
GET /api/v1/communications/logs
```

Searchable API request logs with masked sensitive data.

### Query Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| tenant_id | string | Filter by tenant |
| endpoint | string | Filter by endpoint |
| method | string | HTTP method |
| status_code | integer | HTTP status code |
| provider | string | Provider used |
| date_from | string | Start date |
| date_to | string | End date |
| request_id | string | Request ID |

### Response 200

```json
{
  "data": [
    {
      "request_id": "req-789",
      "tenant_id": "tenant_abc123",
      "endpoint": "/api/v1/communications/notifications",
      "method": "POST",
      "status_code": 201,
      "latency_ms": 45,
      "provider": "africas_talking",
      "error": null,
      "timestamp": "2026-09-08T09:31:22.190Z",
      "ip_address": "192.168.1.100",
      "user_agent": "PesaGuard-Server/2.0"
    }
  ],
  "pagination": {
    "page": 1,
    "per_page": 25,
    "total_items": 8472,
    "total_pages": 339
  }
}
```

## 20. Webhook Management

```
GET    /api/v1/communications/webhooks
POST   /api/v1/communications/webhooks
PUT    /api/v1/communications/webhooks/{webhook_id}
DELETE /api/v1/communications/webhooks/{webhook_id}
POST   /api/v1/communications/webhooks/{webhook_id}/test
POST   /api/v1/communications/webhooks/{webhook_id}/rotate-secret
```

### Response 200 (GET)

```json
{
  "data": [
    {
      "webhook_id": "PG-WH-88234",
      "channel": "SMS",
      "provider": "africas_talking",
      "endpoint": "https://tenant.example.com/webhooks/africas-talking",
      "events": ["notification.delivered", "notification.failed"],
      "status": "ACTIVE",
      "last_delivery_at": "2026-09-08T09:32:04.850Z",
      "success_rate": 99.7,
      "failures_24h": 3,
      "secret_rotation_date": "2026-08-01"
    }
  ]
}
```

## 21. Webhook Event Subscriptions

```
GET    /api/v1/communications/subscriptions
POST   /api/v1/communications/subscriptions
DELETE /api/v1/communications/subscriptions/{subscription_id}
```

### Request (POST)

```json
{
  "tenant_id": "tenant_abc123",
  "events": [
    "notification.delivered",
    "notification.failed",
    "transaction.completed",
    "fraud.detected",
    "reconciliation.exception"
  ],
  "endpoint": "https://tenant.example.com/events",
  "secret": "whsec_abc123..."
}
```

## 22. Trace Viewer

```
GET /api/v1/communications/traces/{trace_id}
```

Full end-to-end trace for a message.

### Response 200

```json
{
  "trace_id": "trace-456",
  "correlation_id": "corr-789",
  "transactions": [
    {
      "step": "API Received",
      "component": "communications_api",
      "timestamp": "2026-09-08T09:31:22.145Z",
      "duration_ms": 2,
      "status": "OK"
    },
    {
      "step": "Policy Evaluation",
      "component": "policy_engine",
      "timestamp": "2026-09-08T09:31:22.147Z",
      "duration_ms": 3,
      "status": "OK",
      "result": {
        "channel": "SMS",
        "provider": "africas_talking",
        "priority": "NORMAL",
        "delay_ms": 0
      }
    },
    {
      "step": "Outbox Persisted",
      "component": "outbox",
      "timestamp": "2026-09-08T09:31:22.150Z",
      "duration_ms": 5,
      "status": "OK",
      "notification_id": "PG-NTF-98234-001"
    },
    {
      "step": "Kafka Published",
      "component": "kafka",
      "timestamp": "2026-09-08T09:31:22.155Z",
      "duration_ms": 8,
      "status": "OK",
      "topic": "pesaguard.communication.notifications"
    },
    {
      "step": "Worker Processed",
      "component": "notification_worker",
      "timestamp": "2026-09-08T09:31:22.164Z",
      "duration_ms": 12,
      "status": "OK"
    },
    {
      "step": "Provider Accepted",
      "component": "africas_talking",
      "timestamp": "2026-09-08T09:31:22.210Z",
      "duration_ms": 182,
      "status": "OK",
      "provider_message_id": "AT-18293041"
    },
    {
      "step": "Webhook Received",
      "component": "webhook_handler",
      "timestamp": "2026-09-08T09:32:04.850Z",
      "duration_ms": 15,
      "status": "OK",
      "inbox_event_id": "PG-INB-88234"
    },
    {
      "step": "Status Updated",
      "component": "worker",
      "timestamp": "2026-09-08T09:32:04.865Z",
      "duration_ms": 10,
      "status": "OK",
      "new_status": "DELIVERED"
    }
  ],
  "total_duration_ms": 42720,
  "steps": 8
}
```

## Developer Portal Endpoints

Additional endpoints for the developer portal:

```
POST   /api/v1/developer/api-keys
DELETE /api/v1/developer/api-keys/{key_id}
GET    /api/v1/developer/api-keys
GET    /api/v1/developer/usage
GET    /api/v1/developer/rate-limits
POST   /api/v1/developer/sandbox/send-test
GET    /api/v1/developer/sandbox/status
```
