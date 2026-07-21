# PesaGuard — Backend Implementation & Modification List

Status categories: **Required now** (blocking pilot reliability), **Modification** (change to 
existing code), **Additional** (new capability, not urgent), **Future** (only build when 
triggered by real need).

---

## Required Now (Pilot Reliability — Do These First)

- [ ] **Webhook idempotency** — unique constraint + check-before-process in `models.py`, 
  `event_store.py`, `reconciliation_engine.py`
- [ ] **Fast `200` response to Daraja** — move slow work (notifications, etc.) to background 
  task so Safaricom doesn't retry unnecessarily
- [ ] **Webhook signature/IP validation** — don't trust inbound payloads blindly
- [ ] **Automated Postgres backups** — daily, with an actually-tested restore procedure
- [ ] **Health check endpoint** (`health.py` already exists — confirm it checks DB, queue, 
  and Daraja connectivity, not just "server is up")
- [ ] **Structured logging with correlation IDs** — trace a transaction through ingestion → 
  reconciliation → notification in the logs

## Modifications to Existing Modules

- [ ] `models.py` — add `processed_transactions` table/model with unique constraint on 
  transaction ID
- [ ] `event_store.py` — confirm it can serve as the idempotency source of truth, or extend it
- [ ] `reconciliation_engine.py` — add duplicate-check before reconciliation write; wrap 
  idempotency-log insert + reconciliation write in one DB transaction
- [ ] `reconciliation_job.py` — confirm scheduled/batch reconciliation also respects the 
  same idempotency guarantees as the real-time path
- [ ] `anomaly_rules.py` — review current rules against real pilot data; tune thresholds 
  based on this specific customer's actual transaction patterns (not generic assumptions)
- [ ] `notifier.py` — confirm retry + failure logging exists (don't silently drop a 
  failed notification)
- [ ] `rate_limiter.py` — confirm it's actually applied to the public webhook endpoint, 
  not just defined
- [ ] `auth_rbac.py` — confirm roles map cleanly to what the frontend needs 
  (admin vs customer-user vs read-only)
- [ ] `escalation_engine.py` / `on_call_service.py` — confirm these are wired to real 
  alerting conditions (webhook failures, queue backlog), not just scaffolded

## Additional (Not Urgent — Build When Stable)

- [ ] Dead-letter log/table for malformed or rejected webhook payloads
- [ ] Fuzzy/approximate reconciliation matching for partial payments or timing lag
- [ ] Per-customer configuration for reconciliation rules (multi-tenant readiness)
- [ ] Public-facing API endpoints for customers to pull their own data
- [ ] Scheduled report generation job (daily/weekly reconciliation summaries)
- [ ] Audit log write-path for all state-changing actions (who matched what, who 
  acknowledged which anomaly)

## Real Need-implenent them all

- [ ] Background job queue (Celery/RQ) — once webhook volume causes processing delays
- [ ] Read replicas — once reporting queries compete with reconciliation writes
- [ ] Redis caching — once duplicate-check lookups become a measurable bottleneck
- [ ] Kafka/PyFlink streaming — only once single-instance processing can't keep up
- [ ] Multi-tenant data isolation — once a 2nd/3rd paying customer is confirmed
- [ ] Statistical/ML anomaly scoring — once months of real transaction data exist
- [ ] AI assistant subsystem (read-only query layer) — only after core reconciliation + 
  idempotency + audit log have run cleanly for 2–4 weeks

---

## Build
- Kubernetes orchestration
- Multi-region deployment
- Any AI-agent write access to transactions, accounts, or credentials
- Free-form SQL generation for any assistant feature

---

**Where to start:** the "Required Now" section, in order. Everything below it should wait 
until those items are shipped and verified against the live pilot customer's real transactions.
