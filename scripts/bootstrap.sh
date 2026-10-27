#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
command -v uv >/dev/null || { printf '%s\n' 'Missing uv; install the trusted developer tool first.' >&2; exit 1; }
uv sync --locked
uv run python scripts/check_plan.py
uv run fonesi-prototype scan
