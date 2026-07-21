# PesaGuard — Scaling & Expansion Plan

Every item below should be triggered by a real signal — a customer asking, or a system genuinely hitting a limit — not built speculatively ahead of demand.

## Technical Scaling (triggered by actual load)

1. **Vertical scaling first** — bigger DB instance, more app workers, before adding new infrastructure pieces
2. **Background job queue** (Celery/RQ) — once webhook volume means synchronous processing causes delays
3. **Read replicas** for Postgres — once reporting/dashboard queries start competing with write load from live reconciliation
4. **Caching layer** (Redis) — for frequently-checked data (e.g. duplicate transaction lookups) once that check becomes a bottleneck
5. **Kafka/PyFlink** — only once single-instance processing genuinely can't keep up with transaction throughput (already scoped in the separate streaming repo — resist pulling in early)
6. **Multi-region/multi-AZ** — only once specific customers require contractual uptime guarantees that need it

## Market Expansion (customer-driven)

1. **Same segment, more customers** — more SACCOs/small fintechs like the current pilot; the product is already shaped for them
2. **Adjacent segments** — e-commerce operators, savings groups (chamas), micro-lenders — once it's clear what's reusable vs. what needs rework
3. **Adjacent rails** — beyond Daraja/M-Pesa, potentially Airtel Money or bank APIs — only if customers specifically need multi-rail reconciliation
4. **Geographic expansion** — Uganda, Tanzania — a later move, only if the Kenyan market is saturated or a specific customer needs it

## Business Model Scaling

- Pricing tiers (by transaction volume, number of connected accounts, or feature tier)
- Self-serve signup vs. the current manual/high-touch pilot approach
- Partnerships (accounting software integrations, SACCO umbrella bodies, Safaricom developer ecosystem)

## Trigger Signals to Watch For

| Move | Signal that it's time |
|---|---|
| Background job queue | Webhook response times creeping up / Safaricom retries increasing |
| Read replicas | Dashboard/report queries visibly slowing down reconciliation writes |
| Redis caching | Duplicate-check queries showing up as a hotspot in monitoring |
| Kafka/PyFlink | Consistent queue backlog even after vertical scaling + job queue |
| Multi-tenant support | 2nd or 3rd paying customer confirmed |
| Self-serve onboarding | Manual onboarding becoming a bottleneck to closing new customers |
| Multi-rail support | A specific customer asks for non-M-Pesa reconciliation |
| Geographic expansion | Kenyan pipeline slows down, or inbound interest from another market |

---

**Guiding principle:** this plan describes *possible* futures, not a queue of committed work. Revisit against real customer signals before starting any item.
