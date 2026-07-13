# Pesaguard Pilot — Advanced Runbook

Purpose: operational runbook for pilot operators to triage issues, verify residency, and manage alerts during the pilot.

1. Onboarding verification
- Confirm pilot tenant created and `deployment_region` is set to the agreed region.
- Verify `preferred_locale` is set correctly for the tenant.
- Confirm admin API access: ensure pilot operator has `PESAGUARD_ADMIN_API_TOKEN` and can call `/admin/tenant/<id>`.

2. Pre-flight checks
- Send test alert through the AlertingService: ensure Slack webhook (if configured) receives message.
- If Email alerts enabled, confirm SMTP connectivity and that pilot recipient receives a test email.
- Verify Kenya formatting by checking sample dashboards and exported report.

3. Incident triage
- If alerting fails: check `SLACK_WEBHOOK_URL`, `SMS_ALERT_RECIPIENT`, and SMTP env vars.
- Check delivery logs in the database (Discrepancy entries with `alert-` prefix).
- Escalate to engineering if delivery errors show network or provider errors.

4. Residency verification
- Confirm storage and backups are running in `deployment_region` by reviewing deployment variables and cloud provider console.
- For cross-border data transfer requests, consult the legal reviewer before enabling `cross_border_transfer_allowed`.

5. Admin token rotation (pilot)
- Rotate `PESAGUARD_ADMIN_API_TOKEN` periodically and notify pilot operators.
- To rotate: set new token in pilot env, update operator local config, and invalidate previous tokens.

6. Post-incident
- Capture timeline and root cause in pilot issue tracker.
- Notify pilot customer of impact and remediation steps.
- Add any required changes to the Premium readiness backlog.

7. Contacts
- Pilot support Slack: #pesaguard-pilot
- Pilot support email: pilot-support@pesaguard.example
- Engineering on-call: see internal rota

