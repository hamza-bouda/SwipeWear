#!/usr/bin/env bash
# Drop, recreate, and re-apply migrations for the local SwipeWear database.
# Usage (from any directory):  bash backend/scripts/db_reset.sh
set -euo pipefail

POSTGRES_USER="${POSTGRES_USER:-swipewear}"
POSTGRES_DB="${POSTGRES_DB:-swipewear}"
POSTGRES_HOST="${POSTGRES_HOST:-localhost}"
POSTGRES_PORT="${POSTGRES_PORT:-5432}"
export PGPASSWORD="${POSTGRES_PASSWORD:-swipewear_dev}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MIGRATIONS_DIR="$SCRIPT_DIR/../migrations"

echo "==> Dropping database '${POSTGRES_DB}' ..."
psql -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" postgres \
    -c "DROP DATABASE IF EXISTS \"${POSTGRES_DB}\";"

echo "==> Creating database '${POSTGRES_DB}' ..."
psql -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" postgres \
    -c "CREATE DATABASE \"${POSTGRES_DB}\";"

echo "==> Applying migrations from ${MIGRATIONS_DIR} ..."
for migration in "$MIGRATIONS_DIR"/*.sql; do
    echo "    -> $(basename "$migration")"
    psql -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" "$POSTGRES_DB" \
        -f "$migration"
done

echo "==> Done. Database '${POSTGRES_DB}' is ready."
