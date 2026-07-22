#!/usr/bin/env bash
#
# Runs the Phoenix observability server as ONE persistent process, separate
# from the FastAPI app. Keep this running in its own terminal; it survives
# uvicorn --reload restarts, so traces are never lost and the DB is never
# corrupted by repeated in-process launches.
#
# Uses an isolated, project-local data dir (repo_root/.phoenix) so it does NOT
# touch the stale global ~/.phoenix DB that caused the null-field GraphQL
# errors (Project.name / Span.spanId).
#
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

export PHOENIX_WORKING_DIR="$REPO_ROOT/.phoenix"

echo "Starting Phoenix"
echo "  data dir : $PHOENIX_WORKING_DIR"
echo "  UI       : http://localhost:6006  (project: code-review)"

exec "$SCRIPT_DIR/venv/bin/python" -m phoenix.server.main serve
