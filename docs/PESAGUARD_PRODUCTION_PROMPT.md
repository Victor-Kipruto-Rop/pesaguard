# PesaGuard — Full Production Build Prompt

A single, self-contained prompt for an AI coding agent (Claude Code, Cursor,
etc.) to build PesaGuard end-to-end as a production-grade system. Unlike the
earlier extension prompt, this one assumes no prior scaffold — feed it alone,
or alongside the existing `pesaguard` as a starting point if you want
to preserve that work.

Copy everything between PROMPT START and PROMPT END into your agent.

---

## PROMPT START

You are building **PesaGuard**, a production-grade, multi-tenant SaaS system
that provides real-time reconciliation and anomaly detection for businesses
accepting payments via Safaricom's M-Pesa Daraja API (SACCOs, e-commerce
operators, small fintechs).

### The problem this solves

Businesses using Daraja today reconcile payments manually, often a day or
more after the fact, in spreadsheets. In that window: money goes missing,
customers get double-charged, and failed webhook callbacks go unnoticed
until someone complains. PesaGuard closes that gap to seconds.

### What "production-grade" means here

This is financial data. Every decision below is written with that in mind.
Correctness, auditability, and no data loss take priority over speed of
delivery or feature breadth. Build the smallest system that satisfies these
constraints, not the largest one that's technically impressive.

---

### 1. Functional Requirements

Build all of the following. Priorities: **Must** = required for a real
pilot customer to trust the system; **Should** = required before charging
money; **Could** = defer unless trivial.

| ID | Requirement | Priority |
|---|---|---|
| FR-1 | Receive and validate M-Pesa Daraja C2B confirmation/validation webhooks | Must |
| FR-2 | Publish validated transaction events to a durable stream (Kafka) | Must |
| FR-3 | Match incoming M-Pesa transactions against internal ledger/order records by phone + amount + configurable time window | Must |
| FR-4 | Detect duplicate transaction IDs (persistent dedup, not in-memory) | Must |
| FR-5 | Detect amount mismatches between M-Pesa and internal records | Must |
| FR-6 | Detect missing callbacks — internal record exists, no matching M-Pesa payment after the window | Must |
| FR-7 | Handle partial matches (e.g. amount matches, phone doesn't — someone paying on another's behalf) as `needs_review`, not a hard discrepancy | Must |
| FR-8 | Auto-resolve a discrepancy when a late-arriving event matches, and record the resolution latency | Should |
| FR-9 | Flag unusually large transactions for manual review (configurable threshold) | Should |
| FR-10 | Send real-time alerts (Slack, SMS, email) on discrepancies, with severity tiers | Must |
| FR-11 | Escalate unresolved `critical` alerts after a configurable delay | Should |
| FR-12 | Daily summary digest (transactions reconciled, open discrepancies, resolution rate) | Should |
| FR-13 | Dashboard: live discrepancy feed with filters (status, tenant, date range) | Must |
| FR-14 | Dashboard: reconciliation rate chart (daily/weekly trend) | Should |
| FR-15 | Dashboard: manual resolution flow with notes | Must |
| FR-16 | Dashboard: tenant settings page (alert channels, thresholds, connector credentials) | Must |
| FR-17 | Multi-tenant data isolation across every table, topic, and API route | Must |
| FR-18 | Pluggable internal-system connectors: Postgres, Google Sheets, generic REST API | Must |
| FR-19 | Per-tenant configurable field mapping for connectors (customers name columns differently) | Must |
| FR-20 | Full audit log — every reconciliation decision traceable to a rule, timestamp, and tenant | Must |

### 2. Non-Functional Requirements

| ID | Requirement | Target |
|---|---|---|
| NFR-1 | Reconciliation latency, webhook receipt to match/flag | < 30 seconds |
| NFR-2 | No data loss on service downtime | Zero dropped events — use a dead-letter queue or buffering with retry |
| NFR-3 | Idempotent processing of duplicate webhook deliveries | 100% dedup, persisted (Redis or DB unique constraint), not in-memory |
| NFR-4 | Webhook receiver uptime | 99.5%+ |
| NFR-5 | Tenant data isolation | Zero cross-tenant leakage, enforced at the query layer, not just application logic |
| NFR-6 | Alert delivery latency | < 60 seconds from detection |
| NFR-7 | All secrets (Daraja creds, DB creds, OAuth tokens) | Never committed; injected via environment/secrets manager |

---

### 3. Tech Stack

Use this stack unless you have a specific, stated reason to deviate —
don't introduce new infrastructure components without justification.

| Layer | Technology |
|---|---|
| Ingestion | Flask (Python) |
| Streaming | Apache Kafka |
| Processing | Python consumer (MVP-scale); document a clear migration path to PyFlink if/when volume requires it — don't build PyFlink from day one |
| Primary storage | PostgreSQL |
| Analytics storage (later) | BigQuery — only if a stated scale reason exists |
| Connectors | psycopg2, gspread (Google Sheets OAuth2), requests (generic REST) |
| Dedup / caching | Redis |
| Alerting | Slack Incoming Webhooks, Africa's Talking (SMS) |
| Dashboard frontend | Next.js + React |
| Dashboard backend | Flask or Django REST Framework |
| Auth | Email/password or magic link (e.g. NextAuth) — don't over-build this |
| Containerization | Docker, docker-compose |
| Production deploy | Single VM + docker-compose by default; only design for Kubernetes if tenant count or throughput explicitly requires it |
| CI/CD | GitHub Actions |
| Observability | Structured JSON logging, Prometheus-compatible `/metrics` endpoints |
| Testing | pytest |

---

### 4. Architecture

```
M-Pesa Daraja
     |
     v
Webhook Receiver (Flask) --validates, dedupes--> Kafka: transactions.raw
     |
     v
Reconciliation Job <----> Internal Ledger Connector (per-tenant config)
     |
     v
PostgreSQL (transactions, discrepancies, audit log — all tenant-scoped)
     |
     +------------------+------------------+
     v                  v                  v
Alerting            Dashboard API      Metrics/Logs
(Slack/SMS/email)   (Flask)            (Prometheus-style)
```

**Non-negotiable architectural principles:**

- Kafka decouples ingestion from processing so a slow rule engine or a
  down database never causes a Daraja webhook timeout.
- Every table, Kafka message, and API route carries `tenant_id`. Design
  this in from the first migration — retrofitting multi-tenancy later is
  expensive and error-prone.
- Postgres is the single source of truth for audit purposes. Log every
  transaction and every reconciliation decision, not just the flagged
  ones — "why wasn't this flagged" must be answerable months later.
- Connectors are pluggable behind a `BaseConnector` interface. The
  reconciliation job must not contain tenant-specific or
  connector-specific logic.

---

### 5. Development Phases

Build in this order. Do not skip Phase 0-1 discipline even though you're
an AI agent and code is "free" to write — a system built ahead of
validation is still wasted effort if the matching logic doesn't fit how
real Daraja/SACCO data actually behaves.

**Phase 1 — Core Pipeline (Weeks 1-2)**
Webhook receiver with validation and persistent dedup, Kafka topics,
Postgres schema (tenant-scoped from the start), basic anomaly rules
(duplicate, invalid amount, large amount), Slack alerting, docker-compose
for local dev. Full audit logging from day one, not bolted on later.

**Phase 2 — Real Matching Logic (Weeks 3-4)**
Postgres connector with per-tenant field mapping, phone+amount+time-window
matching, partial-match handling (`needs_review` tier), missing-callback
detection, auto-resolution of late-arriving matches.

**Phase 3 — Multi-Tenancy & Additional Connectors (Weeks 5-6)**
Full tenant isolation audit across all queries. Google Sheets connector
(OAuth2 service account flow). Generic REST connector with configurable
auth and pagination. Connector config stored per-tenant, not hardcoded.

**Phase 4 — Dashboard (Weeks 7-8)**
Next.js frontend: live discrepancy feed, reconciliation rate chart, manual
resolution flow, tenant settings page. Dashboard API with proper tenant
scoping on every endpoint.

**Phase 5 — Alerting Maturity (Week 9)**
Severity tiers (info/warning/critical), escalation on unresolved critical
alerts, SMS via Africa's Talking, daily digest.

**Phase 6 — Observability & Hardening (Weeks 10-11)**
Structured JSON logging with `tenant_id`/`trans_id` correlation across all
services. Health checks and `/metrics` on every service. Dead-letter queue
for failed processing. Idempotency audit — verify duplicate webhook
deliveries genuinely cannot double-process under load.

**Phase 7 — Testing (Week 12)**
Unit tests for every anomaly rule and every matching scenario (exact
match, partial match, no match, late match, duplicate). Integration test
running the full pipeline against docker-compose with realistic Daraja
sandbox payload fixtures. Basic load test validating no event loss under
burst traffic.

**Phase 8 — Deployment & Launch (Week 13+)**
Single-VM production deploy, GitHub Actions CI (test, build, deploy on
merge to main), secrets management, HTTPS on the webhook receiver
(required by Daraja), onboarding runbook for tenant #2+.

---

### 6. Testing Requirements

- Unit tests for every anomaly rule: clean, duplicate, invalid amount,
  large amount, and every matching scenario (exact, partial, no-match,
  late-match).
- Integration test with realistic Daraja sandbox payload shapes covering
  the full pipeline: webhook → Kafka → reconciliation → Postgres → alert.
- Idempotency test: send the same `TransID` twice in quick succession,
  assert exactly one processed record and one alert (if applicable).
- Load test: simulate burst traffic and confirm zero dropped events.
- Multi-tenant isolation test: confirm tenant A's API calls and queries
  never surface tenant B's data, even under adversarial query construction.

---

### 7. Security & Compliance

- Never commit secrets. Daraja credentials, DB credentials, connector
  OAuth tokens must be injected via environment variables or a secrets
  manager.
- Validate and verify Daraja webhook payloads against Safaricom's
  published IP ranges or shared-secret mechanism if available — flag this
  as an assumption to verify against real sandbox testing.
- Review data handling against Kenya's Data Protection Act before
  onboarding real customer transaction data — flag this explicitly rather
  than assuming compliance.
- Tenant data isolation must be enforced at the database query layer
  (e.g. row-level security or mandatory `tenant_id` filtering in every
  query helper), not solely trusted to application code remembering to
  filter correctly.

---

### 8. Deliverable

A single coherent monorepo with:

- All services described above, organized by responsibility (ingestion,
  streaming, storage, alerting, dashboard).
- A top-level `SETUP.md`: environment setup, running locally, running
  tests, and a checklist for onboarding a new pilot tenant end to end.
- A `SECURITY.md` documenting the secrets-handling approach and any
  compliance assumptions that still need verification.
- Docker Compose for local development and a documented single-VM
  production deployment path.
- GitHub Actions CI running the full test suite on every PR.

### 9. Constraints & Working Style

- Flag any assumption about M-Pesa/Daraja behavior that needs verification
  against real sandbox testing before being trusted in production.
- Don't introduce Kubernetes, Terraform, or BigQuery unless a stated scale
  reason exists — default to the simplest infrastructure that satisfies
  the non-functional requirements above.
- Every new module needs a short docstring explaining the business problem
  it solves, not just what it technically does — this codebase will
  likely be read by future hires who aren't yet fintech domain experts.
- Prefer correctness and auditability over cleverness. If a shortcut would
  make a reconciliation decision harder to explain months later, don't
  take it.

## PROMPT END
