# Start here

This is the continuation entry point for Project Ganymede. The public product explanation and normal installation instructions remain in [README.md](README.md).

## Scope and product shape

Work only inside this `Project-Ganymede-Dual-Mode` repository unless James explicitly expands the scope. Job Matrix and every sibling portfolio project are separate.

Project Ganymede is intentionally a dual-mode source release:

- The **full local edition** is the real Next.js and FastAPI application. It uses an already-authenticated Claude Code CLI and permits `WebSearch` only during research.
- The **deterministic showcase** uses the same interface with fixed fictional data. It exports static files and makes no backend or model calls.

Do not turn this into a showcase-only repository or restore the former root-level showroom as a second application.

## Read order

1. [README.md](README.md) — purpose, user flow, setup, and layout.
2. [AGENTS.md](AGENTS.md) — repository-specific continuation boundaries.
3. [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) — runtime flow and trust boundaries.
4. [docs/CONFIGURATION.md](docs/CONFIGURATION.md) — supported environment settings.
5. [docs/KNOWN_LIMITATIONS.md](docs/KNOWN_LIMITATIONS.md) — retained compatibility behavior and unfinished cleanup.
6. [SECURITY.md](SECURITY.md) — local execution and disclosure boundaries.
7. The backend, UI, and foundation-corpus READMEs before changing those areas.

The main executable entry points are `ganymede-backend/app/main.py`, `ganymede-backend/app/v2_routes.py`, `ganymede-backend/app/services/orchestrator.py`, `ganymede-backend/app/services/substrate.py`, and `ganymede-ui/src/config/edition.ts`.

## Current workspace state

- The public source branch is `main`. Check `git status` and `git log` for the current checkout and revision.
- The canonical UI is under `ganymede-ui/`, and the portable backend is under `ganymede-backend/`. The former root-level Next.js showroom has been replaced by the two editions of this shared application.
- Publishing source to GitHub does not deploy the showcase or start the local application.
- Ignored local state exists under `ganymede-backend/data/` and may contain prior scenarios. Do not inspect, copy, or commit it unless James explicitly asks. When transferring the project by archive instead of Git, exclude all ignored files.

Start every continuation with `git status --short --branch` and `git diff --check`. Preserve the existing changes unless the new task specifically supersedes them.

## Provider truth

This release has no NotebookLM runtime, account requirement, or browser automation. The `notebook_id`, `bridge_notebook_id`, and `create/query/delete_notebook` names that remain are legacy compatibility vocabulary. `ClaudeRuntimeService` maps them to opaque process-local records, then runs work through the authenticated Claude Code CLI. Research is one CLI call with only `WebSearch`; analytical, audit, bridge, and translation calls have all tools disabled.

Compatibility handles and uploaded bridge context are cleared when the backend stops. Sessions and completed strokes can persist in local SQLite. Do not install NotebookLM or restore old browser/source-panel workflows to satisfy legacy names.

## Reproduce and verify

Install from the repository root with `scripts/setup.ps1` on Windows or `scripts/setup.sh` on macOS/Linux. Then run:

```powershell
.\.venv\Scripts\python.exe -m compileall -q ganymede-backend\app
.\.venv\Scripts\python.exe -m unittest discover -s ganymede-backend\tests -v
Push-Location ganymede-ui
npm.cmd ci
npm.cmd run build
npm.cmd run build:showcase
Pop-Location
```

For a live smoke test, run `scripts/start.ps1` and verify `http://127.0.0.1:8000/api/health`, `http://127.0.0.1:8000/docs`, and `http://127.0.0.1:3000`. A real analysis requires an authenticated `claude` command and may perform web research.

## Last verified in this worktree

On September 6, 2026, all 44 regression tests and both frontend builds passed on the documented Node 22 minimum after manual code and security review. These checks use synthetic inputs and do not include an authenticated Claude end-to-end run.

On September 4, 2026:

- The external `node_modules` junction was removed, `npm ci` created dependencies inside this repository, and the sibling checkout remained untouched.
- Backend compilation and all four release-boundary tests passed.
- The full production frontend build and deterministic showcase build passed.
- A loopback-only backend smoke test returned `healthy`, detected the `claude_cli` provider, and exposed the expected OpenAPI document with 16 paths.
- No live analysis or WebSearch request was made during this handoff check.

Before declaring new work complete, verify the relevant tests, `git diff --check`, ignored/generated file boundaries, and documentation. Commit, push, merge, deploy, or publish only when James directly requests it.
