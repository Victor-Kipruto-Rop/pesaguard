# Communications Runbook

## Provider outage

**Trigger:** Provider health score < 70, circuit breaker OPEN, delivery rate < 95%

**Procedure:**
1. Confirm provider health via `GET /api/v1/communications/providers/health`
2. Record incident: `POST /api/v1/communications/incidents` (fingerprint dedupes)
3. Disable the affected route: set `enabled=0` in `communication_provider_routes`
4. Preserve queued records (do NOT delete; do NOT manually re-enqueue with active leases)
5. Enable failover: verify backup provider configured and healthy
6. Keep financial processing enabled (never block transactions for communications)
7. After provider recovers: enable route, verify health score, replay dead-letter entries that are permanent-error free

**Escalation:** If provider unavailable > 15 min, alert on-call + escalate to provider support.

## SMS failures

**Trigger:** Error rate > 5%, delivery rate < 95%, dead-letter count rising

**Procedure:**
1. Check `GET /api/v1/communications/messages?status=failed` for error patterns
2. Examine error categories: TIMEOUT vs NETWORK_ERROR vs INVALID_RECIPIENT vs INSUFFICIENT_BALANCE
3. Check provider dashboard for rate limits, balance, or outages
4. If `INSUFFICIENT_BALANCE`: top up wallet immediately (this is NOT a failover case)
5. If `INVALID_RECIPIENT`: correct the recipient data source; do not retry
6. If transient: wait for retry backoff; verify worker is healthy
7. Replay dead-letter entries via admin API after root cause fixed

## Webhook failure

**Trigger:** Pending-review events, delivery rate drop, missed DELIVERED statuses

**Procedure:**
1. Check `GET /api/v1/communications/webhook-events?processing_status=pending_review`
2. Verify HTTPS routing and secret rotation
3. Verify provider has `callback_base_url` pointing to the delivery endpoint
4. Test with a sandbox send + deliberately bad signature (verify 401)
5. After config verified, replay via `POST /api/v1/communications/webhook-events/<id>/replay`
6. Confirm statuses update via message detail API

## Wallet low balance

**Trigger:** `wallet_health.status` = WARNING or CRITICAL (runway < 7 days)

**Procedure:**
1. Check `GET /api/v1/communications/analytics/costs` for burn rate
2. Verify configured balance via `PESAGUARD_COMMUNICATION_WALLET_BALANCE`
3. Top up provider wallet (urgent if CRITICAL)
4. If balance hits 0: provider returns INSUFFICIENT_BALANCE, messages dead-letter
5. Never silently mark messages as DELIVERED - provider must confirm

## Credential rotation

**Trigger:** Scheduled rotation, suspected leak, provider auth errors

**Procedure:**
1. Generate new credentials in provider dashboard (sandbox first)
2. Update secret store (not source code)
3. Test one controlled send using new credentials
4. Verify callback works (webhook signature still valid)
5. If successful: revoke old credentials
6. Audit the operator and result

## Queue backlog

**Trigger:** Queue depth > N, SLA breaches, page latency

**Procedure:**
1. Inspect outbox status distribution (`pending`/`retrying`/`dead_letter`)
2. Check `available_at` of oldest entries (stuck entries?)
3. Check worker count (scale within provider/database limits)
4. Check provider rate limits and rate governor
5. Do NOT create duplicates by re-enqueuing active leases
6. If critical priority SLAs breached: consider pausing low-priority campaigns

## High latency

**Trigger:** P95 latency > SLA target, provider response time spike

**Procedure:**
1. Check provider health endpoint for latency trend
2. Check worker throughput
3. Check database connection pool
4. Check rate governor wait times
5. If provider slow: consider failover (only if TIMEOUT/NETWORK errors)
6. Record incident with supporting metrics

## Campaign incident

**Trigger:** Campaign stuck, unplanned volume, recipient complaints

**Procedure:**
1. Pause immediately: `POST /api/v1/communications/campaigns/<id>/pause`
2. Check progress: `GET .../campaigns/<id>` (processed/failed counts)
3. Investigate template variables, rate limits, recipient quality
4. Resume only after root cause addressed
5. Cancel if irrecoverable (marks pending recipients as cancelled)

## OTP abuse

**Trigger:** Detect_otp_abuse findings, flood/enumeration patterns

**Procedure:**
1. Review findings (recipient flood, IP enumeration)
2. Apply temporary block on recipient/IP
3. Tighten rate limits if needed
4. Raise security incident (fingerprint dedupes)
5. Preserve evidence (challenge records, IPs, timestamps)

## Provisioning / rollback

**Procedure:**
```bash
# Migrate
alembic upgrade head

# Run worker
python -m pesaguard_backend_pipeline.communications.worker

# Rollback (immediate disable)
export PESAGUARD_FLAG_AFRICASTALKING_SMS=false
export PESAGUARD_FLAG_CAMPAIGNS=false
# Restart the app; provider sends stop without code changes
```
