# PesaGuard — Production Hardening Checklist & Implementation Prompt

## Purpose

Use this as a build prompt to harden PesaGuard from MVP to production-trustworthy, before any new feature work (multi-provider, ML fraud scoring, etc.) begins. Each section below should be implemented and verified in order — idempotency and security come first since they're the highest-risk gaps with a live pilot customer's real money flowing through the system.

---

## 1. Webhook Idempotency

**Goal**: the same Daraja callback, delivered once or five times, produces exactly one processed result.

- [ ] Extract a stable dedup key from every incoming webhook (provider transaction ID / `TransID` from Daraja)
- [ ] Before processing, check an idempotency store (Redis `SETNX` or a DB table with a unique constraint on the dedup key)
- [ ] If the key already exists: return HTTP 200 immediately, log it as a duplicate, do not reprocess or re-trigger side effects (notifications, reconciliation writes)
- [ ] If the key is new: atomically claim it (same operation that checks and inserts, no separate check-then-write) before starting processing, so two near-simultaneous copies of the same webhook can't both pass
- [ ] Set a sensible TTL/retention on the idempotency store — long enough to cover realistic Safaricom retry windows (confirm what that window actually is, don't assume)
- [ ] Write a test that fires the same webhook payload twice in quick succession and asserts only one reconciliation record is created

**Implementation notes**
```python
# Pseudocode pattern
def handle_webhook(payload):
    dedup_key = payload["TransID"]
    claimed = redis.set(dedup_key, "1", nx=True, ex=REPLAY_WINDOW_SECONDS)
    if not claimed:
        log.info("duplicate_webhook_ignored", trans_id=dedup_key)
        return Response(status=200)
    process_transaction(payload)
    return Response(status=200)
```

---

## 2. Security

**Goal**: only legitimate Safaricom traffic is trusted, and a breach of any one component doesn't compromise everything.

- [ ] Validate incoming webhook requests against Daraja's documented IP allowlist or signature scheme — verify this exists in current Daraja docs, don't assume
- [ ] Move all secrets (Daraja consumer key/secret, DB URL, JWT signing key) out of code and `.env` files committed to git — confirm nothing is currently in git history (`git log -p | grep -i secret` as a sanity check)
- [ ] Enforce HTTPS on all Render routes, including internal service-to-service calls
- [ ] Add rate limiting on the public webhook endpoint and any other public routes (per-IP and/or per-API-key)
- [ ] Validate every field from the webhook payload against an expected schema before it reaches business logic — treat the payload as untrusted even though it's "from Safaricom"
- [ ] Confirm the database connection uses a least-privilege user, not an admin/superuser credential
- [ ] Run a dependency audit (`pip-audit` for Python, `npm audit` if there's a JS component) and resolve any critical/high CVEs
- [ ] Confirm CORS policy on any public API is scoped to actual allowed origins, not `*`

---

## 3. Observability

**Goal**: when something goes wrong, you find out before the pilot customer tells you.

- [ ] Structured (JSON) logging on every webhook received, matched, flagged, or errored — include transaction ID in every log line for traceability
- [ ] Alerting configured for: webhook processing failures, an unusual drop or spike in transaction volume, reconciliation mismatch rate exceeding a defined threshold
- [ ] External uptime monitoring on the health check endpoint (don't rely solely on Render's own monitoring)
- [ ] A minimal operational dashboard showing: transactions processed today, anomalies flagged today, current error rate — even a simple Grafana panel or admin page is enough at this stage
- [ ] Error tracking (Sentry or equivalent) capturing unhandled exceptions with request context attached, not just bare stack traces

---

## 4. Data Integrity

**Goal**: every reconciliation decision is explainable after the fact, and data loss is recoverable.

- [ ] Every match/mismatch decision is written to an audit log/table — not just the final state, but the decision and its inputs, so a dispute can be traced
- [ ] Automated database backups are running
- [ ] A restore from backup has actually been tested at least once — this is the step people skip and regret
- [ ] Schema migrations use non-locking patterns where the table is under active load (e.g. `CREATE INDEX CONCURRENTLY` in Postgres) rather than default blocking migrations

---

## 5. Pilot-Specific Readiness

**Goal**: when something breaks at 2am, there's already a plan instead of improvisation.

- [ ] Documented escalation path for the pilot customer (who to contact, expected response time)
- [ ] A short runbook for the most likely failure modes: webhook backlog/delay, Daraja API downtime, database connection exhaustion — each with concrete first steps, not just "investigate"
- [ ] Rollback procedure for a bad deploy confirmed and tested on Render (know the exact steps before you need them under pressure)

---

## Definition of Done

PesaGuard is considered production-hardened when:
1. The duplicate-webhook test (Section 1) passes reliably under concurrent load, not just sequential retries
2. A security review confirms no secrets in git history and all public endpoints are rate-limited
3. An alert fires correctly when a test anomaly/failure is deliberately injected (prove the observability actually works, don't just assume the config is correct)
4. A backup restore has been performed successfully at least once
5. The runbook has been read and understood by anyone who might need to respond to an incident

Only after all five are true should new feature work (multi-provider support, ML fraud scoring, or anything else) begin.
