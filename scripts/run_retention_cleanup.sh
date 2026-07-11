#!/usr/bin/env bash

# PesaGuard retention cleanup cron wrapper.
# Run this daily from cron or systemd timer.

cd "$(dirname "${BASH_SOURCE[0]}")/.." || exit 1
source .venv/bin/activate
python -m pesaguard_backend_pipeline.retention_cleanup
