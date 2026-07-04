# PesaGuard — Full Build Prompt

Use this prompt with an AI coding agent (Claude Code, Cursor, etc.) to build
out the full production version. Feed it the existing `pesaguard`
scaffold as context first, then this prompt.

---

## PROMPT START

You are building **PesaGuard**, a real-time reconciliation and anomaly
detection system for businesses that accept M-Pesa payments (SACCOs,
e-commerce operators, small fintechs) via Safaricom's Daraja API.

**The core problem it solves:** businesses currently reconcile M-Pesa
payments against their internal orders/ledger manually, hours or days
later, using spreadsheets. Money goes missing, customers get double-charged,
and failed callbacks go unnoticed. PesaGuard closes that gap to seconds,
not days.

I already have an MVP scaffold (attached/provided). Build on top of it to
produce a **production-grade, deployable system**. Do not throw away the
existing structure — extend it.

### Non-negotiable requirements

1. **Correctness over speed.** Financial data. Every reconciliation decision
   must be auditable — log which rule fired, when, and why, for every
   transaction, not just the ones flagged as anomalies.
2. **Idempotency.** M-Pesa retries webhooks on timeout. The same `TransID`
   arriving twice must never be double-processed or double-alerted.
3. **No data loss.** If Kafka, Postgres, or the alerting service is down,
   incoming webhook events must not be dropped. Use a dead-letter queue or
   local buffering with retry.
4. **Multi-tenant from day one**, even if the first customer is the only
   tenant. Every table, topic, and API route should be scoped by
   `tenant_id` so onboarding customer #2 doesn't require a rewrite.

### 1. Authentication & connector layer (currently the biggest gap)

Implement real internal-ledger connectors, not just the abstract base class:

- **Postgres connector**: configurable table/column mapping per tenant
  (different customers name columns differently) — build a simple mapping
  config (YAML or DB-stored) rather than hardcoding column names.
- **Google Sheets connector**: OAuth2 service account flow, polling on an
  interval (default 2 min), with a documented rate-limit backoff strategy.
- **Generic REST connector**: for customers with their own API — configurable
  auth (API key or bearer token), field mapping, pagination handling.

Each connector must implement `fetch_recent_records()` from
`base_connector.py` and return the normalized shape already defined there.
Add a `ConnectorRegistry` that loads the right connector per tenant based on
config, so the reconciliation job doesn't need tenant-specific code.

### 2. Reconciliation logic — implement the real matching, not just anomaly flags

The MVP only flags anomalies within the M-Pesa stream itself (duplicates,
large amounts). Build the actual **cross-system matching**:

- Match incoming M-Pesa transaction to internal record by phone number +
  amount + time window (configurable, default ±15 min).
- Handle partial matches: amount matches but phone doesn't (family member
  paying on someone's behalf) — flag as `needs_review`, not `discrepancy`,
  since this is often legitimate.
- Handle the reverse case: internal record exists with no matching M-Pesa
  payment after the time window — this is the "money never arrived" case
  and is usually the highest-priority alert.
- Auto-resolve: if a late-arriving M-Pesa event matches a previously
  unresolved internal record, mark it resolved and note the resolution
  latency (useful for reporting reliability of Daraja callbacks over time).

### 3. Dashboard (real frontend, not just the API)

Build a Next.js frontend (or extend if scaffold provides one) with:

- **Live discrepancy feed** — table with filters (status, tenant, date range),
  real-time updates via polling or websockets.
- **Reconciliation rate chart** — daily/weekly trend, so the customer sees
  the tool earning its keep.
- **Manual resolution flow** — let an ops person mark a discrepancy resolved
  with a note (was it a false positive, genuinely fixed, etc.) — this data
  feeds back into tuning anomaly thresholds later.
- **Tenant settings page** — configure alert channels, thresholds, connector
  credentials.
- Auth: simple email/password or magic link is fine for MVP-to-production;
  don't over-build this.

### 4. Alerting — expand beyond Slack

- Add SMS via Africa's Talking (relevant for Kenyan ops teams who may not
  live in Slack).
- Add alert severity tiers: `info` (matched late but resolved),
  `warning` (needs_review), `critical` (money missing / no match after
  window).
- Add escalation: unresolved `critical` alerts re-notify after 30 min.
- Add a daily digest (total reconciled, open count, resolution rate) —
  this is often what actually gets read, versus real-time pings that get
  muted.

### 5. Observability & ops

- Structured logging (JSON) across all services, with `tenant_id` and
  `trans_id` as consistent fields for traceability.
- Health check endpoints for every service (webhook receiver, reconciliation
  job, dashboard API).
- Basic metrics: transactions/min, reconciliation latency (p50/p95),
  discrepancy rate — exposed via Prometheus-compatible `/metrics` endpoint
  if reasonable, otherwise a simple stats table the dashboard reads from.
- Document a runbook: what to do if Kafka lag grows, if a connector starts
  failing auth, if Daraja callback volume spikes unexpectedly.

### 6. Testing

- Unit tests for every anomaly rule and every matching scenario (exact
  match, partial match, no match, late match, duplicate).
- Integration test that runs the full pipeline against a docker-compose
  stack with fixture M-Pesa payloads (use realistic Daraja sandbox payload
  shapes).
- Load test script (even basic) simulating burst traffic — validate the
  system doesn't drop events under load.

### 7. Deployment

- Keep docker-compose for local dev.
- Add production deployment path: pick **one** — a single VM with
  docker-compose (simplest, fine for early customers) OR Kubernetes
  manifests if you expect >5 tenants soon. Don't build both; default to
  the VM path unless told otherwise.
- Add a basic CI pipeline (GitHub Actions): run tests, build images, on
  merge to main.
- Document secrets management — Daraja credentials, DB creds, connector
  OAuth tokens must never be committed; use environment injection.

### Constraints

- Keep Python for backend services (matches existing scaffold and my
  existing skill set).
- Prefer Postgres over BigQuery until there's a clear scale reason to
  switch — avoid premature infra complexity.
- Every new module should include a short docstring explaining what
  business problem it solves, not just what it does technically — this
  codebase will likely be read by future hires who aren't yet fintech
  domain experts.
- Flag anywhere you're making an assumption about M-Pesa/Daraja behavior
  that I should verify against real sandbox testing before trusting it in
  production.

### Deliverable

A single coherent monorepo (extending the existing `pesaguard/` structure),
with a top-level `SETUP.md` covering: environment setup, running locally,
running tests, and a checklist for onboarding a new pilot tenant end to end.

## PROMPT END
