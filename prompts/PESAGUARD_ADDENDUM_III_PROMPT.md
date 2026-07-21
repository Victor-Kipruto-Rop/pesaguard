# PesaGuard — Addendum III: Data Residency, Localization & Payment-Method Scope

This is the third and likely final layer on top of the Master Build
Prompt, the Gaps Addendum, and the Tenant/Threat/Billing Addendum. It
covers three items that are different in kind from what's come before:
data residency (a compliance/hosting decision), localization (a product
decision), and explicit scope-setting around non-M-Pesa payment methods
(a business decision with technical consequences).

Use alongside the prior three prompts — this doesn't replace anything.

---

## PART A — Technical Build Prompt

Copy everything between PROMPT START and PROMPT END into your coding agent.

### PROMPT START

You are addressing three cross-cutting concerns in **PesaGuard**, a
multi-tenant M-Pesa reconciliation system: data residency compliance,
Swahili localization, and explicit scope boundaries around payment
methods beyond M-Pesa. Each is independent; implement in the order
listed since hosting (Section 1) constrains later infrastructure choices.

---

#### 1. Data Residency

Kenya's Data Protection Act includes restrictions on cross-border
transfer of personal data. If PesaGuard's infrastructure ends up hosted
outside Kenya (e.g. a default AWS/GCP region), this is a compliance
question, not just an operational detail — treat it as such rather than
inheriting whatever region a cloud provider defaults to.

| ID | Requirement | Priority |
|---|---|---|
| RES-1 | Document where each category of tenant data is physically stored (Postgres, Kafka, backups, logs) and which jurisdiction that falls under | Must |
| RES-2 | Evaluate hosting options with an explicit Kenya/East-Africa region if one exists from the chosen cloud provider, or a local hosting provider, and document the tradeoff versus a default region | Must |
| RES-3 | If any cross-border data transfer is unavoidable (e.g. a managed service only available in another region), document the legal basis under Kenya's Data Protection Act for that transfer | Must |
| RES-4 | Backups inherit the same residency constraints as primary data — don't let backup storage quietly violate a residency decision made for primary storage | Must |
| RES-5 | Make the hosting region a per-deployment config decision, not hardcoded, so different tenants' residency requirements could theoretically be satisfied differently in the future | Could |

**Files required:**
- `DATA_RESIDENCY.md` — documents storage locations, jurisdiction, and
  legal basis for any cross-border transfer
- Update `infra/docker-compose.yml` / production deployment docs to note
  the chosen hosting region and why

**Constraint:** this section is primarily a documentation and decision
exercise, not new code. Do not over-engineer a multi-region architecture
before there's a real requirement for one — the deliverable is a clear,
correct decision and its written justification, not new infrastructure.

---

#### 2. Swahili Localization

Dashboard and alert text are currently English-only. For a SACCO
treasurer or small business owner, Kiswahili may matter more than most
technical features already specified.

| ID | Requirement | Priority |
|---|---|---|
| LOC-1 | Extract all customer-facing strings (dashboard UI, alert message templates, help docs) into translatable resource files rather than hardcoded text | Must |
| LOC-2 | Kiswahili translation of: dashboard UI, Slack/SMS alert templates, the Getting Started guide and FAQ from the prior addendum | Must |
| LOC-3 | Per-tenant (or per-user) language preference, defaulting to English but switchable to Kiswahili | Must |
| LOC-4 | SMS alerts respect the language preference — critical for the SMS channel specifically, since it's often the least technical audience touchpoint | Must |
| LOC-5 | Date/time and currency formatting remain Kenya-appropriate regardless of language (KES formatting, EAT timezone) — don't let localization accidentally change these | Should |

**Files required:**
- `dashboard/frontend/locales/en.json`
- `dashboard/frontend/locales/sw.json`
- `alerting/templates/slack_template_sw.md`
- `alerting/templates/sms_template_sw.md`
- `docs/customer/GETTING_STARTED_sw.md`
- `docs/customer/FAQ_sw.md`
- `tests/test_localization_fallback.py` — verify missing translations
  fall back to English rather than showing a raw key or breaking

**Constraint:** don't build a general-purpose i18n framework for
hypothetical future languages. Two languages (English, Kiswahili) is the
actual requirement — use a standard library (e.g. `next-i18next` for the
Next.js dashboard) rather than a custom solution, but don't design for
languages beyond what's needed now.

---

#### 3. Payment-Method Scope Boundary

PesaGuard is Daraja-only today. Pilot customers who also take Airtel
Money or bank transfers will still have an unreconciled gap outside
M-Pesa. This needs an explicit decision, documented and reflected in the
product itself — not silently discovered by a confused customer.

| ID | Requirement | Priority |
|---|---|---|
| SCOPE-1 | Document the current scope decision explicitly: M-Pesa/Daraja only, or intended to expand — and if expansion is intended, to which payment methods and on what timeline | Must |
| SCOPE-2 | The dashboard and onboarding materials state the scope boundary clearly, so a customer taking Airtel Money or bank transfers understands upfront what is and isn't reconciled | Must |
| SCOPE-3 | If expansion beyond M-Pesa is the intended direction, the BaseConnector pattern already used for internal-ledger connectors should be evaluated for reuse as a PaymentSourceConnector pattern — don't hardcode M-Pesa-specific assumptions into core reconciliation logic where avoidable | Should |
| SCOPE-4 | If a pilot customer explicitly needs multi-payment-method reconciliation now, treat that as a distinct scoping conversation and a likely separate phase — do not silently expand scope mid-build without re-running the requirements process | Must |

**Files required:**
- `PRODUCT_SCOPE.md` — the explicit scope decision, reasoning, and any
  planned expansion path
- Update `docs/customer/GETTING_STARTED.md` (and its Kiswahili
  counterpart) to state the scope boundary in plain language

**Constraint:** do not build multi-payment-method support speculatively.
This section's primary deliverable is a decision and its documentation,
not new payment integrations, unless a real pilot customer's requirement
makes the expansion concrete and justified.

---

### Deliverable Summary (Part A)

```
DATA_RESIDENCY.md
PRODUCT_SCOPE.md
dashboard/frontend/locales/en.json
dashboard/frontend/locales/sw.json
alerting/templates/slack_template_sw.md
alerting/templates/sms_template_sw.md
docs/customer/GETTING_STARTED_sw.md
docs/customer/FAQ_sw.md
tests/test_localization_fallback.py
```

### Constraints (apply to all three sections)

- All three sections above are decision-and-documentation-heavy, not
  pure engineering. Resist the instinct to over-build (multi-region
  infra, general i18n framework, speculative payment integrations)
  before a real, stated requirement justifies it.
- Where a decision depends on information you don't have (e.g. which
  cloud region is genuinely cheapest/most reliable for Kenya, whether a
  specific pilot customer needs Airtel Money), flag it explicitly as
  "pending real-world input" rather than guessing and presenting the
  guess as settled.
- Localization (Section 2) and scope documentation (Section 3) should
  both be validated with an actual Kiswahili-speaking user or a real
  pilot candidate before being treated as final.

### PROMPT END

---

## PART B — Suggested Validation Questions for Phase 0

Since all three items above are best resolved through real conversations
rather than more planning, fold these into the Phase 0 discovery
conversations already planned:

- "Would you prefer to use this dashboard in Kiswahili, English, or both?"
- "Is it important to you that your data is stored in Kenya specifically,
  or does that not matter to your business?"
- "Besides M-Pesa, do you take payments through Airtel Money, bank
  transfer, or anything else we'd need to reconcile as well?"

These three questions alone will resolve most of the open decisions in
this addendum faster and more reliably than further upfront speccing.
