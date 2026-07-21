# PesaGuard — Roadmap & Future Features

Organized by what unlocks real value at each stage, not everything at once. 
Each phase should be triggered by actual customer need or a real limitation hit — not built ahead of demand.

## Phase 0 — Now (1 pilot customer)
- [ ] Webhook idempotency (in progress)
- [ ] Automated backups + tested restore procedure
- [ ] Basic monitoring / health check endpoint
- [ ] Rule-based anomaly detection tuned to this customer's actual transaction patterns

## Phase 1 — Once pilot is stable (2–4 more customers)
- [ ] Multi-tenant support — clean data separation, per-customer reconciliation rule config
- [ ] Self-serve onboarding — customer connects their own Daraja credentials
- [ ] Customer-facing dashboard — view own reconciliation status, flag disputes
- [ ] SMS/WhatsApp notification preferences per customer

## Phase 2 — Once real transaction volume + history exists (months of data)
- [ ] Statistical/ML anomaly scoring layered on top of existing rules (not a replacement)
- [ ] Fuzzy reconciliation matching for edge cases (partial payments, timing lag)
- [ ] Historical trend reporting (weekly/monthly reconciliation health per customer)
- [ ] Risk scoring dashboard for triaging flagged items by severity

## Phase 3 — Once volume genuinely demands it (not before)
- [ ] Kafka/PyFlink streaming pipeline (already scoped in the separate streaming repo — bring in only when Postgres + background workers can't keep up)
- [ ] Kubernetes orchestration
- [ ] Horizontal scaling of the webhook receiver

## Longer-term product ideas
- [ ] API access for customers to pull reconciliation data into their own systems
- [ ] Integration with accounting software (QuickBooks, Zoho) for SACCOs
- [ ] Compliance/audit export for regulators or auditors
- [ ] Mobile app for on-the-go anomaly review

## Ongoing, not phase-gated
- [ ] Security hardening (webhook validation, secrets, RBAC) — never deprioritize
- [ ] Documentation kept current as the system evolves

---

**Guiding principle:** revisit this roadmap against what the live pilot customer is actually running into, not against this document. Planning ahead of validated demand is the pattern to actively avoid.
