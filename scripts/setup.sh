#!/usr/bin/env sh
set -eu
project_root=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
python3 -m venv "$project_root/.venv"
"$project_root/.venv/bin/python" -m pip install --disable-pip-version-check --upgrade pip
"$project_root/.venv/bin/python" -m pip install --disable-pip-version-check -r "$project_root/ganymede-backend/requirements.txt"
(cd "$project_root/ganymede-ui" && npm ci)
printf '%s\n' 'Project Ganymede dependencies are installed.'
