# PesaGuard — Master Build Prompt (Full, Phased)

This is the single, complete, self-contained prompt covering everything
needed to take PesaGuard from zero to a production-strong, multi-tenant
system: core pipeline, real reconciliation logic, alerting, monitoring,
dashboards, security, backup/DR, incident response, data retention, docs,
and testing — all organized into build phases.

Feed this to an AI coding agent (Claude Code, Cursor, etc.) as a standalone
prompt. It supersedes and consolidates the earlier partial prompts
(extension prompt, full production prompt, alerting/monitoring/dashboards
prompt, and readiness prompt) into one ordered build plan.

Copy everything between PROMPT START and PROMPT END into your agent.

---

## PROMPT START

You are building **PesaGuard**, a production-grade, multi-tenant SaaS
system providing real-time reconciliation and anomaly detection for
businesses accepting payments via Safaricom's M-Pesa Daraja API (SACCOs,
e-commerce operators, small fintechs).

### The problem

Businesses using Daraja today reconcile payments manually, often a day or
more later, in spreadsheets. In that window, money goes missing, customers
get double-charged, and failed webhook callbacks go unnoticed until
someone complains. PesaGuard closes that gap to seconds.

### What "production-strong" means here

This is financial infrastructure for third-party businesses. Correctness,
auditability, and no data loss take priority over speed of delivery or
feature breadth in every phase below. Build the smallest system that
satisfies each phase's requirements before moving to the next — do not
skip ahead to later phases while earlier non-functional requirements
(multi-tenancy, audit logging, idempotency) remain unmet.

### Guardrails that apply across every phase

- Every table, Kafka message, and API route carries `tenant_id` from the
  very first migration. Retrofitting multi-tenancy later is expensive and
  error-prone — do not defer this.
- Log every transaction and every reconciliation decision, not just
  flagged ones. "Why wasn't this flagged" must be answerable months later.
- Don't introduce Kubernetes, Terraform, BigQuery, or a paid observability
  SaaS unless a stated scale reason exists. Default to the simplest
  infrastructure that satisfies the requirements: single VM +
  docker-compose, PostgreSQL, Prometheus + Grafana.
- Flag any assumption about Daraja behavior, alert thresholds, or
  retention periods that needs verification against real sandbox testing
  or real contractual terms — don't silently treat a guess as final.
- Every new module gets a short docstring explaining the business problem
  it solves, not just what it does technically.

---

### PHASE 0 — Discovery & Validation (Week 1, no code)

Before writing production code, confirm the problem is real:
- Identify 5-10 candidate pilot customers (SACCOs, e-commerce operators)
- Validate that manual reconciliation pain is real and they'd grant read
  access to their internal order/ledger system
- Confirm Daraja sandbox access and pull real callback payload samples

**Do not proceed past this phase without at least directional validation
that one real or realistic pilot customer exists.**

---

### PHASE 1 — Core Pipeline (Weeks 2-3)

Build the ingestion and storage foundation, multi-tenant from day one.

**Functional requirements:**
- Webhook receiver (Flask) validating and ingesting Daraja C2B
  confirmation/validation callbacks
- Publish validated events to Kafka (`mpesa.transactions.raw`)
- Tenant-scoped Postgres schema: transactions, discrepancies, audit log,
  tenant config
- Basic anomaly rules: duplicate transaction ID (persistent, via Redis or
  DB constraint — not in-memory), invalid/zero amount, large-amount flag
- Full audit logging of every transaction and every rule evaluation,
  scoped by `tenant_id`
- docker-compose for local dev (Kafka, Postgres, Redis, services)

**Non-functional requirements:**
- Reconciliation-adjacent latency (webhook receipt to Kafka publish)
  under a few seconds
- Zero dropped events on downstream downtime — buffer or dead-letter,
  don't drop
- 100% idempotent processing of duplicate webhook deliveries
- No secrets committed; environment-injected configuration

---

### PHASE 2 — Real Matching & Reconciliation Logic (Weeks 4-5)

Replace intra-stream-only anomaly detection with real cross-system matching.

**Functional requirements:**
- `BaseConnector` interface; implement `PostgresConnector` with per-tenant
  configurable field mapping (customers name columns differently)
- Match incoming M-Pesa transactions to internal records by phone +
  amount + configurable time window (default plus/minus 15 min)
- Partial matches (amount matches, phone doesn't) flagged as
  `needs_review`, not a hard discrepancy — this is often legitimate
  (e.g. family paying on someone's behalf)
- Missing-callback detection: internal record exists, no matching M-Pesa
  payment after the window — typically the highest-priority case
- Auto-resolution: a late-arriving event matching a previously unresolved
  record gets marked resolved, with resolution latency recorded
- `ConnectorRegistry` loading the right connector per tenant from config
  — the reconciliation job itself must contain no tenant-specific logic

---

### PHASE 3 — Alerting System (Weeks 6-7)

Extract alerting into its own service, decoupled from the reconciliation
job, consuming a dedicated `mpesa.discrepancies` topic.

**Functional requirements:**
- Multi-channel delivery: Slack, SMS (Africa's Talking), email
- Severity tiers: `info` (digest only), `warning` (Slack), `critical`
  (SMS + Slack simultaneously)
- Escalation: unresolved `critical` alerts re-notify every 30 minutes
  until resolved or acknowledged
- Acknowledgement flow that pauses escalation without full resolution
- Daily digest per tenant: transactions processed, open discrepancies,
  resolution rate
- Per-tenant configurable channels and thresholds
- Alert deduplication — retries of the same discrepancy must not
  re-notify
- Every alert logged: channel, recipient, timestamp, delivery
  success/failure, for audit

**Design constraint:** alerting logic lives entirely outside the
reconciliation job so alert routing/tiering can change without touching
matching logic.

---

### PHASE 4 — Monitoring & Observability (Weeks 8-9)

Build visibility into the system's own health — distinct from the
customer-facing alerting in Phase 3.

**Functional requirements:**
- `/health` endpoint on every service
- Structured JSON logging across all services with correlated
  `tenant_id`/`trans_id` fields
- Prometheus-compatible `/metrics` on every service, tracking:
  transactions/min, reconciliation latency (p50/p95/p99), discrepancy
  rate, Kafka consumer lag, alert delivery success rate per channel,
  per-tenant connector health
- Operator alerting: Kafka lag, service downtime, or repeated connector
  failure pages the operator (you) through Prometheus Alertmanager or
  equivalent, **routed to a separate ops-only channel — never the
  customer-facing alert channel from Phase 3**
- `RUNBOOK.md`: what to check and do for Kafka lag growth, connector auth
  failures, or unexpected Daraja volume spikes

---

### PHASE 5 — Dashboards (Weeks 10-12)

Two separate dashboards, different audiences — do not merge them.

**5a. Operational Dashboard (Grafana) — for you:**
- Kafka lag, reconciliation latency, throughput, discrepancy rate by
  type, alert delivery rate, per-tenant connector health
- Provisioned as code (JSON model or Terraform), not clicked together
  manually, so it's reproducible and versioned

**5b. Customer-Facing Dashboard (Next.js) — for the pilot tenant:**
- Live discrepancy feed with filters (status, date range)
- Discrepancy detail view showing the matching decision and reasoning
  (auditability, not just a status badge)
- Manual resolution flow with structured reason category + free-text note
  (this data should be capturable for later threshold tuning)
- Reconciliation rate chart (daily/weekly trend)
- Tenant settings page: alert channels, thresholds, connector credentials
- Simple auth (email/password or magic link) — don't over-build this
- Every view and API call scoped to the authenticated tenant only

---

### PHASE 6 — Security & API Protection (Week 13)

**Functional requirements:**
- Rate limiting on the webhook receiver and dashboard API
- Request size limits on all endpoints
- Daraja webhook endpoint validates source (IP allowlist or shared
  secret) before processing
- Dashboard API auth tokens expire and can be revoked
- Generic external error messages; detailed errors only in internal logs
- Tenant data isolation enforced at the database query layer (e.g. row-
  level security or mandatory `tenant_id` filtering in every query
  helper), not solely trusted to application code

---

### PHASE 7 — Backup, Disaster Recovery & Data Retention (Week 14)

**Functional requirements:**
- Automated daily Postgres backups stored off the primary instance
- Documented, **tested** restore procedure with copy-pasteable commands
  in `DISASTER_RECOVERY.md`
- Backup retention policy (e.g. daily for 30 days, weekly for 6 months)
- Deliberate Kafka topic retention configuration (not left at default) so
  replay is possible after an incident
- Documented retention periods for transaction data, discrepancy records,
  and logs in `DATA_RETENTION.md`
- Tenant offboarding process: data export + deletion with a defined grace
  period
- Audit log retention handled as its own rule, separate from operational
  data

Flag chosen retention periods explicitly as placeholders pending real
contractual/compliance sign-off — don't treat an invented number as final.

---

### PHASE 8 — Incident Response Tooling (Week 15)

**Functional requirements:**
- On-call routing for operator alerts from Phase 4 (even if "on-call" is
  just you — define concretely how you get paged)
- Incident severity definitions (SEV1/SEV2/SEV3)
- Customer notification template for incidents affecting their
  reconciliation
- Postmortem template: what happened, impact, root cause, follow-ups
- Single `INCIDENT_RESPONSE.md` tying together paging, incident
  declaration, status communication, and close-out

---

### PHASE 9 — API Documentation (Week 15, parallel with Phase 8)

**Functional requirements:**
- OpenAPI/Swagger spec for the dashboard API (for pilot customers wanting
  programmatic access)
- Interactive docs served from a docs endpoint (Swagger UI or equivalent)
- Extend (don't duplicate) the existing internal webhook payload
  reference documentation

---

### PHASE 10 — Testing & Hardening (Weeks 16-17)

**Comprehensive test coverage required before launch:**
- Unit tests for every anomaly rule and every matching scenario (exact,
  partial, no-match, late-match, duplicate)
- Integration test running the full pipeline against docker-compose with
  realistic Daraja sandbox payload fixtures
- Idempotency test: duplicate `TransID` delivered twice produces exactly
  one processed record and one alert
- Load test: burst traffic produces zero dropped events and zero dropped
  alert deliveries
- Multi-tenant isolation test: tenant A's queries/API calls never surface
  tenant B's data, including adversarial query construction
- Escalation timing test: unresolved critical alerts re-fire on schedule,
  stop after acknowledgement/resolution
- Verify operator alerts and customer alerts never cross-contaminate
  channels

---

### PHASE 11 — Deployment & Launch (Week 18+)

**Functional requirements:**
- Single-VM production deployment via docker-compose (default; only
  design for Kubernetes if tenant count/throughput explicitly justifies it)
- GitHub Actions CI: run full test suite, build images, deploy on merge
  to main
- Secrets management: Daraja credentials, DB credentials, connector OAuth
  tokens injected via environment/secrets manager, never committed
- HTTPS on the webhook receiver (required by Daraja for the
  ConfirmationURL)
- Tenant-onboarding runbook covering: connector setup, threshold
  configuration, alert channel setup, and a shadow-mode period (alert
  only, no customer-facing trust yet) before going fully live

---

### Final Deliverable

A single coherent monorepo containing:
- All services organized by responsibility (ingestion, streaming,
  storage, alerting, monitoring, dashboard)
- `SETUP.md` — environment setup, running locally (including
  Prometheus/Grafana), running tests, tenant-onboarding checklist
- `SECURITY.md` — secrets handling, tenant isolation approach, any
  compliance assumptions still needing verification
- `DISASTER_RECOVERY.md`, `INCIDENT_RESPONSE.md`, `DATA_RETENTION.md`,
  `RUNBOOK.md`
- OpenAPI spec for the dashboard API
- Grafana dashboard definitions committed as code
- Docker Compose for local dev; documented single-VM production path
- GitHub Actions CI running the full test suite on every PR

## PROMPT END

---

## Appendix — Business & Operational Readiness (Not Buildable by an Agent)

These run in parallel with the technical phases above, ideally starting
no later than Phase 5, since a real pilot customer's data will be
touching the system well before Phase 11.

- **Terms of Service** and **Privacy Policy**
- **Data Processing Agreement (DPA)** — defines liability if
  reconciliation misses something or data leaks
- **ODPC registration** under Kenya's Data Protection Act (check current
  thresholds at odpc.go.ke)
- **E&O / liability insurance** conversation — you are the system a
  business relies on to catch missing money
- **Pricing/packaging** — flat fee, per-transaction, or volume-tiered
- **One-page pilot agreement** — scope, duration, what happens after
- **Support channel** — explicit definition (shared Slack is fine at
  pilot scale) and informal response-time expectation
- **SLA** once paid — uptime and alert-delivery commitments

None of the above is legal advice — every draft should go through a
qualified professional before being used with a real customer.
