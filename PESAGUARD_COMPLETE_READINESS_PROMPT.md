# PesaGuard — Complete Readiness Prompt (Technical + Business)

This closes the remaining gaps beyond the core pipeline, alerting,
monitoring, and dashboards already specified. It has two parts:

- **Part A** is a build prompt for an AI coding agent — feed it directly.
- **Part B** is a checklist for you — these aren't things an AI agent can
  build, but they're required before you charge a real customer real money
  for handling their financial data.

---

## PART A — Technical Hardening Build Prompt

Copy everything between PROMPT START and PROMPT END into your coding agent.

### PROMPT START

You are hardening **PesaGuard**, a real-time M-Pesa reconciliation system,
across the operational areas not yet covered: backup/disaster recovery,
API protection, incident response tooling, data retention, and API
documentation. This is financial infrastructure for third-party
businesses — treat every gap here as something that becomes a real
incident, not a theoretical risk.

#### 1. Backup & Disaster Recovery

| ID | Requirement | Priority |
|---|---|---|
| BDR-1 | Automated daily Postgres backups (pg_dump or managed-provider snapshot) | Must |
| BDR-2 | Backups stored off the primary VM/instance (separate storage, e.g. object storage bucket) | Must |
| BDR-3 | Documented, tested restore procedure — not just "we take backups" | Must |
| BDR-4 | Backup retention policy (e.g. daily for 30 days, weekly for 6 months) | Should |
| BDR-5 | Quarterly restore drill: actually restore a backup to a scratch environment and verify integrity | Should |
| BDR-6 | Kafka topic retention configured deliberately (not left at default) so replay is possible after an incident | Should |

Write this as a `DISASTER_RECOVERY.md` with the actual commands to run a
restore, not just a description of the process — whoever runs this during
an incident will be stressed and needs copy-pasteable steps.

#### 2. API Protection

| ID | Requirement | Priority |
|---|---|---|
| API-1 | Rate limiting on the webhook receiver (protect against retry storms or abuse) | Must |
| API-2 | Rate limiting on the dashboard API | Must |
| API-3 | Request size limits on all endpoints | Must |
| API-4 | Daraja webhook endpoint validates source (IP allowlist or shared secret) before processing | Must |
| API-5 | Dashboard API auth tokens expire and can be revoked | Must |
| API-6 | All API errors return generic messages externally; detailed errors only in internal logs (avoid leaking schema/stack traces to callers) | Must |

#### 3. Incident Response

| ID | Requirement | Priority |
|---|---|---|
| INC-1 | On-call routing for operator alerts (even if "on-call" is just you — define how you get paged) | Must |
| INC-2 | Incident severity definitions (what counts as SEV1 vs SEV2 vs SEV3) | Should |
| INC-3 | Customer notification template for outages/incidents affecting their reconciliation | Should |
| INC-4 | Postmortem template — what happened, impact, root cause, follow-up actions | Should |
| INC-5 | A single `INCIDENT_RESPONSE.md` tying together: who gets paged, how to declare an incident, how to communicate status, how to close it out | Must |

#### 4. Data Retention & Deletion

| ID | Requirement | Priority |
|---|---|---|
| RET-1 | Documented retention period for transaction data, discrepancy records, and logs | Must |
| RET-2 | Automated deletion/archival job enforcing the retention policy | Should |
| RET-3 | Tenant offboarding process: what happens to a tenant's data when they churn (export + delete, with a defined grace period) | Must |
| RET-4 | Audit log itself has its own retention rule, separate from operational data (audit trails often need to be kept longer) | Should |

#### 5. API Documentation

| ID | Requirement | Priority |
|---|---|---|
| DOC-1 | OpenAPI/Swagger spec for the dashboard API, if any pilot customer wants programmatic access | Should |
| DOC-2 | Auto-generated interactive docs (e.g. Swagger UI) served from a docs endpoint | Could |
| DOC-3 | Webhook payload reference for internal engineering use (already partly covered by existing docs — extend, don't duplicate) | Should |

#### Deliverable

- `DISASTER_RECOVERY.md` with tested, copy-pasteable restore steps
- `INCIDENT_RESPONSE.md` with severity definitions, paging, and postmortem template
- `DATA_RETENTION.md` documenting retention periods and the offboarding process
- Rate limiting and request validation implemented on both the webhook
  receiver and dashboard API
- OpenAPI spec for the dashboard API if programmatic customer access is planned

#### Constraints

- Don't over-engineer disaster recovery for a one-tenant pilot — a daily
  backup with a tested restore is enough; don't build multi-region
  failover at this stage.
- Flag any retention period you choose as a placeholder needing sign-off
  once real contractual/compliance requirements are known — don't invent
  a number and treat it as final.

### PROMPT END

---

## PART B — Business & Operational Readiness Checklist

These aren't buildable by a coding agent, but they're required before
PesaGuard handles real money for a real business. None of this is legal
advice — treat every "draft" item below as a starting point for a
qualified professional to review, not a final document.

### Legal & Compliance

- [ ] **Terms of Service** — governs the relationship with each business
  customer; especially important given you're handling their financial
  reconciliation data.
- [ ] **Privacy Policy** — how customer and end-user (payer) data is
  collected, used, and protected.
- [ ] **Data Processing Agreement (DPA)** — SACCOs and fintechs will likely
  ask who's liable if reconciliation misses something or data leaks.
  Defines your role as data processor vs. controller.
- [ ] **ODPC registration** — Kenya's Data Protection Act requires
  registration as a data controller/processor above a certain scale;
  check current thresholds on the [ODPC website](https://www.odpc.go.ke/).
- [ ] **Liability / E&O consideration** — you are the system a business
  relies on to catch missing money; worth a conversation with an insurance
  broker or lawyer about errors & omissions coverage before scaling past
  a free pilot.

### Commercial

- [ ] **Pricing/packaging** — flat monthly fee, per-transaction, or
  tiered by volume. Consider what a SACCO vs. an e-commerce operator can
  actually afford and how their transaction volume differs.
- [ ] **Pilot agreement** — even a simple one-page agreement for the free/
  discounted pilot period, defining scope, duration, and what happens
  after (convert to paid, or end).
- [ ] **Support channel** — explicit definition of how a pilot customer
  reaches you (shared Slack channel is fine at this scale) and expected
  response time, even informally.
- [ ] **SLA (once paid)** — uptime commitment, alert delivery time
  commitment, what happens if you miss it.

### Operational

- [ ] **Onboarding checklist** for tenant #2+ — connector setup, threshold
  configuration, alert channel setup, a shadow-mode period before going live.
- [ ] **Offboarding checklist** — tied to the data retention policy above.
- [ ] **Status page** (even a simple one) — so customers can self-check
  system health during an incident instead of all routing through you.

---

### Suggested Next Step

Rather than doing all of Part B at once, the highest-leverage first moves
are usually:
1. A DPA + minimal ToS/Privacy Policy draft (needed the moment a real
   pilot customer's data touches the system)
2. A one-page pilot agreement
3. Pricing worked out well enough to have the conversation with pilot
   candidates, even if it changes later

I can draft a first-pass version of any of these — the DPA and pilot
agreement are the most time-sensitive given you're already building
toward a real pilot customer. Want me to start with those?
