# Operations Readiness Notes

## Backup automation
- Run the backup script daily from cron or a scheduler:
  - `0 2 * * * /home/kipruto/Desktop/pesaguard/scripts/backup_postgres.sh`
- Store copies off-host using object storage or a backup service.

## Restore drill
- Schedule a quarterly restore drill in a scratch environment and verify dashboard/API access after restore.

## Retention enforcement
- The cleanup job is available at [pesaguard_backend_pipeline/retention_cleanup.py](../pesaguard_backend_pipeline/retention_cleanup.py) and can be run via [scripts/run_retention_cleanup.sh](../scripts/run_retention_cleanup.sh).
- Configure the cron entry to run daily:
  - `0 3 * * * /home/kipruto/Desktop/pesaguard/scripts/run_retention_cleanup.sh`
