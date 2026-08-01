#!/bin/sh
set -eu

: "${POSTGRES_USER:=pesaguard}"
: "${POSTGRES_MULTIPLE_DATABASES:=pesaguard_reports,pesaguard_audit,pesaguard_worker_state}"
: "${POSTGRES_REPLICATION_USER:=pesaguard_repl}"
: "${POSTGRES_REPLICATION_PASSWORD:=pesaguard_repl}"

replication_rule="host replication ${POSTGRES_REPLICATION_USER} 0.0.0.0/0 scram-sha-256"
if ! grep -qF "$replication_rule" "$PGDATA/pg_hba.conf"; then
    printf '%s\n' "$replication_rule" >> "$PGDATA/pg_hba.conf"
fi

for db_name in $(printf '%s' "$POSTGRES_MULTIPLE_DATABASES" | tr ',' ' '); do
    if [ -z "$db_name" ]; then
        continue
    fi

    exists=$(psql -U "$POSTGRES_USER" -d postgres -Atqc "SELECT 1 FROM pg_database WHERE datname='${db_name}'" || true)
    if [ "$exists" != "1" ]; then
        createdb -U "$POSTGRES_USER" -O "$POSTGRES_USER" "$db_name"
    fi
done

role_exists=$(psql -U "$POSTGRES_USER" -d postgres -Atqc "SELECT 1 FROM pg_roles WHERE rolname='${POSTGRES_REPLICATION_USER}'" || true)
if [ "$role_exists" != "1" ]; then
    psql -U "$POSTGRES_USER" -d postgres -v ON_ERROR_STOP=1 <<-EOSQL
        CREATE ROLE ${POSTGRES_REPLICATION_USER} WITH REPLICATION LOGIN PASSWORD '${POSTGRES_REPLICATION_PASSWORD}';
EOSQL
fi