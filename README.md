# Project Ganymede

A **simulation sandbox** for running real scenarios through the 9D strategic-physics framework. Named for Jupiter's largest moon — a self-contained body with its own gravitational field. The project mirrors that shape: the **9D Chess Engine** sits at the gravitational center, ephemeral **PKI Authentication Oracle** notebooks orbit as knowledge silos in the sandbox, and an optional **GSS visualization layer** renders the resulting strategic landscape in 3D.

The Engine is fed authenticated, hash-cited Truth Packets — either harvested by Oracles inside the sandbox or supplied pre-harvested by an external consumer — and resolves scenarios via the Convergence Theorem. The sandbox is closed-loop: nothing inside it talks to the outside world except through explicit, gated entry points.

The project is composed of two halves:

- **`ganymede-backend/`** — FastAPI service exposing the four-phase Universal Logic Loop as discrete primitives. Orchestrates the 9D Chess Engine and the PKI Oracle swarm.
- **`ganymede-ui/`** — Next.js + React Three Fiber frontend hosting the GSS visualization and the Cortex Clipboard. Multi-page experimental playground; each page can host a different experiment.

**Long-term goal:** plug the orchestration + 9D-physics module into the user's other projects as a private analysis library. *Not* a public SaaS; *not* a museum-as-product.

## Where to start

| You want to… | Open |
| --- | --- |
| Understand what this project is in 5 minutes | [`docs/OVERVIEW.md`](docs/OVERVIEW.md) |
| See the strongest single piece of evidence the framework is real | [`docs/experiments/runs/Powell_Cleanroom/`](docs/experiments/runs/Powell_Cleanroom/) |
| Read the four active research pathways | [`docs/experiments/pathways/`](docs/experiments/pathways/) |
| See past run records | [`docs/experiments/runs/`](docs/experiments/runs/) |
| Look up a term (Umpire, Oracle, GSS, Genie Prime, Iterative Engine, etc.) | [`docs/GLOSSARY.md`](docs/GLOSSARY.md) |
| Browse preserved-but-not-committed-to ideas | [`docs/brainstorming/`](docs/brainstorming/) |
| Read the conceptual foundation | [`docs/concepts/`](docs/concepts/) |
| See the operational protocols | [`docs/protocols/`](docs/protocols/) |
| See potential productization paths (not the current direction) | [`docs/visions/`](docs/visions/) |
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

Two confirmed blind validations of the prediction methodology (Powell, Tokenized Land), one partial (Musk-Altman Stroke 1+2; Stroke 3 pending), one demonstration of the Genie pathfinding pathway (Giant-Slayer), and one instructive failure (60-second Amnesia) that motivated the Mirror Validation pathway. The GSS visualization pipeline is functional end-to-end on the Hualapai canonical sample.

The project is past operational baseline and into methodology-tightening. Next planned work: pre-registered live prediction with timestamped outputs, Mirror Validation full standup (contrast notebook), and Iterative Engine three-stroke completion on a real scenario. See [`docs/OVERVIEW.md`](docs/OVERVIEW.md) for the current state-of-build and [`docs/experiments/`](docs/experiments/) for the run library.
