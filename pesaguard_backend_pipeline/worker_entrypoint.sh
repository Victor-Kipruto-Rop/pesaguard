#!/bin/sh
set -eu

export PYTHONPATH="${PYTHONPATH:-}:/app/pesaguard_backend_pipeline"
exec rq worker --path /app/pesaguard_backend_pipeline --url "${REDIS_URL:-redis://redis:6379/0}" "${RQ_QUEUE_NAME:-transaction_events}"
