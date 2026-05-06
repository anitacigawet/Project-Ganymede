# Project Ganymede — Overview

## What this is

Project Ganymede is a working laboratory for running real scenarios through a 9-dimensional strategic-physics framework, end-to-end:

```
   user scenario
        │
        ▼
┌──────────────────┐    queries    ┌────────────────────────┐
│   Orchestrator   │──────────────▶│  9D Chess Engine        │
│   (FastAPI svc)  │               │  (hard-coded NotebookLM,│
│                  │◀──────────────│   read-only Umpire)     │
└──────────────────┘   triage      └────────────────────────┘
        │
        │ spawns per-subject
        ▼
┌──────────────────────────────────────┐
│  PKI Oracle Swarm                     │
│  (ephemeral NotebookLMs, persona-     │
│   locked: zero hallucination,         │
│   hash-cited Truth Packets)           │
└──────────────────────────────────────┘
        │
        │ Truth Packets re-injected
        ▼
┌──────────────────┐               ┌────────────────────────┐
│  9D Chess Engine │──synthesis───▶│  GSS payload (JSON)     │
│  (holistic re-   │               │  drives the 3D engine   │
│   analysis)      │               └─────────┬──────────────┘
└──────────────────┘                         │
                                              ▼
                              ┌──────────────────────────────┐
                              │ ganymede-ui (Next.js + R3F)  │
                              │   • GravityWell (D_n physics)│
                              │   • Cortex Clipboard         │
                              │   • Live overrides           │
                              └──────────────────────────────┘
```

## State of build

### Wired and working
- **`/api/orchestrate`** — single FastAPI endpoint. Takes `{query, notebook_id}`, queries the supplied notebook, returns a structured prompt block ready for the Gemini compiler.
- **`NotebookLMService`** — `create_notebook`, `query_notebook`, `configure_pki_oracle` (the Phase-0 persona lock), `query_chess_engine` (read-only against the hard-coded Engine ID).
- **`GeminiService`** — `identify_entities` and `generate_strategic_model` (two-stage perceive→encode). Currently only invoked from `test_compiler.py`, not from `main.py`.
- **`GravityWell.tsx`** — the actual 9D physics: D_n inverted-radial-decay deformation, fracture state when depth < threshold, entangled agricultural nodes, holographic legislative plane, dynamic node spawning from the GSS schema.
- **`PhysicsCanvas.tsx`** — the 3D stage: scanning HUD, live override sliders for `drawRate` and `mitigation`, status readout, "TOPOLOGICAL FAILURE" alert.
- **`DevOverlay.tsx` (Cortex Clipboard)** — copy-out prompt block + paste-in GSS JSON + "Apply To Topology" button. The current bridge between the human-driven Gemini-Pro phase and the live frontend.
- **GSS schema** — fully typed in `ganymede-ui/src/types/ganymede.ts`. Contract is stable.

### Designed but not yet wired
- **`AnalystStream.tsx`** — exists as a static dummy chat component but isn't imported anywhere in `page.tsx`. The whole left-panel "Analyst" experience from the original blueprint is effectively missing from the live app — `GalleryPanel` is shown there instead.
- **Gallery exhibits** — 10 hard-coded titles in `GalleryPanel.tsx`, no payloads, not connected to anything backend-side.
- **Scenario archive** — every GSS payload is currently transient. There is no persistence layer yet.
- **Universal Logic Loop, end-to-end (productized).** The four-phase loop is now exposed as discrete FastAPI endpoints: `POST /api/triage`, `POST /api/oracle`, `POST /api/oracle/{id}/go`, `POST /api/oracle/{id}/harvest` (or `/api/swarm/harvest`), `POST /api/synthesize`, `POST /api/resolution-check`. Implementation in `ganymede-backend/app/services/orchestrator.py`. The 36 ad-hoc scripts that previously lived in `ganymede-backend/scratch/` are archived as historical receipts at [`experiments/scripts/`](experiments/scripts/). Protocol spec: [`protocols/Universal_Logic_Loop_Protocol.md`](protocols/Universal_Logic_Loop_Protocol.md).

## Hard guardrails

These are non-negotiable rules baked into the project. Every contributor — human or agent — must respect them.

1. **The 9D Chess Engine is read-only.** Notebook ID `5967ce5d-f9eb-4f4e-b3e1-620f643d8390`. Hard-coded as `CHESS_ENGINE_ID` in `notebooklm_service.py`. Never create, rename, configure, or delete it. Only `query_chess_engine` is allowed against it.
2. **Manual approval before spawning notebooks.** PKI Oracles are created on demand, but never autonomously. The human approves each new oracle. This is to protect the Google account from ban risk and to keep the swarm curated.
3. **No browser-driven Gemini-Pro automation.** A previous experiment burned Pro queries by mis-firing keyboard events. The Cortex Clipboard exists specifically to keep the Gemini-Pro step a deliberate human paste action.
4. **Surgical, plain-language prompts to Oracles.** The Umpire's internal jargon (DAI, ROEM, Horus Trap, etc.) does not survive contact with a research bot. Translate first.
5. **Holistic synthesis at the Umpire.** When the Truth Packets come back, do not pre-frame them with "find SDS only." Hand the engine the authenticated facts and the original scenario, and let it run.

## Where to go next

See [`history/Architecture_History.md`](history/Architecture_History.md) for the project timeline and [`experiments/`](experiments/) for the run records (Hualapai, GPS triage, Powell validation, 60s amnesia mirror swarm, Compute Autarky pending).
