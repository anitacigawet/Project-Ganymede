#!/usr/bin/env sh
set -eu
project_root=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
mode=${1:-full}

if [ "$mode" = "showcase" ]; then
  cd "$project_root/ganymede-ui"
  exec npm run dev:showcase -- --hostname 127.0.0.1
fi

cd "$project_root/ganymede-backend"
"$project_root/.venv/bin/python" -m app.cli_preflight
"$project_root/.venv/bin/python" -m uvicorn app.main:app --host 127.0.0.1 --port 8000 &
backend_pid=$!
trap 'kill "$backend_pid" 2>/dev/null || true' EXIT INT TERM
cd "$project_root/ganymede-ui"
npm run dev -- --hostname 127.0.0.1
