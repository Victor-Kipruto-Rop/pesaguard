# Operations Readiness Notes

## Backup automation
- Run the backup script daily from cron or a scheduler:
  - `0 2 * * * /home/kipruto/Desktop/pesaguard/pesaguard_backend_pipeline/scripts/backup_postgres.sh`
- Store copies off-host using object storage or a backup service.

## Restore drill
- Schedule a quarterly restore drill in a scratch environment and verify dashboard/API access after restore.

## Retention enforcement
- The cleanup job is available at [pesaguard_backend_pipeline/retention_cleanup.py](../pesaguard_backend_pipeline/retention_cleanup.py) and can be run via [pesaguard_backend_pipeline/scripts/run_retention_cleanup.sh](../pesaguard_backend_pipeline/scripts/run_retention_cleanup.sh).
- Configure the cron entry to run daily:
  - `0 3 * * * /home/kipruto/Desktop/pesaguard/pesaguard_backend_pipeline/scripts/run_retention_cleanup.sh`

## Deployment readiness gate
`health.build_deployment_readiness()` aggregates the operational controls above into a
single verdict that is exposed on `GET /status` (as `deployment_readiness`) and can be
used as a deploy gate. The incident-response view is exposed separately as
`incident_readiness`.

| Control | `ready` | `configured` | `degraded` |
| --- | --- | --- | --- |
| `backup` | tooling present **and** a backup artifact newer than `PESAGUARD_BACKUP_MAX_AGE_HOURS` (default 26h) exists in `PESAGUARD_BACKUP_DIR` | backup script or systemd unit present, but no fresh artifact yet (new deploy or stale backups) | no backup script and no systemd unit found |
| `incident_response` | runbook (`docs/INCIDENT_RESPONSE.md` or `docs/RUNBOOK.md`) present **and** at least one alert channel configured | only one of {runbook, alert channel} present | neither present |

Overall `status` is `ready` when no control is `degraded`; otherwise it is `degraded` and
the offending control names are listed in `gaps`.

Alert channels are detected from `SLACK_WEBHOOK_URL`, `SMS_ALERT_RECIPIENT`, and
`ALERT_EMAIL_RECIPIENTS` — the same variables `notifier.py` pages through.

### Checking readiness manually
```bash
PYTHONPATH=. python -c "import json; from pesaguard_backend_pipeline import health; print(json.dumps(health.build_deployment_readiness(), indent=2))"
```
