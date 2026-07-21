PesaGuard Scheduled Reports

This document describes how to run `scheduled_reports.py` regularly to generate daily/weekly reports.

Quick run (one-off):

```bash
python3 pesaguard_backend_pipeline/scheduled_reports.py --tenant all --days 1 --type daily
```

Cron example (runs daily at 01:05 UTC):

```
5 1 * * * cd /home/pesaguard/Desktop/pesaguard && /usr/bin/env python3 pesaguard_backend_pipeline/scheduled_reports.py --tenant all --days 1 --type daily >> /var/log/pesaguard/scheduled_reports.log 2>&1
```

Systemd timer (preferred on modern Linux):

- Copy `infra/scheduled_reports.service` to `/etc/systemd/system/scheduled_reports.service`.
- Copy `infra/scheduled_reports.timer` to `/etc/systemd/system/scheduled_reports.timer`.
- Enable and start:

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now scheduled_reports.timer
```

Notes:
- Ensure the `DATABASE_URL` environment variable is set for the `pesaguard` user in the service environment, or modify the service unit to include `Environment=` entries.
- Logs are written to stdout; redirect or use `StandardOutput` in the unit file if you want to capture logs.
- For multi-tenant runs you can pass `--tenant <tenant_id>` to target a single tenant.
