# Project Ganymede

A strategic-physics observatory: feed in a real-world scenario, get back a 9-dimensional analysis grounded in authenticated sources, and watch the resulting strategic landscape render as a warping 3D topology.

The project is composed of two halves:

- **`ganymede-backend/`** — FastAPI service that orchestrates a hard-coded **9D Chess Engine** (a protected NotebookLM acting as the strategic logic core) and a swarm of ephemeral **PKI Authentication Oracles** (NotebookLMs spun up per subject, persona-locked into a zero-hallucination, hash-citing research role).
- **`ganymede-ui/`** — Next.js + React Three Fiber frontend that consumes the **Ganymede Strategic Schema (GSS)** and renders the live topology.

## Where to start

| You want to… | Open |
| --- | --- |
| Understand what this project is in 5 minutes | [`docs/OVERVIEW.md`](docs/OVERVIEW.md) |
| Look up a term (Umpire, Oracle, GSS, ROEM, SDS, etc.) | [`docs/GLOSSARY.md`](docs/GLOSSARY.md) |
| Read the conceptual foundation | [`docs/concepts/`](docs/concepts/) |
| See the operational protocols | [`docs/protocols/`](docs/protocols/) |
| Read run-records of past experiments | [`docs/experiments/`](docs/experiments/) |
| See potential productization paths | [`docs/visions/`](docs/visions/) |
| Trace how the system evolved | [`docs/history/Architecture_History.md`](docs/history/Architecture_History.md) |

## Running it locally

### Backend

```powershell
cd ganymede-backend
.\venv_312\Scripts\activate          # Python 3.12 venv with the live deps
$env:PYTHONPATH = "."
uvicorn app.main:app --reload --port 8000
```

The backend expects:
- `GOOGLE_API_KEY` in env (for `GeminiService`)
- A valid NotebookLM session at `~/.notebooklm/storage_state.json` (run `notebooklm login` if expired)

### Frontend

```powershell
cd ganymede-ui
npm install
npm run dev          # http://localhost:3000 (or 3001 if 3000 is taken)
```

> **Note for Claude / agents working on the UI:** this version of Next.js (16) has breaking changes from training data. Always check `node_modules/next/dist/docs/` before writing Next-specific code. See `ganymede-ui/AGENTS.md`.

## Related repositories

- **[anitacigawet/9D-Chess](https://github.com/anitacigawet/9D-Chess)** — the upstream theoretical project. Contains the formalization of the 9D framework, ROEM, and BNOPDM, plus a separate Vite/Python simulation platform. Treated as reference, not merged. Project Ganymede draws on its concepts but does not depend on its code.

## Status

Operational baseline reached on the Hualapai water-crisis run. See [`docs/OVERVIEW.md`](docs/OVERVIEW.md) for the current state-of-build (what's wired, what's still designed-not-built) and [`docs/experiments/`](docs/experiments/) for completed and pending runs.
