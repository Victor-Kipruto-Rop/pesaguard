# PesaGuard — Full Frontend Build Prompt

Hand this to your coding agent (Claude Code) as a complete brief. Build incrementally — 
one page/section at a time — rather than all at once.

---

## Design Direction

Build a premium, modern, sleek control-room interface for a real-time financial 
monitoring product. This is not a generic SaaS dashboard template — it should feel 
like mission control for money movement: calm, precise, and trustworthy, with an 
underlying sense of "everything is being watched."

**Palette:**
- Base background: deep navy-forest `#0B2E24` to `#0A1F2E` gradient range
- Surface/card: `#0F241D`
- Primary accent (success/reconciled): `#2ECC87`
- Secondary accent (brand): `#124A3B`
- Warning: `#F1A83C`
- Critical/alert: `#E11D48`
- Text primary: `#F4FBF8`, text muted: `#8FA69C`

**Type:** a technical/monospace-adjacent face for data and numbers (clarity at a glance, 
reinforces the "control room" feel), paired with a clean geometric sans for headings and 
body copy. Avoid generic template fonts.

**Signature element:** a live-feeling pulse/heartbeat line motif that appears subtly across 
the product — in the dashboard header, in loading states, in the health page — representing 
the real-time nature of the system without being decorative filler.

**Stack:** Next.js 14 App Router, Tailwind CSS, shadcn/ui components. Responsive down to 
tablet at minimum.

Build to a quality floor: keyboard focus visible, reduced motion respected, real empty/error 
states (not blank screens), loading states designed intentionally.

---

## PAGE INVENTORY

### A. Public / Marketing Pages
1. **Landing page** — hero (the product's single job stated plainly), problem/solution framing for SACCOs and fintechs, how-it-works in 3 steps, trust signals, CTA to request a pilot/demo
2. **Pricing page** — tiers (once defined), what's included per tier, FAQ
3. **About / Company page** — mission, why this exists, founder note
4. **Blog / Updates** — launch posts, product updates (reuses your existing Medium/Dev.to content)
5. **Contact / Request a demo** — form, or calendar booking link
6. **Security & Trust page** — plain-language explanation of data handling, encryption, audit logging (SACCOs will ask about this before trusting real transaction data)
7. **Legal pages** — Terms of Service, Privacy Policy

### B. Authentication Pages
8. **Login**
9. **Sign up / Request access** (likely invite-only at pilot stage, not open self-serve yet)
10. **Forgot password / Reset password**
11. **Two-factor verification** (if/when implemented)

### C. Core Application Pages (customer-facing)
12. **Dashboard (Overview)** — top-line stats, real-time activity feed, match-rate trend, system health banner
13. **Transactions** — searchable/filterable table, detail view per transaction
14. **Reconciliation** — unmatched pairs, suggested matches, manual match action
15. **Anomalies / Alerts** — flagged list, detail view, acknowledge/resolve actions
16. **System Health** (customer-visible subset) — uptime, last sync time, connectivity status
17. **Notifications settings** — channel config, thresholds, recipients
18. **Reports** — generate/download, scheduled reports, historical trends
19. **Account & Integration Settings** — Daraja credentials (masked), connected accounts, team management
20. **Audit Log** — chronological action history, filterable, exportable

### D. Admin Pages (internal, PesaGuard team only — not customer-visible)
21. **Admin dashboard** — all customers at a glance, system-wide health, pilot status
22. **Customer management** — list of customers, onboarding status, plan/tier, account health
23. **Internal system monitoring** — infrastructure-level metrics (queue depth, DB load, error rates across all tenants)
24. **Feature flags / configuration** — toggle features per customer during rollout
25. **Internal audit log** — actions taken by PesaGuard staff (support access, config changes) — separate from customer-facing audit log
26. **Support/ticket view** — if you build support tooling, a simple internal queue of customer issues

### E. Pilot / Onboarding-Specific Pages
27. **Pilot onboarding wizard** — step-by-step: connect Daraja credentials, configure reconciliation rules, set notification preferences, confirm first sync
28. **Pilot status page** (internal) — tracks where each pilot customer is in the onboarding funnel, flags stuck steps
29. **Sandbox/test mode banner + page** — clearly marked test environment for a pilot customer to try before going live with real transactions
30. **Feedback capture page** — simple in-app form for pilot customers to report issues or request features directly (feeds your own backlog, not a generic support ticket)

### F. Documentation Pages
31. **Docs home** — overview, navigation to all doc sections
32. **Getting started guide** — connecting Daraja, first reconciliation walkthrough
33. **API reference** (once a public API exists) — endpoints, auth, example requests/responses
34. **Webhook reference** — payload structure, retry behavior, signature verification (for customers integrating their own systems)
35. **FAQ** — common questions (what happens on a mismatch, how anomalies are scored, data retention)
36. **Changelog** — what's shipped, version history
37. **Glossary** — plain-language definitions of terms used in the product (reconciliation, anomaly score, idempotency, etc. — written for a SACCO finance person, not a developer)

### G. Error / System States (not routes, but required everywhere)
38. **404 page**
39. **500 / system error page**
40. **Maintenance mode page**
41. **Empty states** for every list/table view (no transactions yet, no anomalies — reassuring tone, not alarming)
42. **Offline/connectivity lost state** (relevant since this is a real-time product)

---

## Build Priority (do not build all 40+ at once)

**Now (pilot has 1 live customer):**
Dashboard, Transactions, Reconciliation, Anomalies, Notifications settings, basic Login/Auth, 
Security & Trust page (builds pilot trust), Getting Started doc

**Next (stabilizing, 2–4 customers):**
Reports, Account/Integration Settings, Audit Log, Pilot onboarding wizard, FAQ, empty/error states polish

**Later (scaling):**
Admin pages, Customer management, full public marketing site, API reference/webhook docs, 
Changelog, Glossary, feature flags

---

## Content & Copy Guidance (apply to every page)
- Write from the user's side of the screen: name things by what they control, not how the system works internally ("Notification settings," not "Webhook config")
- Errors state what went wrong and how to fix it — never vague, never apologetic in tone
- Empty states are an invitation to act, not a dead end ("No anomalies today — your reconciliation is clean" reads very differently from a blank table)
- Keep vocabulary consistent across the whole product: if a button says "Match," the resulting confirmation should also say "Matched," never "Reconciled" in one place and "Linked" in another

---

## Explicit Guardrail for the Agent
Build one page or page-group at a time, working from the "Now" priority list first. 
Do not scaffold all 40+ pages in a single pass — confirm each section is functional 
and reviewed before moving to the next.
