# PesaGuard — Alerting, Monitoring & Dashboards Build Prompt

A focused, self-contained prompt for an AI coding agent to build out the
three pillars that make PesaGuard trustworthy in production: **alerting**
(getting the right people notified), **monitoring** (knowing the system
itself is healthy), and **dashboards** (both operational and customer-facing
visibility). Pair with the existing MVP scaffold or the full production
prompt — this one goes deep on just these three areas.

Copy everything between PROMPT START and PROMPT END into your agent.

---

## PROMPT START

You are extending **PesaGuard**, a real-time M-Pesa reconciliation and
anomaly detection system, to be production-strong across three areas:
**alerting**, **monitoring/observability**, and **dashboards** (both an
internal operational view and a customer-facing product view).

This is financial infrastructure. A silent failure here means money goes
missing without anyone noticing — that's the exact problem PesaGuard
exists to prevent, so the system monitoring PesaGuard itself must be at
least as reliable as the reconciliation logic it watches.

---

### 1. Alerting System

**Goal:** the right person is notified of the right thing, at the right
urgency, without alert fatigue burning out trust in the system.

**Requirements:**

| ID | Requirement | Priority |
|---|---|---|
| AL-1 | Multi-channel delivery: Slack, SMS (Africa's Talking), email | Must |
| AL-2 | Severity tiers: `info`, `warning`, `critical` — each with its own channel routing | Must |
| AL-3 | `critical` alerts (e.g. money missing, no match after window) go to SMS + Slack simultaneously | Must |
| AL-4 | `warning` alerts (e.g. needs_review, partial match) go to Slack only | Must |
| AL-5 | `info` alerts (e.g. late match auto-resolved) go to a digest, not real-time | Should |
| AL-6 | Escalation: unresolved `critical` alerts re-notify every 30 minutes until resolved or acknowledged | Must |
| AL-7 | Acknowledgement flow: someone can mark an alert "seen" without fully resolving it, stopping escalation | Should |
| AL-8 | Daily digest: total transactions, open discrepancies, resolution rate, sent once per day per tenant | Should |
| AL-9 | Per-tenant configurable channels (one customer wants SMS, another only wants Slack) | Must |
| AL-10 | Alert deduplication — the same discrepancy must not trigger duplicate notifications across retries | Must |
| AL-11 | Every alert sent is logged (channel, recipient, timestamp, delivery success/failure) for audit | Must |

**Design notes:**
- Don't let alerting logic live inside the reconciliation job. Emit
  discrepancy events to a dedicated topic/queue; a separate alerting
  service consumes them and handles routing, tiering, and escalation.
  This keeps the reconciliation job simple and lets you change alerting
  behavior without touching matching logic.
- Alert fatigue is a real failure mode — if `info`-tier events get
  pushed in real-time, customers will mute the channel and miss the
  `critical` one that matters. Be disciplined about the tiering.

---

### 2. Monitoring & Observability

**Goal:** you know the system itself is healthy before a customer has to
tell you it isn't.

**Requirements:**

| ID | Requirement | Priority |
|---|---|---|
| MON-1 | Health check endpoint (`/health`) on every service | Must |
| MON-2 | Structured JSON logging across all services, with `tenant_id` and `trans_id` as consistent correlated fields | Must |
| MON-3 | Prometheus-compatible `/metrics` endpoint on every service | Must |
| MON-4 | Track: transactions/min, reconciliation latency (p50/p95/p99), discrepancy rate, Kafka consumer lag | Must |
| MON-5 | Track: alert delivery success/failure rate per channel | Must |
| MON-6 | Track: connector health per tenant (last successful sync, error rate) | Must |
| MON-7 | Alert-on-monitoring: if Kafka lag exceeds a threshold, or a connector fails repeatedly, or the reconciliation job stops consuming, alert the *operator* (you), not the customer | Must |
| MON-8 | Grafana dashboards visualizing all of the above, provisioned as code (not manually clicked together) | Should |
| MON-9 | Log retention and rotation policy documented, even if simple | Should |
| MON-10 | A written runbook: what to check and do when Kafka lag grows, a connector starts failing auth, or Daraja callback volume spikes unexpectedly | Should |

**Design notes:**
- Use Prometheus + Grafana as the default stack. Don't reach for a paid
  SaaS observability tool at this stage — the operational need is
  simple enough that the open-source stack is the right level of
  investment.
- Structured logs should be queryable by `tenant_id` and `trans_id`
  together, since debugging a specific customer's specific transaction
  is the most common investigation you'll do.
- Distinguish clearly between **customer-facing alerts** (Section 1 —
  "your transaction didn't reconcile") and **operator-facing alerts**
  (this section — "the system watching transactions is itself unhealthy").
  These must never share a channel; conflating them means an
  operational page looks like a customer notification, or vice versa.

---

### 3. Dashboards

Two distinct dashboards with different audiences — do not merge them.

#### 3a. Operational Dashboard (Grafana) — for you

**Requirements:**
- Kafka consumer lag over time
- Reconciliation latency (p50/p95/p99) over time
- Transactions processed per minute
- Discrepancy rate and breakdown by anomaly type
- Alert delivery success rate per channel
- Per-tenant connector health (last sync time, error count)
- Provisioned via Grafana dashboard-as-code (JSON model or Terraform),
  not manually built through the UI, so it's reproducible and versioned

#### 3b. Customer-Facing Dashboard (Next.js) — for the pilot tenant

**Requirements:**

| ID | Requirement | Priority |
|---|---|---|
| DASH-1 | Live discrepancy feed with filters (status, date range) | Must |
| DASH-2 | Discrepancy detail view showing the matching decision and why it was flagged (auditability, not just a status) | Must |
| DASH-3 | Manual resolution flow — mark resolved with a note | Must |
| DASH-4 | Reconciliation rate chart (daily/weekly trend) | Should |
| DASH-5 | Tenant settings page: alert channel configuration, thresholds, connector credentials | Must |
| DASH-6 | Simple auth (email/password or magic link) — don't over-build this | Must |
| DASH-7 | Every view and API call scoped to the authenticated tenant only | Must |

**Design notes:**
- The resolution-note data customers enter (DASH-3) should feed back
  into tuning anomaly thresholds later — capture it in a structured way
  (reason category + free text), not just a blob.
- Keep this dashboard read-and-annotate focused. It is not meant to be
  a full admin panel — connector credential editing (DASH-5) is the
  only "configuration" surface; everything else is observation and
  resolution.

---

### 4. Tech Stack for This Scope

| Purpose | Tool |
|---|---|
| Metrics collection | Prometheus |
| Metrics visualization | Grafana (dashboards provisioned as code) |
| Log aggregation | Structured JSON logs; Grafana Loki if you want log search alongside metrics, otherwise `docker-compose logs` is enough at pilot scale |
| Alert routing/escalation | Custom alerting service (Python) consuming a Kafka discrepancy topic |
| SMS | Africa's Talking |
| Email | Any SMTP provider or a transactional email API (e.g. SendGrid) |
| Customer dashboard frontend | Next.js + React |
| Customer dashboard backend | Existing Flask/DRF dashboard API, extended |
| Operator alerting (monitoring-on-monitoring) | Prometheus Alertmanager, or route Grafana alerts to a dedicated Slack channel separate from customer alerts |

Don't introduce a paid observability SaaS (Datadog, New Relic, etc.) at
this stage — the open-source stack above is sufficient and keeps
operating cost near zero during the pilot.

---

### 5. Architecture

```
Reconciliation Job
     |
     |  discrepancy events
     v
Kafka: mpesa.discrepancies
     |
     v
Alerting Service ---------------------------+
     |  routes by severity tier             |
     +--> Slack (warning, critical)         |
     +--> SMS via Africa's Talking (critical)|
     +--> Email digest (info, daily)         |
     |                                       |
     v                                       v
Alert Delivery Log (Postgres)      Escalation Scheduler
                                    (re-notify unresolved critical)

--- separately ---

All services --> /metrics --> Prometheus --> Grafana
                                    |
                                    v
                         Operator Alertmanager
                         (Kafka lag, service down,
                          connector failing)
                                    |
                                    v
                         Separate ops Slack channel
                         (never the customer channel)

--- separately ---

Postgres (transactions, discrepancies, audit log)
     |
     v
Dashboard API (Flask/DRF, tenant-scoped)
     |
     v
Next.js Customer Dashboard
```

---

### 6. Build Phases for This Scope

**Phase A — Alerting Service (Week 1)**
Extract alerting into its own service consuming
`mpesa.discrepancies`. Implement severity tiering, multi-channel
routing, per-tenant channel config, dedup, and alert-delivery logging.

**Phase B — Escalation & Digest (Week 2)**
Escalation scheduler for unresolved `critical` alerts. Acknowledgement
flow. Daily digest job per tenant.

**Phase C — Monitoring Foundations (Week 3)**
`/metrics` endpoints on every service. Structured JSON logging with
correlated `tenant_id`/`trans_id`. Prometheus scraping config.

**Phase D — Operator Alerting (Week 4)**
Prometheus Alertmanager (or equivalent) rules for Kafka lag, service
health, connector failure. Route to a separate ops-only Slack channel.
Write the runbook.

**Phase E — Grafana Dashboards (Week 5)**
Provision operational dashboards as code: latency, throughput,
discrepancy rate, alert delivery rate, per-tenant connector health.

**Phase F — Customer Dashboard (Weeks 6-7)**
Next.js frontend: discrepancy feed, detail view, resolution flow,
reconciliation chart, tenant settings, auth, tenant scoping on every
route.

**Phase G — Hardening (Week 8)**
Load test the alerting path specifically (burst of discrepancies
shouldn't flood a channel or drop deliveries). Verify escalation timing
under test. Confirm operator alerts and customer alerts never
cross-contaminate channels.

---

### 7. Testing Requirements

- Unit tests for severity tiering and channel-routing logic
- Test that duplicate discrepancy events don't produce duplicate alerts
- Test escalation timing (unresolved critical alert re-fires on schedule,
  stops after acknowledgement/resolution)
- Test that a burst of discrepancies doesn't silently drop any alert
  deliveries
- Test tenant isolation on every customer dashboard API route
- Test that operator alerts (Kafka lag, service down) route to the ops
  channel only, never the customer-facing channel, and vice versa

---

### 8. Deliverable

- Alerting service as its own deployable component, documented
  separately from the reconciliation job
- Grafana dashboard JSON models (or Terraform) committed to the repo,
  reproducible from scratch
- A `RUNBOOK.md` covering the operator scenarios in MON-10
- Next.js customer dashboard, tenant-scoped throughout
- Updated `SETUP.md` covering how to run Prometheus/Grafana locally
  alongside the existing docker-compose stack

### 9. Constraints

- Keep operator-facing and customer-facing alerting fully separate —
  different services, different channels, different Slack workspaces
  or channels if using Slack for both.
- Don't build a custom metrics/dashboard system — Prometheus + Grafana
  is the right level of tooling here; resist the urge to build a bespoke
  admin panel for operational metrics.
- Flag anywhere you're guessing at reasonable alert thresholds (e.g.
  Kafka lag threshold, escalation interval) — these should be tunable
  config, not hardcoded assumptions, since the right values will only
  become clear from real pilot usage.

## PROMPT END
