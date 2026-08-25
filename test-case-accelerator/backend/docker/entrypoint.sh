#!/bin/sh
set -eu

if [ "${RUN_DATABASE_MIGRATIONS:-false}" = "true" ]; then
    echo "Applying database migrations before API startup"
    alembic upgrade head
fi

exec "$@"
