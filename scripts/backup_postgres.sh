#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

: "${POSTGRES_HOST:=localhost}"
: "${POSTGRES_PORT:=5432}"
: "${POSTGRES_USER:=pesaguard}"
: "${POSTGRES_DB:=pesaguard}"
: "${POSTGRES_PASSWORD:=pesaguard}"
: "${BACKUP_DIR:=/tmp/pesaguard-backups}"
: "${S3_BUCKET:=}"
: "${BACKUP_REGION:=${DEPLOYMENT_REGION:-ke-1}}"

# Backups must stay in BACKUP_REGION per DATA_RESIDENCY.md (RES-4).
# When using S3, ensure the bucket resides in the same jurisdiction as primary data.

mkdir -p "$BACKUP_DIR"
TS="$(date +%F-%H%M%S)"
BACKUP_PATH="$BACKUP_DIR/pesaguard-$TS.dump"

export PGPASSWORD="$POSTGRES_PASSWORD"
pg_dump -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" -F c -b -v -f "$BACKUP_PATH" "$POSTGRES_DB"

if [[ -n "$S3_BUCKET" ]]; then
  aws s3 cp "$BACKUP_PATH" "s3://$S3_BUCKET/$(basename "$BACKUP_PATH")"
fi

echo "$BACKUP_PATH"
