# PesaGuard — Full System Build Prompt

Use this as a **reference architecture**, not a single build sprint. Feed one subsystem at a time to your coding agent, prioritized by what your live pilot customer actually needs next.

## System Overview

PesaGuard is a real-time M-Pesa reconciliation and anomaly detection platform for Kenyan SACCOs, e-commerce operators, and small fintechs, built on Safaricom's Daraja API. Treat it as a system of cooperating subsystems, each independently testable and deployable, not a monolith.

---

## 1. Ingestion Subsystem
- Daraja API webhook receiver (STK Push callbacks, C2B/B2C confirmations, transaction status)
- Signature/IP validation on every inbound webhook — never trust payload blindly
- Idempotency layer: unique transaction ID check + DB unique constraint before any processing
- Fast `200` response to Safaricom; defer slow work to background jobs
- Dead-letter log for malformed or rejected payloads

## 2. Reconciliation Engine
- Deterministic exact-match reconciliation (transaction ID / receipt number vs internal records)
- Configurable matching rules per customer (different SACCOs may structure records differently)
- Fuzzy/near-match suggestions for human review when exact match fails (timing lag, rounding, partial payments) — only after exact-match is solid
- Reconciliation status states: matched, unmatched, pending, disputed

## 3. Anomaly Detection Subsystem
- **Phase 1 (now):** rule-based checks — duplicate detection, amount thresholds, velocity checks (too many transactions too fast), off-hours activity
- **Phase 2 (later, with data volume):** statistical/ML layer on top of rules — customer-specific behavior baselines, drift detection
- Every anomaly gets a risk score and reason code, never a silent auto-block
- Human-in-the-loop confirmation before any account action

## 4. Notification Subsystem
- Channels: email, SMS (Africa's Talking), WhatsApp Business API
- Notify: reconciliation mismatches, anomalies, system health issues, daily/weekly summaries
- Per-customer notification preferences (channel, frequency, severity threshold)
- Delivery retry + failure logging (don't silently drop a notification)

## 5. Alerting & On-Call Subsystem
- Internal alerting for system health (not customer-facing): webhook failures, queue backlog, DB errors, elevated error rates
- Escalation policy: notify → escalate if unacknowledged → page on-call
- Integrates with existing `escalation_engine.py` / `on_call_service.py` if already present — extend, don't duplicate

## 6. Monitoring & Observability Subsystem
- Structured logging (JSON logs, correlation IDs per transaction/request)
- Metrics: webhook success/failure rate, reconciliation match rate, processing latency, queue depth
- Health check endpoint (`/health`) covering DB, queue, and external Daraja connectivity
- Dashboard (internal) showing system status at a glance — no SSH required to check health

## 7. Security Subsystem
- Webhook signature/IP allowlist validation
- Secrets management (env vars minimum, vault/secret manager as you scale) — never committed to git
- Role-based access control for internal users (`auth_rbac.py`)
- Rate limiting on public endpoints
- Audit trail: who/what changed reconciliation status, when

## 8. Data & Storage Subsystem
- Postgres as source of truth (transactions, reconciliation state, processed-transaction log)
- Automated daily backups with a tested restore procedure — not just "backup exists"
- Data retention policy (how long to keep raw payloads vs summarized records)
- Event store (`event_store.py`) as the audit-friendly log of everything that happened, if not already serving this role

## 9. Integrations Subsystem
- Daraja API (core)
- Africa's Talking (SMS) — already present (`africas_talking.py`)
- Email service — already present (`email_service.py`)
- Base connector pattern (`base_connector.py`, `connector_mapping`) for adding new customer data sources without rewriting core logic

## 10. Admin / Dashboard Subsystem
- Internal view: pending reconciliations, flagged anomalies, system health
- Customer-facing view (eventual): their own transaction reconciliation status, ability to flag a suspected mismatch themselves
- Keep read-only and action-taking permissions clearly separated (RBAC)

## 11. DevOps / Deployment Subsystem
- Containerized (Docker), reproducible builds
- CI: run tests + lint on every PR
- CD: auto-deploy to staging on merge to main; manual promote to production
- Environment parity: staging should mirror production configuration (minus real customer data)

## 12. Documentation & Onboarding
- README covering setup, architecture diagram, and how to run locally
- SECURITY.md (already drafted) — keep current as security posture evolves
- Runbook: what to do when [webhook fails / queue backs up / reconciliation mismatch spikes]

---

## Working Principles for the Agent

1. **Extend existing modules before creating new ones.** The codebase already has building blocks (`event_store.py`, `escalation_engine.py`, `on_call_service.py`, `anomaly_rules.py`, `reconciliation_engine.py`) — check what exists before adding parallel systems.
2. **Ship the smallest correct version of each subsystem first.** A working rule-based anomaly check beats an unfinished ML model. A working email alert beats an unfinished multi-channel notification system.
3. **Every subsystem must degrade safely.** If notifications fail, reconciliation still happens. If anomaly detection fails, transactions still get logged for later review. No single subsystem failure should silently lose financial data.
4. **Human confirmation stays in the loop** for anything touching money movement or account status — this is a guardrail, not a suggestion.
5. **Real customer data and feedback drive what gets built next** — not this document. Revisit priorities against what your live pilot customer is actually running into.
