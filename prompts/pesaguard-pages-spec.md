# PesaGuard — Frontend Pages & Content Specification

Design direction: control-room aesthetic, deep navy/forest-green palette, Tailwind + shadcn/ui. 
Each page below lists its purpose and what it must contain.

---

## 1. Login / Authentication
- Email + password login, "forgot password" flow
- Optional: SSO or magic-link login for enterprise customers later
- Branding: PesaGuard logo, tagline ("Real-Time M-Pesa Reconciliation")
- Security messaging (small trust cues: "your data is encrypted", audit-friendly footer)

## 2. Dashboard (Home / Overview)
- Top-line stats: total transactions today, reconciliation match rate, open anomalies, system health status
- Real-time activity feed (last N transactions processed)
- Quick-glance chart: reconciliation match rate over time (7/30 day)
- Alert banner if system health is degraded
- Shortcut cards to "Review Anomalies" and "Unmatched Transactions"

## 3. Transactions
- Full searchable/filterable table: date, amount, transaction ID, status (matched/unmatched/pending/disputed), source
- Filter by date range, status, amount range, account
- Row click → transaction detail view (raw Daraja payload, matching internal record if any, timeline of what happened to it)
- Bulk actions: mark reviewed, export selected

## 4. Reconciliation
- Split view: unmatched internal records vs. unmatched Daraja transactions
- Suggested fuzzy matches (once that feature exists) with confidence score
- Manual match action (link two records together) with audit log entry
- Reconciliation summary by day/week/month

## 5. Anomalies / Alerts
- List of flagged anomalies with risk score, reason code (duplicate, threshold breach, velocity, off-hours, etc.)
- Filter by severity, status (new/acknowledged/resolved/false-positive)
- Detail view: transaction context, why it was flagged, similar past anomalies
- Action buttons: acknowledge, mark false positive, escalate

## 6. System Health / Monitoring
- Webhook success/failure rate (chart)
- Queue depth / processing latency
- Database and external Daraja connectivity status
- Recent errors/incidents log
- Uptime summary (last 24h/7d/30d)

## 7. Notifications & Alerting Settings
- Per-channel configuration: email, SMS, WhatsApp
- Severity thresholds (what triggers a notification vs. just a dashboard flag)
- Recipient management (who on the customer's team gets what)
- Notification history/log (sent, delivered, failed)

## 8. Reports
- Generate/download reconciliation reports (daily, weekly, monthly, custom range)
- Export formats: PDF, CSV
- Historical trend charts (match rate, anomaly volume, transaction volume over time)
- Scheduled report delivery setup (email a report every Monday, etc.)

## 9. Account / Integration Settings
- Daraja API credentials management (shortcode, keys — masked, with rotate/update action)
- Connected accounts/tills list
- Webhook callback URL display (for customer's own reference/troubleshooting)
- Team/user management (invite, roles, permissions — ties into RBAC)

## 10. Audit Log
- Full chronological log of actions: who matched what, who acknowledged which anomaly, config changes
- Filter by user, action type, date range
- Read-only, exportable — this is the compliance/trust anchor for SACCOs and auditors

---

## Cross-page requirements
- Consistent left sidebar navigation (control-room style: icon + label, collapsible)
- Global search (jump to a transaction ID from anywhere)
- Dark navy theme by default, with the PesaGuard shield/checkmark mark in the header
- Responsive down to tablet width at minimum; mobile view can be a simplified read-only dashboard
- Loading states and empty states designed intentionally (not blank screens) — especially important since a "no anomalies" empty state should feel reassuring, not broken

## Explicitly NOT a v1 requirement
- Full mobile app (separate future item)
- Multi-language support (add only if a customer needs it)
- White-label theming (only relevant once you have multiple distinct customer brands to support)
