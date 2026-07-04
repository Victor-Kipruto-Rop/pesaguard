# PesaGuard — Final Addendum: Tenant Provisioning, Threat Modeling, Feature Flags, Billing & Help Docs

This is the last layer on top of the Master Build Prompt and the Gaps
Addendum. It covers: tenant provisioning workflow, threat modeling,
per-tenant rule versioning/feature flags, billing/invoicing, and
end-user help documentation — plus a short documented PCI-DSS
applicability note you can hand to a customer who asks.

Use alongside the Master Build Prompt and Gaps Addendum — this doesn't
replace anything, it fills what's left.

---

## PART A — Technical Build Prompt

Copy everything between PROMPT START and PROMPT END into your coding agent.

### PROMPT START

You are adding the final operational layer to **PesaGuard**, a
multi-tenant M-Pesa reconciliation system. Implement in the order listed
— tenant provisioning is foundational, since threat modeling and billing
both assume a clean tenant lifecycle, and feature flags should exist
before rule versioning depends on them.

---

#### 1. Tenant Provisioning Workflow

Today, onboarding a tenant is a manual runbook checklist. Turn the
repeatable parts into an actual workflow so it scales past a handful of
manual onboardings without new engineering effort each time.

| ID | Requirement | Priority |
|---|---|---|
| PROV-1 | A `Tenant` creation flow (admin-triggered, not self-serve at this stage) that provisions: tenant record, default role assignments, default alert thresholds, empty connector config | Must |
| PROV-2 | Connector setup wizard (or at minimum a guided config form) so filling in a `PostgresConnector`/`GoogleSheetsConnector` config doesn't require editing raw JSON/YAML by hand | Should |
| PROV-3 | A `shadow_mode` flag per tenant — when true, discrepancies are logged and shown in the dashboard but alerts are suppressed. New tenants default to `shadow_mode = true` for their first week | Must |
| PROV-4 | Tenant status states: `provisioning`, `shadow`, `active`, `suspended`, `offboarded` — enforced via a state machine, not a free-text field | Should |
| PROV-5 | Provisioning actions logged to the audit trail (who provisioned, when, initial config) | Must |

**Files required:**
- `dashboard/api/services/tenant_provisioning.py`
- `dashboard/api/models/tenant_status.py` — state machine
- `dashboard/frontend/components/ConnectorSetupWizard.jsx`
- `tests/test_tenant_provisioning.py` — including a test that a tenant
  in `shadow` mode never triggers a customer-facing alert

---

#### 2. Threat Modeling

A dedicated pass on how the reconciliation logic itself could be attacked
or gamed — distinct from general API security already covered.

| ID | Requirement | Priority |
|---|---|---|
| THREAT-1 | Document threat scenarios specific to reconciliation logic: spoofed webhook events attempting to mask a real duplicate; a compromised internal-system connector feeding false "matched" records; replay of an old legitimate transaction to create a false match | Must |
| THREAT-2 | For each scenario, document the current mitigation (or explicitly note it's unmitigated and why that's currently acceptable) | Must |
| THREAT-3 | Verify webhook source validation (from the Gaps Addendum) actually defends against the spoofing scenario in THREAT-1 — write a test that attempts a spoofed payload and confirms rejection | Must |
| THREAT-4 | Review connector credential storage: if a connector's stored credentials leaked, what's the blast radius? Document it | Should |
| THREAT-5 | Revisit this document every time a new connector type or alert channel is added — it is a living document, not a one-time exercise | Should |

**Files required:**
- `THREAT_MODEL.md` — scenarios, mitigations, and open risks
- `tests/test_webhook_spoofing_rejection.py`

---

#### 3. Feature Flags & Per-Tenant Rule Versioning

Resolution-note data from the dashboard is meant to feed back into tuning
anomaly/matching thresholds. That only works safely if a rule change can
roll out to one tenant without affecting others.

| ID | Requirement | Priority |
|---|---|---|
| FLAG-1 | A feature-flag mechanism (simple per-tenant config table is enough — no need for a third-party flag service at this scale) | Must |
| FLAG-2 | Anomaly/matching rule thresholds (time window, large-amount threshold, etc.) are per-tenant config values, not global constants | Must |
| FLAG-3 | Rule version tagged on every discrepancy record — so if thresholds change later, historical decisions remain explainable under the rules that were active at the time | Must |
| FLAG-4 | A documented process for rolling out a rule change: enable for one tenant, observe for N days, then expand | Should |
| FLAG-5 | Rollback path: reverting a tenant to a previous rule version doesn't require a deploy, just a config change | Should |

**Files required:**
- `streaming/flink_jobs/rule_config.py` — per-tenant threshold loading
- `storage/models/rule_version.py` — version tagging on discrepancy records
- `RULE_ROLLOUT.md` — the rollout/rollback process

---

#### 4. Billing & Invoicing

Not needed for a free pilot, but needed the moment pricing (from the
Readiness checklist) is decided and a customer needs to actually pay.

| ID | Requirement | Priority |
|---|---|---|
| BILL-1 | Usage tracking per tenant: transactions processed per billing period (useful regardless of pricing model, even flat-fee) | Must |
| BILL-2 | Integration with a payment processor for recurring billing — evaluate Stripe (well-documented, handles international cards) vs. a local M-Pesa-based collection flow (may suit Kenyan SACCOs better); don't build both, pick one based on the actual pilot customers' preference | Must |
| BILL-3 | Invoice generation (PDF) per billing period, itemizing usage if pricing is volume-based | Should |
| BILL-4 | Dunning flow: what happens on a failed payment (grace period before `suspended` status from Section 1) | Should |
| BILL-5 | Billing data itself is tenant-scoped and access-controlled like everything else — a tenant should never see another tenant's invoice or usage data | Must |

**Files required:**
- `billing/usage_tracker.py`
- `billing/invoice_generator.py`
- `billing/payment_integration.py` (Stripe or M-Pesa, per decision above)
- `tests/test_billing_tenant_isolation.py`

**Note:** don't build this section until pricing is actually decided
(see Readiness checklist appendix). Building billing logic against an
undecided pricing model means rebuilding it once the real model is chosen.

---

#### 5. End-User Help Documentation

Separate from the OpenAPI/technical docs — this is for whoever on the
customer side isn't an engineer (e.g. a SACCO treasurer using the
dashboard).

| ID | Requirement | Priority |
|---|---|---|
| HELP-1 | A plain-language "Getting Started" guide: what a discrepancy means, how to resolve one, what the severity tiers mean | Must |
| HELP-2 | A short FAQ: common questions like "why was this flagged," "how do I add a team member," "how do I change alert settings" | Should |
| HELP-3 | In-dashboard contextual help (tooltips or a help panel) rather than requiring a separate document lookup for basic actions | Could |
| HELP-4 | Written at a reading level appropriate for a non-technical business owner, not an engineer — avoid jargon like "reconciliation window" without explanation | Must |

**Files required:**
- `docs/customer/GETTING_STARTED.md`
- `docs/customer/FAQ.md`

---

### Deliverable Summary (Part A)

```
dashboard/api/services/tenant_provisioning.py
dashboard/api/models/tenant_status.py
dashboard/frontend/components/ConnectorSetupWizard.jsx
THREAT_MODEL.md
streaming/flink_jobs/rule_config.py
storage/models/rule_version.py
RULE_ROLLOUT.md
billing/usage_tracker.py
billing/invoice_generator.py
billing/payment_integration.py
docs/customer/GETTING_STARTED.md
docs/customer/FAQ.md
tests/test_tenant_provisioning.py
tests/test_webhook_spoofing_rejection.py
tests/test_billing_tenant_isolation.py
```

### Constraints

- Build Section 1 (tenant provisioning) before relying on `shadow_mode`
  anywhere else in the system — every other section assumes it exists.
- Don't build Section 4 (billing) until pricing is actually decided;
  build the usage-tracking piece (BILL-1) early since it's useful
  regardless of pricing model, but hold off on payment integration.
- Threat modeling (Section 2) is a living document — schedule a revisit
  whenever a new connector type or alert channel is added, don't treat
  it as done once written.
- Feature flags (Section 3) should be the simplest mechanism that works
  — a per-tenant config table is enough; don't adopt a third-party
  flagging service at this scale.

### PROMPT END

---

## PART B — Reference Note (Non-Code)

### PCI-DSS Applicability

PesaGuard reconciles transaction metadata (amounts, phone numbers,
transaction IDs, timestamps) received from M-Pesa Daraja callbacks. It
does not touch, transmit, or store card data, and does not hold or move
funds itself — Safaricom's systems handle the actual payment processing.
On that basis, PCI-DSS is very unlikely to apply to PesaGuard directly.

This is a starting point for the conversation, not a compliance
determination — if a customer or partner asks formally, confirm this
reasoning with a qualified compliance professional before representing it
as settled, especially if PesaGuard's scope ever expands to include
initiating payments (e.g. B2C refunds) rather than only reconciling them.
