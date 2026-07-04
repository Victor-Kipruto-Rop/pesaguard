# PesaGuard — Gaps Addendum: Build Prompt

This closes the remaining gaps identified after the master build prompt:
Daraja OAuth token management, a staging environment, dependency
vulnerability scanning, RBAC + action audit in the dashboard, data export,
API versioning, and secrets rotation. It also covers two non-code items
(SMS sender ID registration, trademark/domain) that need action but not an
AI agent.

Use this alongside the Master Build Prompt — it doesn't replace any phase,
it fills gaps that phase didn't cover in detail.

---

## PART A — Technical Build Prompt

Copy everything between PROMPT START and PROMPT END into your coding agent.

### PROMPT START

You are closing operational gaps in **PesaGuard**, a multi-tenant M-Pesa
reconciliation system. Each section below is independent — implement them
in the order listed, since later ones (e.g. RBAC) build on earlier
foundational pieces (e.g. staging environment to test changes safely).

---

#### 1. Daraja OAuth Token Management

Needed the moment PesaGuard calls Daraja APIs itself (transaction status
queries, B2C refunds) rather than only receiving webhooks. Daraja access
tokens expire hourly.

| ID | Requirement | Priority |
|---|---|---|
| OAUTH-1 | A `DarajaAuthClient` that fetches and caches an access token, refreshing before expiry (not on-failure only) | Must |
| OAUTH-2 | Token cached in Redis (shared across service instances) with TTL matching Daraja's expiry minus a safety margin | Must |
| OAUTH-3 | Automatic retry-with-refresh if a Daraja API call returns a 401 (token expired early/revoked) | Must |
| OAUTH-4 | Per-tenant Daraja credentials support (different tenants may have different Daraja apps) | Should |
| OAUTH-5 | Consumer key/secret never logged, even at debug level | Must |

**Files required:**
- `shared/daraja/auth_client.py` — token fetch, cache, refresh logic
- `shared/daraja/config.py` — per-tenant credential loading
- `tests/test_daraja_auth.py` — token refresh and 401-retry test coverage

---

#### 2. Staging Environment

Everything built so far distinguishes local dev from production. Add a
middle tier to test changes against Daraja sandbox before they touch a
real pilot's data.

| ID | Requirement | Priority |
|---|---|---|
| STG-1 | A `staging` deployment target, same docker-compose-based architecture as production but pointed at Daraja sandbox | Must |
| STG-2 | Staging uses its own isolated Postgres/Kafka/Redis — never shares data with production | Must |
| STG-3 | CI deploys to staging automatically on merge to a `staging` branch; production deploy requires a manual promotion step | Should |
| STG-4 | Seed/fixture data for staging so reconciliation logic can be exercised without a real tenant's data | Should |

**Files required:**
- `infra/docker-compose.staging.yml`
- `.env.staging.example`
- `.github/workflows/deploy-staging.yml`
- `scripts/seed_staging_data.py`

---

#### 3. Dependency Vulnerability Scanning

| ID | Requirement | Priority |
|---|---|---|
| DEP-1 | Dependabot (or equivalent) configured for all services' dependency manifests | Must |
| DEP-2 | `pip-audit` (Python) run in CI on every PR; fail the build on high/critical findings | Must |
| DEP-3 | `npm audit` (or equivalent) run in CI for the Next.js dashboard | Must |
| DEP-4 | A documented process for triaging findings that can't be fixed immediately (accepted risk, tracked, revisited) | Should |

**Files required:**
- `.github/dependabot.yml`
- `.github/workflows/dependency-scan.yml`
- `SECURITY.md` — updated with the vulnerability triage process

---

#### 4. RBAC & Action Audit in the Dashboard

Current "simple auth" doesn't distinguish roles. Add this before onboarding
a tenant with more than one dashboard user.

| ID | Requirement | Priority |
|---|---|---|
| RBAC-1 | At least two roles per tenant: `admin` (can edit settings/connectors) and `viewer` (can view and resolve discrepancies, not edit config) | Must |
| RBAC-2 | Every mutating dashboard action (resolve discrepancy, edit settings, invite user) is written to an action audit log: who, what, when, tenant | Must |
| RBAC-3 | Action audit log viewable by tenant `admin` role only | Should |
| RBAC-4 | Role checks enforced server-side on every API route, not just hidden in the frontend UI | Must |

**Files required:**
- `dashboard/api/models/roles.py` — role definitions and permission checks
- `dashboard/api/models/action_audit.py` — audit log model
- `dashboard/frontend/components/AuditLogView.jsx`
- `tests/test_rbac_enforcement.py` — verify a `viewer` cannot hit admin-only routes even by direct API call

---

#### 5. Data Export

Customers will want their reconciliation history outside the live
dashboard view.

| ID | Requirement | Priority |
|---|---|---|
| EXP-1 | CSV export of transactions and discrepancies, filterable by date range | Must |
| EXP-2 | Export respects tenant scoping — no cross-tenant data possible even via crafted requests | Must |
| EXP-3 | Large exports handled asynchronously (generate + email/download link) rather than blocking the request | Should |

**Files required:**
- `dashboard/api/routes/export.py`
- `dashboard/frontend/components/ExportButton.jsx`
- `tests/test_export_tenant_scoping.py`

---

#### 6. API Versioning

Matters once external customers integrate against the dashboard API
directly (tied to Data Export and any future public API).

| ID | Requirement | Priority |
|---|---|---|
| VER-1 | All dashboard API routes namespaced under `/v1/...` from the start | Must |
| VER-2 | A documented deprecation policy (e.g. minimum 90 days notice before removing a version) | Should |
| VER-3 | Version included in the OpenAPI spec (from the earlier documentation phase) | Should |

**Files required:**
- Update existing route files to nest under `/v1/`
- `API_VERSIONING.md` — deprecation policy

---

#### 7. Secrets Rotation

| ID | Requirement | Priority |
|---|---|---|
| ROT-1 | Documented rotation schedule for DB credentials, Daraja API keys, Slack/SMS webhook tokens (e.g. every 90 days) | Should |
| ROT-2 | Rotation process doesn't require downtime (support two valid credentials briefly during rotation, where the provider allows it) | Should |
| ROT-3 | Rotation events themselves logged to the audit trail | Could |

**Files required:**
- `SECRETS_ROTATION.md` — schedule and step-by-step rotation procedure per secret type

---

### Deliverable Summary (Part A)

```
shared/daraja/auth_client.py
shared/daraja/config.py
infra/docker-compose.staging.yml
.env.staging.example
.github/workflows/deploy-staging.yml
.github/workflows/dependency-scan.yml
.github/dependabot.yml
scripts/seed_staging_data.py
dashboard/api/models/roles.py
dashboard/api/models/action_audit.py
dashboard/api/routes/export.py
dashboard/frontend/components/AuditLogView.jsx
dashboard/frontend/components/ExportButton.jsx
SECURITY.md (updated)
API_VERSIONING.md
SECRETS_ROTATION.md
tests/test_daraja_auth.py
tests/test_rbac_enforcement.py
tests/test_export_tenant_scoping.py
```

### Constraints

- Implement staging (Section 2) before RBAC/export changes land, so those
  changes can be tested against sandbox data before touching production.
- Don't build a custom secrets manager — use environment injection plus a
  documented manual rotation process at this scale; a full secrets-manager
  integration (Vault, AWS Secrets Manager) is justified only once tenant
  count or team size makes manual rotation impractical.
- Flag anywhere a rotation interval or deprecation window is a placeholder
  guess rather than a value confirmed against real provider constraints
  (e.g. Daraja key rotation process, Africa's Talking token behavior).

### PROMPT END

---

## PART B — Non-Code Action Items

Not buildable by an agent, but each has a concrete next step.

### SMS Sender ID Registration (Kenya)

Bulk/transactional SMS sent via Africa's Talking in Kenya typically
requires sender ID registration with the Communications Authority. This
directly affects the alerting system (Phase 3 of the Master Build Prompt)
— `critical` alerts routed to SMS won't work correctly without it.

**Next step:** check Africa's Talking's current sender ID registration
process and Communications Authority requirements before relying on SMS
alerts in production. Budget lead time for this — registration is not
usually instant.

### Trademark / Domain Check

Before "PesaGuard" appears on real invoices or a pilot agreement:

- [ ] Search the Kenya Industrial Property Institute (KIPI) trademark
  database for conflicts
- [ ] Confirm domain availability (.com, .co.ke)
- [ ] Confirm no existing fintech product is already using the name in a
  way that could cause confusion or a takedown request

None of this is legal advice — a trademark search through KIPI directly,
or a quick consult with a lawyer, is the reliable way to confirm this
before it's on a contract.
