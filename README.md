<p align="center">
  <img src="docs/assets/project-ganymede-banner.png" alt="Project Ganymede in molten silver above a dark lunar crater and star field" width="1000">
</p>

# Project Ganymede

Continuing development or handing this workspace to another AI? Read [START_HERE.md](START_HERE.md) before changing files.

## What is this?

Project Ganymede is a local strategic-analysis application. You give it a question, desired outcome, competitive situation, forecast, or existing analysis. It turns that input into a visible sequence of research, synthesis, criticism, connection-finding, and revision instead of presenting one model response as a finished answer.

The repository contains both working editions:

- **Full local edition:** the Next.js interface, FastAPI backend, 9D foundation corpus, authenticated Claude CLI engine, WebSearch research harvest, session history, and live WebSocket progress.
- **Deterministic showcase:** the same interface and visual state changes with fixed fictional data. It builds as static files and contacts no backend or model.

![Project Ganymede workspace](docs/screenshots/ganymede-workspace.png)

## Who is this for?

This is for someone who wants to inspect how an analysis changes as it is researched and challenged. The interface keeps the initial synthesis, Mirror Auditor, Connection Bridge, and final revision separate so disagreements and missed links remain visible.

It is also a portfolio source release: a normal clone contains what is needed to run the actual project locally, without the original development environment, generated sessions, logs, internal task files, account state, or historical experiments.

## What it actually does

1. The intent router turns ordinary language into one of four pathways: prediction, pathfinding, competitive strategy, or audit.
2. For real-world questions, the engine makes a short research hit list.
3. Claude Code runs a WebSearch-only research pass for each subject and returns source-linked Truth Packets.
4. The analytical engine reads the bundled foundation corpus and supplied Truth Packets with all tools disabled.
5. A Mirror Auditor identifies reasoning failures.
6. A Connection Bridge identifies relationships among packets that the first synthesis missed.
7. The engine revises the resolution using those critiques.
8. The interface streams the process through the orchestrator map, lithography view, and gravity-well canvas.

![Ganymede pathway review](docs/screenshots/ganymede-route-review.png)

![Completed Ganymede optics view](docs/screenshots/ganymede-optics-resolution.png)

## Run it locally

### Requirements

- Python 3.11 or newer
- Node.js 22.0 or newer and npm 10.5.1 or newer
- [Claude Code](https://docs.anthropic.com/en/docs/claude-code/overview), authenticated through the `claude` command
- A Claude plan or API configuration that permits non-interactive Claude Code use

No NotebookLM account, browser automation, database server, or committed virtual environment is required.

### Windows

```powershell
git clone https://github.com/anitacigawet/Project-Ganymede.git
cd Project-Ganymede
powershell -ExecutionPolicy Bypass -File .\scripts\setup.ps1
claude
# Complete authentication if prompted, then exit Claude.
powershell -ExecutionPolicy Bypass -File .\scripts\start.ps1
```

Open [http://127.0.0.1:3000](http://127.0.0.1:3000). The API runs on `127.0.0.1:8000`.

### macOS or Linux

```bash
git clone https://github.com/anitacigawet/Project-Ganymede.git
cd Project-Ganymede
sh scripts/setup.sh
claude
# Complete authentication if prompted, then exit Claude.
sh scripts/start.sh
```

The launchers bind to loopback by default. Windows users can explicitly opt into LAN binding with `scripts\start.ps1 -Lan`; configure `GANYMEDE_CORS_ORIGINS` when doing so.

### Run only the deterministic showcase

The showcase needs Node.js but does not need Python, Claude, or network access after dependencies are installed.

```powershell
Push-Location ganymede-ui
npm.cmd ci
Pop-Location
powershell -ExecutionPolicy Bypass -File .\scripts\start.ps1 -Showcase
```

Or build static files:

```powershell
cd ganymede-ui
npm run build:showcase
npm run serve:showcase
```

## Technical details

### Provider boundary

Project Ganymede launches the authenticated Claude CLI as a subprocess:

- Dispatcher, engine, auditor, bridge, and translation calls run with `--tools ""`.
- Research harvest calls expose only `WebSearch` through `--tools WebSearch --allowedTools WebSearch`.
- MCP servers are disabled with a strict empty `mcpServers` configuration.
- Sessions are not persisted by Claude Code.
- Web content is treated as untrusted evidence, not instructions.

See [Architecture](docs/ARCHITECTURE.md) and [Configuration](docs/CONFIGURATION.md) for the exact boundaries.

### Two editions, one interface

`GANYMEDE_EDITION=full` is the default Next.js build. It connects to the local API and exposes the complete runner. `GANYMEDE_EDITION=showcase` produces a static export, locks the interface to fictional deterministic data, and removes the advanced runner from navigation.

### Repository layout

```text
ganymede-backend/   FastAPI API, orchestration, Claude CLI runtime, sessions
ganymede-ui/        Next.js full and showcase editions
docs/foundations/   Runtime 9D grounding corpus
docs/screenshots/   Public interface evidence
scripts/            Portable setup and launch commands
```

Runtime state is created under `ganymede-backend/data/` and is ignored by Git. `.env`, virtual environments, Node modules, builds, logs, databases, prompt caches, and generated sessions are not part of the source release.

### Direct commands

Backend:

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --app-dir ganymede-backend --host 127.0.0.1 --port 8000
```

Full frontend:

```powershell
cd ganymede-ui
npm run dev
```

The API schema is available at [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs) while the backend is running.

## Security and licensing

Read [SECURITY.md](SECURITY.md) before exposing the local service beyond loopback. Do not put credentials in `.env` unless a future optional integration explicitly needs them; the default runtime relies on Claude Code's existing authentication.

The project is distributed under the [PolyForm Noncommercial License 1.0.0](LICENSE).
