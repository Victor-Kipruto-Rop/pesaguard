# PesaGuard Advanced Features Documentation

## Overview

This document covers 8 advanced enterprise features implemented in PesaGuard 2.0, enabling sophisticated incident management, automation, and security.

---

## 1. Webhook Notifications for Escalations

### Purpose
Real-time event delivery to external systems when incidents escalate.

### Key Features
- **Event Types**: `escalation`, `resolution`, `assignment`, `sla_breach`
- **Retry Logic**: Exponential backoff (1s, 2s, 4s) up to configurable attempts
- **HMAC Signatures**: Secure webhook authenticity verification
- **Delivery Tracking**: Full history of webhook delivery attempts

### API Endpoints

#### Register Webhook
```bash
POST /webhooks
Authorization: Bearer {token}

{
  "tenant_id": "acme-corp",
  "url": "https://your-system.com/webhooks",
  "event_types": ["escalation", "resolution"],
  "retry_attempts": 3,
  "timeout_seconds": 10
}

Response:
{
  "id": "webhook_abc123",
  "tenant_id": "acme-corp",
  "url": "https://your-system.com/webhooks",
  "event_types": ["escalation", "resolution"],
  "active": true,
  "created_at": "2026-07-04T10:30:00Z"
}
```

#### List Webhooks
```bash
GET /webhooks?tenant_id=acme-corp
Authorization: Bearer {token}

Response:
{
  "tenant_id": "acme-corp",
  "webhooks": [
    {
      "id": "webhook_abc123",
      "url": "https://...",
      "event_types": ["escalation"],
      "active": true,
      "created_at": "..."
    }
  ]
}
```

#### Get Delivery History
```bash
GET /webhooks/{webhook_id}/deliveries?limit=50
Authorization: Bearer {token}

Response:
{
  "webhook_id": "webhook_abc123",
  "deliveries": [
    {
      "id": "delivery_xyz789",
      "event_type": "escalation",
      "status": "success",
      "attempt_count": 1,
      "response_status": 200,
      "created_at": "2026-07-04T11:15:00Z",
      "delivered_at": "2026-07-04T11:15:01Z"
    }
  ]
}
```

### Webhook Payload Structure
```json
{
  "event_type": "escalation",
  "incident_id": "inc_abc123",
  "trans_id": "TX123456",
  "severity": "critical",
  "anomaly_type": "double_charge",
  "assigned_to": "senior_operator",
  "rule_applied": "Critical Severity Escalation",
  "timestamp": "2026-07-04T11:15:00Z"
}
```

---

## 2. Email Distribution of Reconciliation Reports

### Purpose
Automated email delivery of reconciliation reports and daily summaries.

### Key Features
- **Report Types**: Reconciliation, Daily Summary, Escalation Notifications
- **HTML Templates**: Professional pre-formatted emails
- **Status Tracking**: Sent/Failed/Pending states
- **Batch Distribution**: Multiple recipients per report

### API Endpoints

#### Send Reconciliation Report
```bash
POST /emails/reconciliation
Authorization: Bearer {token}

{
  "tenant_id": "acme-corp",
  "recipient_email": "manager@acme.com",
  "report_data": {
    "total_discrepancies": 42,
    "resolved": 38,
    "pending": 4,
    "sla_compliance": 95,
    "avg_resolution_time": 15
  }
}

Response:
{
  "id": "email_rec123",
  "status": "sent",
  "recipient": "manager@acme.com",
  "report_type": "reconciliation",
  "sent_at": "2026-07-04T10:30:00Z"
}
```

#### Send Escalation Notification
```bash
POST /emails/escalation
Authorization: Bearer {token}

{
  "tenant_id": "acme-corp",
  "recipient_email": "senior@acme.com",
  "incident_data": {
    "anomaly_type": "double_charge",
    "severity": "critical",
    "amount": 5000,
    "trans_id": "TX123456",
    "detected_at": "2026-07-04T10:15:00Z"
  }
}
```

#### Get Email History
```bash
GET /emails/history?tenant_id=acme-corp&limit=50
Authorization: Bearer {token}

Response:
{
  "tenant_id": "acme-corp",
  "emails": [
    {
      "id": "email_rec123",
      "recipient": "manager@acme.com",
      "report_type": "reconciliation",
      "status": "sent",
      "created_at": "2026-07-04T10:30:00Z",
      "sent_at": "2026-07-04T10:30:05Z"
    }
  ]
}
```

### Configuration
Set environment variables:
```bash
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_FROM_EMAIL=noreply@pesaguard.com
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
```

---

## 3. Custom Escalation Rules Per Tenant

### Purpose
Define tenant-specific workflows for automatic incident escalation.

### Key Features
- **Condition-Based Triggers**: severity, anomaly_type, age, status
- **Flexible Actions**: escalate, notify, webhook
- **Priority Ordering**: Higher priority rules execute first
- **Per-Tenant Configuration**: Isolated rules per tenant

### API Endpoints

#### Create Escalation Rule
```bash
POST /escalation-rules
Authorization: Bearer {token}

{
  "tenant_id": "acme-corp",
  "name": "Critical Severity Escalation",
  "description": "Auto-escalate critical incidents to senior ops",
  "condition_field": "severity",
  "condition_operator": "equals",
  "condition_value": "critical",
  "action": "escalate",
  "target": "senior_operator",
  "priority": 10
}

Response:
{
  "id": "rule_abc123",
  "tenant_id": "acme-corp",
  "name": "Critical Severity Escalation",
  "condition_field": "severity",
  "condition_operator": "equals",
  "condition_value": "critical",
  "action": "escalate",
  "target": "senior_operator",
  "active": true,
  "priority": 10,
  "created_at": "2026-07-04T10:30:00Z"
}
```

#### List Escalation Rules
```bash
GET /escalation-rules?tenant_id=acme-corp
Authorization: Bearer {token}

Response:
{
  "tenant_id": "acme-corp",
  "rules": [
    {
      "id": "rule_abc123",
      "name": "Critical Severity Escalation",
      "condition_field": "severity",
      "condition_operator": "equals",
      "condition_value": "critical",
      "action": "escalate",
      "priority": 10
    }
  ]
}
```

#### Update Rule
```bash
PUT /escalation-rules/{rule_id}
Authorization: Bearer {token}

{
  "active": false,
  "priority": 5
}
```

### Supported Operators
- `equals`: Exact match
- `not_equals`: Not matching value
- `greater_than`: Greater than (for numeric fields)
- `less_than`: Less than (for numeric fields)
- `contains`: Substring match
- `in`: Within list

### Example Rules

**Rule 1: Age-Based Escalation**
```json
{
  "condition_field": "age",
  "condition_operator": "greater_than",
  "condition_value": "30",
  "action": "escalate",
  "description": "Escalate incidents older than 30 minutes"
}
```

**Rule 2: Anomaly Type Webhook**
```json
{
  "condition_field": "anomaly_type",
  "condition_operator": "equals",
  "condition_value": "triple_charge",
  "action": "webhook",
  "webhook_url": "https://fraud-system.com/alert"
}
```

---

## 4. Operator On-Call Rotation Tracking

### Purpose
Manage and track operator schedules with automatic on-call assignment.

### Key Features
- **Shift Management**: Define start/end times per operator
- **Escalation Levels**: Primary, secondary, tertiary on-call tiers
- **Active Status**: Automatic activation based on current time
- **Coverage Status**: View current coverage and upcoming shifts
- **Bulk Operations**: Create multiple rotations at once

### API Endpoints

#### Create On-Call Rotation
```bash
POST /on-call/rotations
Authorization: Bearer {token}

{
  "tenant_id": "acme-corp",
  "operator_id": "op_001",
  "operator_name": "John Operator",
  "operator_email": "john@acme.com",
  "operator_phone": "+254712345678",
  "shift_start": "2026-07-04T08:00:00Z",
  "shift_end": "2026-07-04T16:00:00Z",
  "escalation_level": 1
}

Response:
{
  "id": "rotation_abc123",
  "tenant_id": "acme-corp",
  "operator_id": "op_001",
  "operator_name": "John Operator",
  "shift_start": "2026-07-04T08:00:00Z",
  "shift_end": "2026-07-04T16:00:00Z",
  "is_active": true,
  "escalation_level": 1,
  "created_at": "2026-07-04T07:55:00Z"
}
```

#### Get Active On-Call Coverage
```bash
GET /on-call/rotations/active?tenant_id=acme-corp
Authorization: Bearer {token}

Response:
{
  "tenant_id": "acme-corp",
  "coverage": {
    "currently_covered": true,
    "active_operators": 2,
    "coverage_by_level": {
      "1": [
        {"operator_id": "op_001", "operator_name": "John Operator"}
      ],
      "2": [
        {"operator_id": "op_002", "operator_name": "Jane Manager"}
      ]
    },
    "upcoming_shifts": 5,
    "next_shift": {...}
  },
  "active_rotations": [...]
}
```

#### Get Operator Schedule
```bash
GET /on-call/schedule/{operator_id}?tenant_id=acme-corp&days=30
Authorization: Bearer {token}

Response:
{
  "operator_id": "op_001",
  "tenant_id": "acme-corp",
  "days": 30,
  "schedule": [
    {
      "id": "rotation_abc123",
      "shift_start": "2026-07-04T08:00:00Z",
      "shift_end": "2026-07-04T16:00:00Z",
      "escalation_level": 1
    },
    ...
  ]
}
```

#### Bulk Create Rotations
```bash
POST /on-call/bulk
Authorization: Bearer {token}

{
  "tenant_id": "acme-corp",
  "rotations": [
    {
      "operator_id": "op_001",
      "operator_name": "John Operator",
      "operator_email": "john@acme.com",
      "operator_phone": "+254712345678",
      "shift_start": "2026-07-04T08:00:00Z",
      "shift_end": "2026-07-04T16:00:00Z",
      "escalation_level": 1
    },
    {
      "operator_id": "op_002",
      "shift_start": "2026-07-04T16:00:00Z",
      "shift_end": "2026-07-05T00:00:00Z",
      "escalation_level": 1
    }
  ]
}

Response:
{
  "created": 2,
  "errors": 0,
  "rotations": [...]
}
```

---

## 5. Historical Trend Charts on Dashboard

### Purpose
Visualize incident trends, patterns, and performance metrics over time.

### Features
- **7-Day Trending**: Historical incident volume
- **Peak Analysis**: Identify high-incident periods
- **SLA Metrics**: Compliance tracking
- **Resolution Efficiency**: Trend analysis
- **Responsive Visualization**: Mobile-friendly charts

### Dashboard Display

The dashboard now shows:
```
Historical Trends & Insights
┌──────────────────┬──────────────────┬──────────────────┬──────────────────┐
│ 7-day Average    │ Incident Peak    │ Resolution       │ SLA Compliance   │
│ Incidents        │ Hour             │ Efficiency       │                  │
│                  │                  │                  │                  │
│ 24               │ 3:00 PM          │ 94%              │ 92%              │
│ ↓ 12% prev week  │ 34 txn/min avg   │ ↑ 8% this month  │ Critical only    │
└──────────────────┴──────────────────┴──────────────────┴──────────────────┘
```

### Data Points Tracked
- Total incidents per day
- Resolved incidents per day
- Average resolution time
- SLA compliance percentage
- Peak transaction times
- Operator efficiency metrics

---

## 6. Advanced Search with Boolean Operators

### Purpose
Powerful incident search using boolean logic and field-based filtering.

### Key Features
- **Boolean Operators**: AND, OR, NOT
- **Field Filtering**: severity, status, anomaly_type, age, assignee
- **Free-Text Search**: Multi-field text searching
- **Structured Filters**: Dropdown-based filtering
- **Search Presets**: Save and reuse search queries

### API Endpoints

#### Boolean Search
```bash
GET /search?tenant_id=acme-corp&q=severity:critical%20AND%20status:open
Authorization: Bearer {token}

# Supported query syntax:
# severity:critical
# status:open
# anomaly_type:double_charge
# resolved:true
# age>30 (older than 30 minutes)
# assignee:john_operator
# trans_id:TX123456
# free text search

Response:
{
  "query": "severity:critical AND status:open",
  "total": 12,
  "results": [
    {
      "id": "inc_123",
      "trans_id": "TX123456",
      "anomaly_type": "double_charge",
      "severity": "critical",
      "status": "open",
      "resolved": false,
      "assignee": "john",
      "detected_at": "2026-07-04T10:15:00Z"
    }
  ],
  "parsed": {
    "conditions": [
      {"type": "field", "field": "severity", "operator": ":", "value": "critical"},
      {"type": "field", "field": "status", "operator": ":", "value": "open"}
    ]
  }
}
```

#### Structured Search
```bash
GET /search/structured?tenant_id=acme-corp&severity=critical&status=open&limit=25
Authorization: Bearer {token}

Response:
{
  "total": 12,
  "limit": 25,
  "offset": 0,
  "filters": {
    "severity": "critical",
    "status": "open",
    "anomaly_type": null,
    "resolved": null,
    "assignee": null,
    "days_back": 30
  },
  "results": [...]
}
```

#### Get Available Filters
```bash
GET /search/filters?tenant_id=acme-corp
Authorization: Bearer {token}

Response:
{
  "tenant_id": "acme-corp",
  "available_filters": {
    "severities": ["critical", "warning", "info"],
    "statuses": ["needs_review", "in_progress", "resolved"],
    "anomaly_types": ["double_charge", "triple_charge", "timeout"],
    "assignees": ["john_operator", "jane_manager", "unassigned"]
  }
}
```

### Query Examples

```bash
# Critical incidents that are still open
/search?q=severity:critical%20AND%20status:open

# All double charges except those assigned to john
/search?q=anomaly_type:double_charge%20NOT%20assignee:john

# Incidents older than 1 hour
/search?q=age%3E60

# Either critical or warning severity
/search?q=severity:critical%20OR%20severity:warning

# Unresolved incidents in specific transaction
/search?q=trans_id:TX123456%20AND%20resolved:false
```

---

## 7. Rate Limiting on Bulk Operations

### Purpose
Prevent abuse and ensure fair resource usage with token bucket rate limiting.

### Key Features
- **Token Bucket Algorithm**: Fair rate limiting
- **Per-User Limits**: Individual rate limits per user
- **Exponential Backoff**: Suggested retry timing
- **Rate Limit Headers**: Standard HTTP rate limit headers

### Configuration
```python
@rate_limit(
    max_requests_per_minute=5,      # Default: 5 requests/min
    tokens_per_request=1,            # Cost per request
    endpoint_name="bulk_assign"
)
```

### Rate-Limited Endpoints
- `/bulk/assign` - 5 req/min (1 token each)
- `/bulk/escalate` - 3 req/min (2 tokens each)

### Response Headers
```
X-RateLimit-Limit: 5
X-RateLimit-Remaining: 3
X-RateLimit-Reset: 1625445600
```

### Rate Limit Exceeded Response
```
HTTP/1.1 429 Too Many Requests

{
  "error": "rate_limit_exceeded",
  "retry_after": 12
}

Headers:
Retry-After: 12
```

### Usage Example
```bash
# First request succeeds
POST /bulk/assign
→ 200 OK
→ Rate-Limit-Remaining: 4

# Multiple requests within time window
POST /bulk/assign (request 5)
→ 200 OK
→ Rate-Limit-Remaining: 0

# Next request hits limit
POST /bulk/assign (request 6)
→ 429 Too Many Requests
→ Retry-After: 12
```

---

## 8. API Authentication & RBAC

### Purpose
Secure API endpoints with JWT authentication and role-based access control.

### Key Features
- **JWT Tokens**: 24-hour expiry
- **Role-Based Access**: admin, operator, viewer
- **Fine-Grained Permissions**: 15+ permission types
- **Tenant Isolation**: Per-tenant data access
- **Token Verification**: Validate and verify tokens

### Permission Matrix

| Role | Permissions |
|------|-------------|
| **admin** | All permissions (read/write everything) |
| **operator** | Read discrepancies, write updates, bulk operations |
| **viewer** | Read-only access to incidents and analytics |

### Permissions List
```
read:discrepancies
write:discrepancies
delete:discrepancies
read:analytics
write:escalation_rules
manage:webhooks
manage:users
manage:on_call
manage:settings
bulk:operations
```

### API Endpoints

#### Generate Token (Login)
```bash
POST /auth/login

{
  "username": "john_operator",
  "password": "secure_password",
  "tenant_id": "acme-corp"
}

Response:
{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user_id": "user_john_operator",
  "username": "john_operator",
  "tenant_id": "acme-corp",
  "roles": ["operator"],
  "expires_in": 86400
}
```

#### Verify Token
```bash
GET /auth/verify
Authorization: Bearer {token}

Response:
{
  "user_id": "user_john_operator",
  "username": "john_operator",
  "tenant_id": "acme-corp",
  "roles": ["operator"],
  "permissions": [
    "read:discrepancies",
    "write:discrepancies",
    "bulk:operations"
  ]
}
```

### Using Tokens

#### Request with Token
```bash
curl -H "Authorization: Bearer eyJhbGci..." \
  http://localhost:5002/discrepancies?tenant_id=acme-corp
```

#### Missing Token
```
HTTP/1.1 401 Unauthorized

{
  "error": "missing_auth_header"
}
```

#### Invalid Token
```
HTTP/1.1 401 Unauthorized

{
  "error": "invalid_token"
}
```

#### Insufficient Permissions
```
HTTP/1.1 403 Forbidden

{
  "error": "insufficient_permissions"
}
```

### Environment Variables
```bash
JWT_SECRET_KEY=your-secret-key-change-in-production
JWT_EXPIRY_HOURS=24
```

---

## Integration Guide

### Setting Up Webhooks + Escalation Rules

```python
from webhook_manager import WebhookManager
from escalation_engine import EscalationEngine
from sqlalchemy.orm import Session

# Register webhook
webhook_mgr = WebhookManager(session)
webhook = webhook_mgr.register_webhook(
    tenant_id="acme-corp",
    url="https://your-system.com/webhooks",
    event_types=["escalation", "sla_breach"]
)

# Create escalation rule
engine = EscalationEngine(session)
rule = engine.create_rule(
    tenant_id="acme-corp",
    name="Critical Incidents",
    condition_field="severity",
    condition_operator="equals",
    condition_value="critical",
    action="webhook",
    webhook_url="https://your-system.com/alerts"
)

# When an incident escalates:
# 1. EscalationEngine evaluates rules
# 2. If matched, triggers webhook
# 3. WebhookManager delivers with retries
# 4. EmailService sends notifications
```

### Complete Workflow Example

```python
# 1. Authenticate
token = AuthRBAC.generate_token(
    user_id="user_123",
    username="john",
    tenant_id="acme-corp",
    roles=["admin"]
)

# 2. Create on-call rotations for next month
rotations = OnCallService(session).bulk_create_rotations(
    tenant_id="acme-corp",
    rotations_data=[...]
)

# 3. Set up escalation rules
EscalationEngine(session).create_rule(...)

# 4. Register webhook for incident updates
WebhookManager(session).register_webhook(...)

# 5. Search for specific incidents
results = AdvancedSearchEngine(session).search(
    tenant_id="acme-corp",
    query="severity:critical AND status:open"
)

# 6. Bulk escalate with rate limiting
POST /bulk/escalate
→ Escalation engine evaluates all rules
→ Matching incidents escalated to on-call
→ Webhooks triggered for external systems
→ Emails sent to operators
```

---

## Performance Considerations

### Database Indexes
Create indexes for faster queries:
```sql
CREATE INDEX idx_escalation_tenant ON escalation_rules(tenant_id);
CREATE INDEX idx_on_call_tenant_shift ON on_call_rotations(tenant_id, shift_start, shift_end);
CREATE INDEX idx_email_notification_status ON email_notifications(tenant_id, status);
CREATE INDEX idx_webhook_delivery_webhook_id ON webhook_deliveries(webhook_id);
```

### Rate Limiting Tuning
Adjust based on your needs:
```python
# Conservative (high security)
rate_limit(max_requests_per_minute=3)

# Moderate (default)
rate_limit(max_requests_per_minute=10)

# Aggressive (high throughput)
rate_limit(max_requests_per_minute=100)
```

### Email Sending
For high volume:
```python
# Use async email queue
# Configure batch sending
# Implement retry schedule
# Monitor SMTP connection pooling
```

---

## Troubleshooting

### Webhooks Not Delivering
1. Check webhook URL is accessible
2. Verify event types are registered
3. Check delivery history for errors
4. Review network logs for timeout issues

### On-Call Auto-Assignment Not Working
1. Verify shift times are in UTC
2. Check escalation_level matches rules
3. Ensure operator_id matches rule targets
4. Review logs for condition evaluation

### Rate Limit Blocking
1. Check X-RateLimit-Remaining header
2. Wait suggested Retry-After seconds
3. Increase batch size (not requests)
4. Contact admin for limit increase

### Search Not Finding Results
1. Verify tenant_id is correct
2. Check query syntax (AND/OR/NOT capitalized)
3. Try structured search as alternative
4. Review available filters
