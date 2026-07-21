# PesaGuard Assistant — Full Implementation Roadmap

An AI agent layer for customers and internal users to query, understand, and act on reconciliation and anomaly data conversationally. Read-only and advisory by design — never autonomous over money movement.

---

## Phase 0 — Prerequisites (must be true before starting this at all)
- [ ] Core reconciliation engine stable and trusted (no known data-integrity bugs)
- [ ] Webhook idempotency shipped and verified
- [ ] At least one full month of clean transaction/anomaly data to ground answers in
- [ ] Audit log subsystem in place (the assistant's answers must be checkable against it)

**Do not start Phase 1 until these are true.** An assistant answering questions about unreliable data is worse than no assistant.

---

## Phase 1 — Read-Only Query Assistant (MVP)
**Goal:** answer questions about existing data. No actions, no writes.

- [ ] Define a fixed set of supported query types first (don't allow fully open-ended queries yet):
  - "Show unmatched transactions from [date range]"
  - "Why was transaction [ID] flagged?"
  - "Summarize reconciliation status for [period]"
  - "List anomalies by severity for [period]"
- [ ] Backend: agent calls existing internal APIs/DB queries — never lets the model generate SQL directly against production data
- [ ] All numeric answers must be sourced from an actual query result, not generated from the model's "reasoning" — include the underlying data alongside the answer so it's checkable
- [ ] Access control: agent respects the same RBAC as the dashboard — a user can't ask their way into data they can't otherwise see
- [ ] Logging: every query + answer logged, tied to user, for audit and for catching hallucination early
- [ ] Simple chat UI panel in the dashboard (collapsible sidebar or modal)

**Success criteria:** internal team uses it daily and trusts the numbers without double-checking manually.

---

## Phase 2 — Explanatory / Triage Assistant
**Goal:** help non-technical users understand *why*, not just *what*.

- [ ] Anomaly explanation in plain language, generated from the actual rule/score that fired (e.g. "flagged because amount is 3.2x this account's 30-day average and occurred at 2am") — template-grounded, not free-form guessing
- [ ] Suggested next step per anomaly type ("Recommend confirming with the account holder" / "Recommend checking for a duplicate STK push") — advisory language only, never directive/automatic
- [ ] "Explain this reconciliation mismatch" for a specific unmatched pair
- [ ] Feedback mechanism: user marks explanation as helpful/not — used to improve prompt templates, not to auto-retrain a model

**Success criteria:** SACCO staff resolve anomalies faster without escalating every one to you.

---

## Phase 3 — Onboarding & Setup Assistant
**Goal:** reduce manual onboarding load as customer count grows.

- [ ] Guided setup conversation for connecting Daraja credentials, explaining each field
- [ ] Answers general "how does PesaGuard work" / "what does this status mean" questions
- [ ] Escalates to a human (you) when it doesn't have a confident answer — never guesses on credential/config specifics
- [ ] No write access to credentials itself — it explains, the human/customer still enters the actual values

**Success criteria:** a new customer can self-serve through initial setup with fewer support messages to you.

---

## Phase 4 — Report Generation on Demand
**Goal:** natural-language report requests instead of manual filter navigation.

- [ ] "Generate a reconciliation summary for June" → pulls the same data the Reports page would, formats it, offers PDF/CSV export
- [ ] Scheduled natural-language reports ("send me this every Monday") — still just triggers the existing scheduled report subsystem, not a new pipeline
- [ ] No new data source — this phase should reuse Phase 1's query layer entirely

**Success criteria:** reduces time-to-report for both you and customers without duplicating report logic.

---

## Explicitly Out of Scope (any phase)
- Autonomous approval/rejection of reconciliation matches
- Autonomous account locking, transaction reversal, or fraud declaration
- Write access to Daraja credentials or payment rails
- Free-form SQL generation against production data
- Any action that moves money or changes account status without a human confirming first

---

## Cross-Phase Guardrails (non-negotiable throughout)
1. **Groundedness over fluency** — every factual/numeric claim must trace to an actual query result, never model-generated numbers
2. **RBAC-respecting** — the assistant is a lens on data the user could already see, not a bypass
3. **Full logging** — every interaction auditable, same as any other system action
4. **Human confirmation gate** — anything beyond "read and explain" requires an explicit human action outside the chat

---

## Suggested Trigger to Start Phase 1
Not a date — a condition: **core system (reconciliation + idempotency + audit log) has run cleanly against real pilot customer data for at least 2–4 weeks with no data-integrity incidents.** Building the assistant before that just adds a conversational layer on top of an unproven foundation.
