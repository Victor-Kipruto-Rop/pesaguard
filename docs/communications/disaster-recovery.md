# PesaGuard Communications \u2014 Disaster Recovery

**Version:** 1.0.0
**Last Updated:** 2026-09-08
**Owner:** PesaGuard Platform Team
**Classification:** Internal \u2014 Operational

---

## Purpose

This document defines the disaster recovery procedures for the PesaGuard
communications subsystem. Communications are a critical supporting service:
they must degrade gracefully without impacting core financial transaction
processing, reconciliation, fraud detection, or payout systems.

The guiding principle of PesaGuard disaster recovery is:

> **Financial integrity always takes priority over communication delivery.**

---

## 1. Recovery Objectives

| Objective | Target | Reason |
|-----------|--------|--------|
| RPO (Recovery Point Objective) | 5 minutes | Communication events are streamed through Kafka; the outbox pattern ensures no lost events. |
| RTO \u2014 Communications | 15 minutes | The communications subsystem is stateless relative to core banking. Recovery involves restarting workers, reconnecting Kafka consumers, and verifying provider connectivity. |
| RTO \u2014 Core Financial Systems | 0 minutes (never down) | Core transaction processing, reconciliation, fraud detection, and payouts must never stop due to a communications failure. |
| Backup Frequency | Every 6 hours (full), continuous WAL | Communication data must be recoverable to within 5 minutes of any failure. |
| Backup Retention | 30 days (daily), 90 days (weekly), 12 months (monthly) | Retention aligns with Kenyan financial regulations and internal audit requirements. |

---

## 2. Disaster Scenarios and Procedures

### 2.1 Africa\'s Talking Outage

**Severity:** HIGH
**Impact:** SMS and USSD delivery interrupted.
**Financial Impact:** NONE.

#### Detection

- Provider health score drops below 80
- Circuit breaker trips to OPEN state
- Alert: `pg-comm-provider-at-sms-degraded`

#### Immediate Actions (0\u20135 minutes)

1. **Do NOT restart Africa\'s Talking integration.** The circuit breaker is protecting the system.

2. **Verify circuit breaker state:**

   ```bash
   curl -s https://api.pesaguard.internal/api/v1/communications/providers/africas_talking/health | jq .channels.SMS.circuit_breaker
   ```
   Expected: `OPEN`

3. **Confirm failover routing is active:**

   ```bash
   curl -s https://api.pesaguard.internal/api/v1/communications/providers/africas_talking/health | jq .channels.SMS.status
   ```
   Expected: `CRITICAL` or `DEGRADED`

4. **Check notification queue depth:**

   ```bash
   curl -s https://api.pesaguard.internal/api/v1/communications/queues/status | jq
   ```
   If growing, scale up notification workers.

#### Short-Term Actions (5\u201330 minutes)

5. Monitor Africa\'s Talking status page at `status.africastalking.com`.

6. If failover is configured: verify secondary provider is healthy.

7. If no failover: queue will grow. Notify on-call.

8. Create or update incident:

   ```bash
   POST /api/v1/communications/incidents
   { "title": "Africa\'s Talking SMS outage", "severity": "HIGH", "status": "INVESTIGATING" }
   ```

#### Recovery (when Africa\'s Talking recovers)

9. Africa\'s Talking test requests through HALF_OPEN will succeed, transitioning circuit to CLOSED.

10. Verify recovery:

    ```bash
    curl -s https://api.pesaguard.internal/api/v1/communications/providers/africas_talking/health | jq .channels.SMS
    ```
    Expected: `status: HEALTHY`, `circuit_breaker: CLOSED`

11. Update incident to RESOLVED with duration and impact summary.

#### Force Failback (if needed)

```bash
PUT /api/v1/communications/providers/africas_talking/circuit
{ "state": "CLOSED", "force": true }
```
Use only with explicit approval.

---

### 2.2 Database Outage

**Severity:** CRITICAL
**Impact:** All communication data writes stop.
**Financial Impact:** NONE for core transactions.

#### Detection

- Database connection errors in logs
- Health check: `GET /health` returns `database: DOWN`
- Alert: `pg-db-communications-unavailable`

#### Immediate Actions (0\u20135 minutes)

1. Verify database is actually down:

   ```bash
   pg_isready -h db-primary.internal -p 5432
   ```

2. Core PesaGuard transaction processing should continue independently.

3. Communications API returns 503 for write endpoints. Read-only endpoints may still work.

4. Notification workers pause until database is available.

#### Recovery (when database recovers)

5. Verify database health:

   ```bash
   pg_isready -h db-primary.internal -p 5432
   psql -h db-primary.internal -U pesaguard -d pesaguard -c "SELECT 1"
   ```

6. Restart notification workers if not auto-recovered:

   ```bash
   systemctl restart pesaguard-comm-workers
   ```

7. Drain the outbox queue. Notifications published to Kafka during outage will be picked up.

8. Verify no data loss:

   ```sql
   SELECT COUNT(*) FROM notifications WHERE created_at > NOW() - INTERVAL \'15 minutes\';
   ```

9. Check Kafka lag:

   ```bash
   kafka-consumer-groups --bootstrap-server kafka:9092 --describe --group pesaguard-comm-workers
   ```

#### Database Recovery from Backup

If severe corruption or loss:

10. Stop all writers.

11. Identify last known good backup:

    ```bash
    ls -lt /backups/pesaguard/database/ | head -5
    ```

12. Restore to a point within RPO (5 minutes):

    ```bash
    pg_restore -h db-primary.internal -U pesaguard -d pesaguard \
      /backups/pesaguard/database/backup-2026-09-08-0600.dump
    ```

13. Validate restored data:

    ```sql
    SELECT COUNT(*) FROM notifications;
    SELECT MAX(created_at) FROM notifications;
    ```

14. Restart all services and verify end-to-end with a test notification.

---

### 2.3 Redis Outage

**Severity:** MEDIUM
**Impact:** Rate limiting, circuit breaker state, caching affected.
**Financial Impact:** NONE.

#### Impact Assessment

| Feature | Impact if Redis Down |
|---------|---------------------|
| Rate limiting | May be bypassed (fail-open or fail-closed per config) |
| Circuit breaker state | In-memory fallback; state not shared across instances |
| Caching | Cache misses increase DB load |
| Queue (if Redis-based) | Queue operations fail |

#### Recovery

1. Restart Redis:

   ```bash
   systemctl restart redis
   redis-cli -h redis.internal ping
   ```

2. Restart notification workers to re-establish connections.

3. Verify queue processing resumed.

---

### 2.4 Kafka Outage

**Severity:** HIGH
**Impact:** Outbox-to-worker event pipeline interrupted.
**Financial Impact:** NONE. Outbox pattern ensures notifications are not lost.

#### Impact

| Component | Impact |
|-----------|--------|
| Outbox writer | Can still write to database |
| Outbox publisher to Kafka | Fails to publish; events stay in outbox |
| Notification workers | No new messages to consume |
| In-flight notifications | Unaffected |

#### Recovery

1. Verify Kafka is down:

   ```bash
   kafka-broker-api-versions --bootstrap-server kafka:9092
   ```

2. Outbox events accumulate in database. This is expected and safe.

3. Restart Kafka brokers if needed:

   ```bash
   systemctl restart kafka
   ```

4. Restart outbox publisher:

   ```bash
   systemctl restart pesaguard-outbox-publisher
   ```

5. Monitor outbox drain:

   ```sql
   SELECT COUNT(*) FROM outbox_events WHERE processed = false;
   ```

6. Restart notification workers if needed.

#### Kafka Data Recovery

If Kafka data loss occurs, outbox is the source of truth:

```bash
pesaguard-outbox-publisher --recovery --since 2026-09-08T09:00:00
```

---

### 2.5 Worker Failure

**Severity:** MEDIUM
**Impact:** Notification processing stops on failed worker only.
**Financial Impact:** NONE.

#### Recovery

1. Check if worker restarted automatically (supervisor, systemd, Kubernetes).

2. If not: manually restart:

   ```bash
   systemctl restart pesaguard-comm-workers
   ```

3. Verify worker rejoined consumer group:

   ```bash
   kafka-consumer-groups --bootstrap-server kafka:9092 --describe --group pesaguard-comm-workers
   ```

4. Check for locked notifications with expired leases:

   ```sql
   SELECT COUNT(*) FROM notifications
   WHERE status = \'PROCESSING\' AND locked_at < NOW() - INTERVAL \'30 seconds\';
   ```

---

### 2.6 Webhook Endpoint Outage

**Severity:** MEDIUM
**Impact:** Delivery webhooks cannot be received. Status updates delayed.
**Financial Impact:** NONE.

#### Recovery

1. Check webhook endpoint health:

   ```bash
   curl -s https://api.pesaguard.internal/api/v1/health/webhooks
   ```

2. Restart webhook service if down:

   ```bash
   systemctl restart pesaguard-webhook-handler
   ```

3. For lost webhooks (Africa\'s Talking gave up retrying), use replay system:

   ```bash
   POST /api/v1/communications/webhooks/replay
   { "provider": "africas_talking", "channel": "SMS", "from": "2026-09-08T09:00:00" }
   ```

---

### 2.7 Network Failure

**Severity:** MEDIUM to HIGH
**Impact:** Depends on scope.

#### Recovery

1. Identify scope: communications only or broader?

   ```bash
   curl -s https://api.pesaguard.internal/api/v1/health | jq
   ```

2. If communications isolated: core transactions should continue.

3. Restore network connectivity per standard network operations procedures.

4. Once restored, verify all dependencies and drain backlogged queues.

---

### 2.8 Credential Rotation (API Key Compromised)

**Severity:** CRITICAL
**Impact:** Unauthorized SMS usage potential.

#### Immediate Actions (0\u20135 minutes)

1. Rotate Africa\'s Talking API key at `https://account.africastalking.com`.

2. Update PesaGuard configuration:

   ```bash
   PUT /api/v1/communications/providers/africas_talking/credentials
   { "api_key": "new_api_key_here", "rotated_by": "ops-oncall-01", "reason": "Credential compromise" }
   ```

3. Restart services:

   ```bash
   systemctl restart pesaguard-comm-workers pesaguard-comm-api
   ```

4. Verify new credentials:

   ```bash
   curl -s https://api.pesaguard.internal/api/v1/communications/providers/africas_talking/health
   ```
   Expected: `status: HEALTHY`

#### Post-Incident

5. Audit trail:

   ```bash
   GET /api/v1/communications/audit/credentials?provider=africas_talking
   ```

6. File incident report with detection time, rotation time, estimated unauthorized usage.

7. Review access controls.

8. Notify Africa\'s Talking support if financial loss occurred.

---

## 3. Backup and Restore Procedures

### 3.1 Database Backups

| Backup Type | Frequency | Retention | Location |
|-------------|-----------|-----------|----------|
| Full dump (pg_dump) | Every 6 hours | 30 days | `/backups/pesaguard/database/` |
| WAL archiving | Continuous | 7 days | `/backups/pesaguard/wal/` |
| Weekly full + WAL | Every Sunday 00:00 | 90 days | `/backups/pesaguard/database/weekly/` |
| Monthly archive | 1st of month | 12 months | Offsite storage |

**Backup Verification (weekly):**

```bash
pg_restore --list /backups/pesaguard/database/backup-latest.dump > /dev/null
echo "Backup integrity: OK"
```

**Point-in-Time Recovery Test (monthly):**

```bash
pg_restore -h test-db.internal -U pesaguard_test \
  /backups/pesaguard/database/backup-2026-09-01-0000.dump
psql -h test-db.internal -U pesaguard_test -d pesaguard_test \
  -c "SELECT COUNT(*) FROM notifications WHERE created_at > \'2026-09-01\'"
```

### 3.2 Redis Backups

RDB snapshots every 5 minutes:

```bash
redis-cli -h redis.internal BGSAVE
ls -lt /var/lib/redis/dump.rdb
```

### 3.3 Kafka Data

| Topic | Retention | Replication |
|-------|-----------|-------------|
| `pesaguard.communication.notifications` | 24 hours | 3 |
| `pesaguard.communication.webhooks` | 7 days | 3 |
| `pesaguard.communication.outbox` | 7 days | 3 |
| `pesaguard.communication.events` | 30 days | 3 |

---

## 4. Failover Architecture

### 4.1 Provider Failover

**Failover triggers:**
- Circuit breaker OPEN
- Provider health score below 50
- Repeated timeouts (3+ consecutive)
- 503 responses

**Failover exclusions (do NOT fail over):**
- Invalid recipient / phone number
- Authentication errors
- Invalid template
- Rate limiting (429) \u2014 retry instead

**Failover priority (configurable):**
1. Africa\'s Talking (primary)
2. Secondary Provider
3. Emergency Provider

### 4.2 Channel Failover

If a channel is unavailable, the policy engine may select an alternative channel
based on priority and customer preferences.

### 4.3 Region Failover

For multi-region deployments, traffic should fail over to a secondary region.
Requires multi-region Kafka, database replication, and provider accounts in both
regions.

---

## 5. Communication vs Core Financial Processing Isolation

**This is the most important disaster recovery guarantee of PesaGuard.**

The communications subsystem is architecturally isolated from core financial
processing:

```
Financial Transaction Processing
  (M-Pesa, Airtel, Bank, Reconciliation, Fraud)
           |
           v
    Event Bus (Kafka)
           |
           +---> [Independent] ---> Communication Router ---> Providers
           |
           +---> [Independent] ---> Reconciliation Engine
           |
           +---> [Independent] ---> Fraud Engine
           |
           +---> [Independent] ---> Analytics
```

**If communications is completely down:**
- Transactions are still ingested
- Reconciliation still runs
- Fraud detection still evaluates
- Payouts still process
- The only impact: customers do not receive notifications until communications recovers

**This is by design.** The outbox pattern, event streaming, and asynchronous
worker architecture ensure that a communications failure never blocks financial
operations.

---

## 6. Recovery Checklists

### 6.1 Africa\'s Talking Outage \u2014 Quick Checklist

- [ ] Confirm circuit breaker is OPEN
- [ ] Verify failover is routing to secondary provider
- [ ] Check notification queue depth
- [ ] Scale up workers if queue growing
- [ ] Monitor Africa\'s Talking status page
- [ ] Create incident ticket
- [ ] On recovery: verify circuit closes automatically
- [ ] Update incident to RESOLVED

### 6.2 Database Outage \u2014 Quick Checklist

- [ ] Verify database is down (not transient)
- [ ] Confirm core transactions unaffected
- [ ] Notify on-call
- [ ] On recovery: restart workers
- [ ] Drain outbox queue
- [ ] Verify no data loss
- [ ] Check Kafka lag
- [ ] Send test notification

### 6.3 Full Communications Subsystem Recovery \u2014 Quick Checklist

- [ ] Database available
- [ ] Redis available
- [ ] Kafka available
- [ ] Workers running and consuming
- [ ] Africa\'s Talking health: HEALTHY
- [ ] Circuit breaker: CLOSED
- [ ] Outbox drained
- [ ] Test notification: DELIVERED
- [ ] Incident updated to RESOLVED

---

## 7. Contact and Escalation

| Role | Contact | Escalation |
|------|---------|------------|
| Communications On-Call | ops-oncall@pesaguard.internal | Platform Lead |
| Platform Lead | platform-lead@pesaguard.internal | CTO |
| Africa\'s Talking Support | support@africastalking.com | \u2014 |
| Database On-Call | dba-oncall@pesaguard.internal | Platform Lead |
| Security On-Call | security-oncall@pesaguard.internal | CISO |

---

## 8. Post-Incident Review

After every communication-related incident, conduct a post-incident review within
48 hours covering:

1. Timeline of events
2. Detection time vs. incident start time
3. Recovery time
4. Impact assessment
5. Root cause
6. What worked well
7. What needs improvement
8. Action items with owners and due dates

Post-incident reviews are stored in the PesaGuard incident management system.
