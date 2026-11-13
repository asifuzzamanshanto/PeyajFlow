#!/bin/sh
set -eu
python -m app.migrate
if [ -n "${SHOWCASE_ACCESS_KEY:-}" ]; then
    python -m app.seed_showcase
fi
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}" --no-access-log
