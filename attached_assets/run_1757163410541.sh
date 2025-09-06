#!/usr/bin/env bash
set -euo pipefail
export $(grep -v '^#' .env | xargs -d '\n' -r) || true
exec uvicorn app.main:app --reload --host "${HOST:-0.0.0.0}" --port "${PORT:-8000}"
