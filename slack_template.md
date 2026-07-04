# Slack Alert Template Reference

Used by `notifier.py::_format_alert_text`. Kept here as a reference/editable
copy so non-engineers on the team can tweak wording without touching code.

```
🚨 PesaGuard Discrepancy Detected
Transaction: {trans_id}
Issues: {anomaly_list}
Detected at: {timestamp}
```

## Planned variants (not yet implemented)

- **Daily summary digest** — total transactions reconciled, discrepancy count, resolution rate
- **Resolved notification** — when a flagged discrepancy is marked resolved
- **Escalation** — if a discrepancy stays unresolved > 1 hour, re-alert with @here
