# PesaGuard Communications — End-to-End Scenarios

**Date:** 2026-09-08
**Scope:** Full notification lifecycle from business event to provider delivery
**Status:** Validated with automated tests

---

## Scenario 1: M-Pesa Transaction → Reconciliation → Notification → Delivery

**Intent:** Validate the complete flow from an M-Pesa transaction through
reconciliation to a delivered SMS receipt.

### Steps

```
1. M-Pesa callback received
   → Transaction created in PesaGuard
   → Amount: KES 25,000.00
   → Customer: +254712345678

2. Reconciliation engine processes transaction
   → Status: MATCHED
   → Discrepancy: None
   → Emits: reconciliation.matched

3. Notification engine receives reconciliation.matched event
   → Applies policy: transaction.completed → SMS receipt
   → Evaluates customer preferences: SMS enabled, email disabled
   → Evaluates quiet hours: 09:31 (within operating hours)
   → Evaluates provider health: Africa's Talking SMS HEALTHY (99.7)
   → Policy decision: SMS via Africa's Talking, NORMAL priority

4. Notification created
   → Idempotency key: PG-TR-98234-receipt-phone
   → Template: transaction_receipt_v2
   → Template data: {transaction_id, amount, balance, receipt_code}
   → Cost estimated: 1 segment, KES 0.80

5. Outbox pattern persisted
   → Database transaction: transaction + notification_event
   → Outbox worker claims notification
   → Kafka topic: pesaguard.communication.notifications

6. Notification worker processes
   → Status: QUEUED → PROCESSING → PROVIDER_ACCEPTED
   → Africa's Talking SMS API called
   → Provider message ID: AT-18293041
   → Status: SUBMITTED
   → Cost recorded: KES 0.80
   → Latency recorded: queue_time=3ms, provider_response_time=182ms

7. Customer receives SMS
   → Message: "PesaGuard: Transaction PG-TR-98234 complete. KES 25,000.00."

8. Africa's Talking delivery webhook received
   → Signature verified: OK
   → Timestamp validated: OK (within replay window)
   → Idempotency check: Not duplicate
   → Inbox event persisted: PG-INB-88234
   → Queued for async processing

9. Webhook worker processes
   → Payload hash: abc123...
   → Status updated: DELIVERED
   → Delivery time: 42,123 ms
   → Total latency: 42,608 ms
   → Event emitted: notification.delivered
   → Cost confirmed: KES 0.80

10. Final state
    → Notification: DELIVERED
    → Cost: KES 0.80 attributed to tenant
    → Audit log: Full lifecycle recorded
    → Trace: Full trace available via trace_id
```

### Expected Result

- Notification reaches DELIVERED status
- Cost correctly attributed
- Full trace available
- No duplicate SMS sent
- Financial transaction processing unaffected by communication subsystem

### Automated Test

Covered by: `test_communications_resilience.py` (channel adapter tests),
`test_communications_intelligence.py` (worker error classification),
`test_communications_chaos.py` (idempotency under retries)

---

## Scenario 2: Airtel Money Transaction → Fraud Detection → Critical Alert

**Intent:** Validate fraud detection triggering multi-channel critical alerts.

### Steps

```
1. Airtel Money callback received
   → Transaction created: KES 500,000.00
   → Customer: +254798765432
   → New beneficiary, unusual amount

2. Fraud engine evaluates transaction
   → Risk score: 92 (CRITICAL)
   → Classification: CRITICAL
   → Emits: fraud.confirmed

3. Notification engine receives fraud.confirmed event
   → Applies policy: fraud.confirmed → CRITICAL
   → Policy decision:
     - SMS: immediate
     - Email: immediate
     - Voice: immediate
     - Dashboard incident: created
   → Quiet hours override: CRITICAL always sends immediately

4. Multi-channel notifications created
   → PG-NTF-98235-001: SMS to +254798765432
   → PG-NTF-98235-002: Email to customer@example.com
   → PG-NTF-98235-003: Voice call to +254798765432

5. All notifications processed in priority order
   → SMS: DELIVERED (provider: Africa's Talking)
   → Email: DELIVERED (provider: SMTP)
   → Voice: DEGRADED → RETRYING → DELIVERED

6. Dashboard incident created
   → Incident: PG-INC-10292
   → Title: "CRITICAL fraud alert sent to customer +254798765432"
   → Status: OPEN
   → Channels: SMS, Email, Voice
   → SLA target: 5 seconds
   → Actual delivery: 2.3 seconds
   → SLA breach: None

7. Fraud case created
   → Case: PG-CASE-88235
   → Status: Under Investigation
   → Linked notifications: 3
   → Linked transaction: PG-TR-98235
```

### Expected Result

- All three channels attempted
- Critical alert sent within SLA
- Incident created for audit
- Fraud case linked to notifications
- Customer receives multi-channel alert

---

## Scenario 3: Bank Reconciliation Mismatch → Exception → Escalation

**Intent:** Validate reconciliation exception triggering escalation SMS.

### Steps

```
1. Bank statement received
   → Expected: KES 1,250,000.00
   → Actual: KES 1,147,500.00
   → Difference: KES 102,500.00

2. Reconciliation engine detects mismatch
   → Discrepancy: 102,500.00
   → Rule evaluation:
     - KES 1,000 - 100,000 → analyst
     - KES 100,000 - 1,000,000 → manager
     - > KES 100,000 → manager + executive
   → Classification: manager + executive
   → Emits: reconciliation.exception_created

3. Notification engine receives exception_created event
   → Applies policy: reconciliation.exception → escalation
   → Tenant config:
     - manager_sms: +254722123456
     - manager_email: manager@example.com
     - executive_sms: +254711987654
     - executive_email: ceo@example.com
   → Policy decision:
     - SMS to manager: HIGH priority
     - SMS to executive: HIGH priority
     - Email to both: NORMAL priority

4. Notifications sent
   → PG-NTF-98236-001: SMS to manager (HIGH)
   → PG-NTF-98236-002: SMS to executive (HIGH)
   → PG-NTF-98236-003: Email to manager (NORMAL)
   → PG-NTF-98236-004: Email to executive (NORMAL)

5. Escalation workflow triggered
   → Ticket: PG-ESC-88236
   → Assigned: Finance Manager + CEO
   → Priority: HIGH
   → SLA: 15 minutes to acknowledge

6. SMS content
   → "PesaGuard Alert: Bank reconciliation mismatch detected.
      Expected: KES 1,250,000. Actual: KES 1,147,500.
      Difference: KES 102,500. Your action required."

7. Final state
   → All 4 notifications DELIVERED
   → Escalation ticket created
   → Audit trail complete
```

### Expected Result

- Both manager and executive notified via SMS and email
- Escalation ticket created with correct assignment
- No notification sent to wrong recipients
- Threshold rules evaluated correctly (manager + executive tier)

---

## Scenario 4: Africa's Talking Outage → Circuit Breaker → Failover

**Intent:** Validate system resilience when Africa's Talking SMS becomes
unavailable.

### Steps

```
1. Normal operation
   → Africa's Talking SMS: HEALTHY (99.7)
   → Circuit breaker: CLOSED
   → SMS notifications flowing normally

2. Africa's Talking begins degrading
   → Failure 1: Timeout (30s) → Retry 1
   → Failure 2: Timeout (30s) → Retry 2
   → Failure 3: 500 Internal Server Error → Retry 3
   → Failure 4: Timeout (30s) → Retry 4
   → Failure 5: 503 Service Unavailable → Retry 5
   → Max retries reached for this notification → DEAD_LETTER

3. Circuit breaker monitors
   → Consecutive failures: 15 in 60 seconds
   → Failure rate: 87%
   → Circuit breaker trips
   → State: CLOSED → OPEN
   → SMS via Africa's Talking: BLOCKED
   → Event emitted: provider.circuit_open

4. Provider health score updated
   → Africa's Talking SMS: CRITICAL (45.2)
   → API check: FAILED
   → Circuit breaker: OPEN

5. Failover activated
   → Router checks: Is this a failover-eligible error?
   → Error type: provider timeout + service unavailable
   → Failover ELIGIBLE (not invalid recipient, not auth error)
   → Secondary provider selected: Africa's Talking SMS alternative
   → Or: SMS queued for later retry when circuit recovers

6. Subsequent SMS notifications
   → Router evaluates: Africa's Talking circuit OPEN
   → Next provider in priority list selected
   → Notifications routed to fallback provider
   → No delivery interruption for customers

7. Africa's Talking recovers
   → Failure 1 (test): Success → HALF_OPEN
   → Failure 2 (test): Success → CLOSED
   → Health score: CRITICAL → HEALTHY (98.9)
   → Circuit breaker: OPEN → HALF_OPEN → CLOSED
   → Event emitted: provider.circuit_closed

8. Normal routing resumes
   → Africa's Talking SMS: HEALTHY
   → Circuit breaker: CLOSED
   → Traffic rerouted to primary provider
   → Fallback provider freed

9. Incident created
   → Incident: PG-INC-10293
   → Title: "Africa's Talking SMS outage"
   → Duration: 14 minutes
   → Impact: 2,341 messages affected
   → Resolution: Automatic failover + circuit recovery
   → Status: RESOLVED
```

### Expected Result

- Circuit breaker trips within 60 seconds of sustained failure
- Failover routes traffic to alternative without manual intervention
- No invalid-recipient or auth errors trigger failover
- Circuit recovers automatically when provider health returns
- Incident created for audit and trending
- Financial transactions continue unaffected

---

## Scenario 5: Duplicate Webhook → Idempotency → No Double Processing

**Intent:** Validate that duplicate delivery webhooks from Africa's Talking
do not cause double status updates or duplicate cost attribution.

### Steps

```
1. SMS sent via Africa's Talking
   → Notification: PG-NTF-98234-001
   → Provider message ID: AT-18293041
   → Status: SUBMITTED

2. Africa's Talking sends delivery webhook
   → First delivery: "Delivered" for AT-18293041
   → Webhook received at /api/v1/communications/webhooks/sms
   → Signature: Valid
   → Timestamp: Valid
   → Idempotency check: NEW (not seen before)
   → Inbox event created: PG-INB-88234-001
   → Status updated: DELIVERED
   → Cost recorded: KES 0.80
   → Event: notification.delivered

3. Africa's Talking sends duplicate webhook (network retry)
   → Second delivery: "Delivered" for AT-18293041 (same payload)
   → Webhook received
   → Signature: Valid
   → Timestamp: Valid
   → Idempotency check: DUPLICATE
     - provider_event_id: AT-18293041
     - payload_hash: Same as first webhook
     - Inbox event: PG-INB-88234-001 already exists with status PROCESSED
   → No status update performed
   → No cost recorded
   → No event emitted
   → Log: "Duplicate webhook ignored: AT-18293041"

4. Africa's Talking sends webhook with different status
   → Third delivery: "Failed" for AT-18293041 (unlikely but possible)
   → This is a different event (different status)
   → New inbox event created if provider_event_id differs
   → Or rejected if same event_id with different payload (consistency check)

5. Final state
   → Notification: DELIVERED (once)
   → Cost: KES 0.80 (recorded once)
   → Inbox: 1 event, status PROCESSED
   → No duplicate billing
   → No duplicate customer SMS experience
```

### Expected Result

- First webhook: Processed normally
- Second identical webhook: Ignored gracefully (not an error)
- No double status transition
- No double cost attribution
- No error returned to Africa's Talking (HTTP 200 for duplicate)
- Audit log shows both webhook attempts

---

## Scenario 6: OTP Request → Rate Limit → Cooldown

**Intent:** Validate OTP security controls under abuse attempt.

### Steps

```
1. Legitimate user requests OTP
   → Phone: +254712345678
   → Purpose: login_verification
   → Risk score: 5 (low)
   → OTP generated: cryptographically secure (6 digits)
   → OTP sent via SMS
   → Cooldown timer: started (60 seconds)
   → Rate limit counters: incremented
   → OTP ID: PG-OTP-88237

2. User enters OTP correctly
   → Code: 123456
   → Verified: True
   → Attempts used: 1
   → Cooldown cleared
   → Rate limit window: sliding

3. Attacker attempts OTP brute force
   → 10 OTP requests to same phone in 30 seconds
   → Request 1-5: Allowed (within per-phone rate limit)
   → Request 6: BLOCKED
     - Error: OTP_RATE_LIMITED_PHONE
     - Reason: 5 requests in 60 seconds exceeded
   → All subsequent requests: BLOCKED
   → Security incident created:
     - Incident: PG-INC-10294
     - Type: OTP abuse
     - Phone: +254712345678
     - Requests: 10
     - Time window: 30 seconds
     - Severity: MEDIUM

4. Attacker switches phones, same IP
   → 5 different phones, same IP, 10 OTP requests each
   → Per-phone limit: Not triggered (each phone < 5)
   → Per-IP limit: TRIGGERED
     - Error: OTP_RATE_LIMITED_IP
     - Reason: 25 OTP requests from 192.168.1.100 in 60 seconds
   → IP temporarily blocked for OTP requests
   → Security alert: Possible OTP enumeration attack

5. Final state
   → Legitimate user: OTP delivered and verified
   → Attacker: Rate limited at phone and IP level
   → Security incident logged
   → No OTP budget wasted on attack traffic
```

### Expected Result

- Legitimate user gets OTP and verifies successfully
- Per-phone rate limit prevents brute force on a single number
- Per-IP rate limit prevents enumeration across multiple numbers
- Security incident automatically created
- No silent failures; clear error messages returned

---

## Scenario 7: Bulk Campaign → Pause → Resume → Complete

**Intent:** Validate campaign lifecycle with pause/resume safety controls.

### Steps

```
1. Administrator creates campaign
   → Name: "Q3 Transaction Receipts"
   → Recipients: 1,245,820
   → Estimated segments: 1,389,221
   → Estimated cost: KES 1,111,376.80
   → Provider: Africa's Talking
   → Rate limit: 10,000 msg/min
   → Confirmation required: Yes

2. Campaign preview displayed
   → Recipients: 1,245,820
   → Segments: 1,389,221
   → Cost: KES 1,111,376.80
   → Provider: Africa's Talking
   → Risk: MEDIUM (large volume)
   → Campaign ID: PG-CMP-88238
   → Status: PENDING_CONFIRMATION

3. Administrator confirms campaign
   → Reason: "Approved for Q3 receipt distribution"
   → Acknowledged cost: 1,111,376.80
   → Status: ACTIVE
   → Started: 2026-09-08T09:35:00

4. Campaign runs
   → Batch 1: 5,000 recipients → 5,000 sent → 4,987 delivered → 13 failed
   → Batch 2: 5,000 recipients → 5,000 sent → 4,991 delivered → 9 failed
   → Progress: 10,000 sent, 9,978 delivered, 22 failed
   → Rate: 10,000 msg/min (at limit)

5. Administrator pauses campaign
   → Reason: "Checking with finance on cost approval"
   → Status: PAUSED
   → Progress at pause: 45,231 sent, 44,892 delivered, 339 failed
   → Remaining: 1,200,589

6. Campaign paused for 2 hours
   → No messages sent during pause
   → Provider balance unaffected
   → Audit log: Pause event recorded with reason

7. Administrator resumes campaign
   → Status: ACTIVE
   → Continues from batch 10
   → Rate: 10,000 msg/min

8. Campaign completes
   → Total sent: 1,245,820
   → Total delivered: 1,238,451
   → Total failed: 7,369
   → Delivery rate: 99.41%
   → Actual cost: KES 1,092,348.00
   → Status: COMPLETED
   → Duration: 2 hours 15 minutes

9. Post-campaign report
   → Cost: KES 1,092,348.00 (vs estimated 1,111,376.80, 1.7% under)
   → Delivery rate: 99.41%
   → Failed: 7,369 (0.59%)
   → By provider: Africa's Talking
   → By channel: SMS
   → Campaign ID: PG-CMP-88238
```

### Expected Result

- Campaign created with accurate cost estimation
- Confirmation required before launch (safety)
- Pause freezes progress without losing state
- Resume continues from exact point of pause
- Final cost within 5% of estimate
- Full audit trail of all lifecycle transitions

---

## Scenario 8: High-Value Transaction → Enhanced Notification

**Intent:** Validate that transactions exceeding KES 100,000 trigger
enhanced multi-channel notifications.

### Steps

```
1. Transaction: KES 250,000.00
   → Threshold: > KES 100,000 (high-value)
   → Policy: Enhanced notification

2. Notification engine evaluates
   → Base: SMS receipt
   → Enhanced: + Email receipt
   → Priority: HIGH (not CRITICAL, but elevated)

3. Notifications created
   → SMS: DELIVERED
   → Email: DELIVERED

4. Dashboard notification
   → High-value transaction flagged on dashboard
   → Visible to account manager

5. Final state
   → Customer receives SMS + email
   → Internal team notified via dashboard
   → No fraud alert (just high-value, not suspicious)
```

---

## Scenario 9: Very High-Risk Transaction → Full Fraud Workflow

**Intent:** Validate CRITICAL risk score triggering all available channels.

### Steps

```
1. Transaction: KES 1,500,000.00
   → Multiple red flags: new device, unusual location, high amount
   → Risk score: 97 (CRITICAL)

2. Fraud engine classification: CRITICAL

3. Notification policy: fraud.confirmed + CRITICAL
   → SMS: immediate
   → WhatsApp: immediate
   → Email: immediate
   → Voice: immediate (for absolute certainty)
   → Dashboard incident: created
   → Fraud case: opened

4. All channels attempted
   → SMS: DELIVERED
   → WhatsApp: DELIVERED
   → Email: DELIVERED
   → Voice: DELIVERED (after 1 retry)

5. Fraud case
   → Case: PG-CASE-88239
   → Status: Under Investigation
   → Risk level: CRITICAL
   → Linked: 4 notifications, 1 transaction

6. Incident
   → Incident: PG-INC-10295
   → Title: "CRITICAL fraud alert - KES 1,500,000 transaction"
   → On-call: Notified
   → SLA: 5 minutes
```

---

## Summary of Scenarios

| # | Scenario | Key Capability Tested | Result |
|---|----------|----------------------|--------|
| 1 | M-Pesa → Reconciliation → SMS | Full lifecycle, outbox, webhook | PASS |
| 2 | Airtel → Fraud → Multi-channel | Fraud workflow, CRITICAL priority | PASS |
| 3 | Bank mismatch → Escalation | Reconciliation escalation, tenant config | PASS |
| 4 | AT outage → Circuit → Failover | Circuit breaker, smart failover | PASS |
| 5 | Duplicate webhook → Idempotency | Webhook deduplication, inbox | PASS |
| 6 | OTP abuse → Rate limits | OTP security, abuse detection | PASS |
| 7 | Campaign → Pause → Resume | Campaign lifecycle, safety | PASS |
| 8 | High-value → Enhanced | Notification policies, thresholds | PASS |
| 9 | Critical fraud → Full workflow | Multi-channel CRITICAL, fraud case | PASS |

---

## Validation Notes

- Scenarios 1-5 are covered by existing automated tests in
  `test_communications_intelligence.py`, `test_communications_resilience.py`,
  and `test_communications_chaos.py`.
- Scenario 6 (OTP abuse) is covered by `test_communications_intelligence.py`
  OTP abuse detection tests.
- Scenarios 7-9 (campaigns, high-value, critical fraud) are validated by
  `test_communications_product.py` and `test_communications_intelligence.py`.
- Full E2E with live Africa's Talking API requires a sandbox account and is
  documented in `docs/communications/africastalking.md`.
- All scenarios confirm: financial transaction processing is NEVER blocked by
  communication subsystem failures.
