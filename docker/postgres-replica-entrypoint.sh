#!/bin/sh
set -eu

: "${POSTGRES_PRIMARY_HOST:=postgres}"
: "${POSTGRES_REPLICATION_USER:=pesaguard_repl}"
: "${POSTGRES_REPLICATION_PASSWORD:=pesaguard_repl}"

if [ ! -s "$PGDATA/PG_VERSION" ]; then
    until pg_isready -h "$POSTGRES_PRIMARY_HOST" -p 5432 -U "${POSTGRES_USER:-postgres}" >/dev/null 2>&1; do
        sleep 1
    done

    export PGPASSWORD="$POSTGRES_REPLICATION_PASSWORD"
    pg_basebackup \
        -h "$POSTGRES_PRIMARY_HOST" \
        -p 5432 \
        -D "$PGDATA" \
        -U "$POSTGRES_REPLICATION_USER" \
        -Fp \
        -Xs \
        -P \
        -R
fi

chown -R postgres:postgres "$PGDATA"
chmod 700 "$PGDATA"
exec gosu postgres postgres -D "$PGDATA" -c hot_standby=on