## Frequently Asked Questions (Pilot)

### Does PesaGuard reconcile all payment methods?

No. **Current scope is M-Pesa/Daraja only.** Airtel Money, bank transfers, and other payment rails are not reconciled or alerted on during the pilot. If you need multi-rail support, that requires a separate scoping conversation — we will not expand scope silently.

### Where is my data stored?

PesaGuard supports a documented residency posture for primary data, backups, and logs. We will confirm the selected deployment region for your tenant during onboarding and enforce residency controls as configured. See [DATA_RESIDENCY.md](../../DATA_RESIDENCY.md).

### Can I change the language?

Yes. Each tenant can set a default language at the tenant level; individual users may override the preference where supported. During the pilot we support English and Kiswahili translations for core workflows and alerts. SMS alerts respect your language preference.

### What alerts are sent?

Alerts are delivered to the channels configured for your tenant (Slack, SMS, and optionally Email). Content is localized according to the tenant's preferred locale.

### Does PesaGuard support Kenya-specific formatting?

Yes. Dashboards and exported reports use Kenya-appropriate date/time (EAT) and currency (KES) formatting regardless of language choice.

### How do I get support during the pilot?

We provide a shared Slack channel for pilot participants and a named support contact. See the pilot runbook for escalation steps and SLAs.

### Who signs off residency and legal terms?

Our legal reviewer will review the residency decision document and produce a signed readiness statement before we publish the pilot status page.
