#!/bin/sh
set -e

# Ensure DB schema is up to date before starting API server.
uv run alembic upgrade head

exec uv run uvicorn app.main:app --host 0.0.0.0 --port 8000
