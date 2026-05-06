# Project Ganymede — Overview

## What this is

Project Ganymede is a working laboratory for running real scenarios through a 9-dimensional strategic-physics framework, end-to-end. The 9D Chess Engine (a single hard-coded NotebookLM) is treated as a closed strategic-physics engine; ephemeral PKI Authentication Oracle notebooks act as research extenders that feed the Engine authenticated, hash-cited Truth Packets; the Engine then resolves scenarios via the Convergence Theorem.

```
   user scenario (Dream-State framed)
            │
            ▼
   ┌──────────────────────┐
   │ 9D Chess Engine      │── Architectural Blueprint
   │ (Lead Architect)     │   (research requirements)
   └──────────────────────┘
            │
            ▼
   ┌──────────────────────┐
   │ Orchestrator (Hand)  │── plain-language jargon strip
   │ "Surgical Middleman" │   (no editorial summary)
   └──────────────────────┘
            │
            ▼
   ┌──────────────────────┐
   │ PKI Oracle Swarm     │── deep-research, persona-locked
   │ (one notebook each   │   (or one Master Silo on Pro)
   │  OR Master Silo)     │
   └──────────────────────┘
            │
            ▼ Truth Packets (raw, unmodified, hash-cited)
   ┌──────────────────────┐
   │ 9D Chess Engine      │── Convergence Theorem synthesis
   │ (resolution)         │   ("Strategic Lasso" + "Incomprehensible Move")
   └──────────────────────┘
            │
            ▼ Resolution
            │
            ▼
   ┌──────────────────────┐
   │ Independent Audit    │── Gemini Deep Research
   │ (Blind Validation)   │   "Is this real? Are people doing it?"
   └──────────────────────┘

   ┌──────────────────────────────────────────┐
   │ Optional: Iterative Engine multi-stroke   │
   │   Stroke 1 (raw resolution) → user/Mirror │
   │   notebook injects friction → Stroke 2    │
   │   (engine red-teams itself) → Stroke 3    │
   │   (synthesis: the unbreakable move)       │
   └──────────────────────────────────────────┘

   ┌──────────────────────────────────────────┐
   │ Optional: GSS visualization layer         │
   │  Gemini Pro turns the resolution into a   │
   │  GSS JSON payload via the Cortex Clipboard│
   │  → ganymede-ui renders it in 3D           │
   │  (this layer is independent of prediction;│
   │  it's the Museum mode of the project)     │
   └──────────────────────────────────────────┘
```

## North star: module, not service

The project's long-term goal is **to plug into the user's other projects as a private logistics / strategic-physics analysis module** — not to ship as a public-facing SaaS, not to be a museum. The user's framing: *"Build this as a foundation to get something that works to where I can then plug this into my other projects and turn it as a private logistics physics model."*

This shapes the API design priorities:
- The Python import surface of `app/services/orchestrator.py` matters as much as the HTTP surface in `app/main.py`. Both should be clean, both will eventually be consumed.
- No multi-tenant concerns. No public-user UX concerns. No marketing surface.
- The Museum / SaaS / Showcase paths are preserved in [`visions/`](visions/) as future possibilities, not commitments.

## Active research pathways

These are the four hypothesis lines the project is actively iterating on. Full pathway docs in [`experiments/pathways/`](experiments/pathways/):

| Pathway | What it tests | Status |
| --- | --- | --- |
| [Prediction Cleanroom](experiments/pathways/prediction_cleanroom.md) | Can the Engine, in Dream-State + closed-loop with no Gemini contamination, predict non-obvious strategic outcomes that reality later confirms? | ✅ Two confirmed blind validations (Powell, Musk-Altman partial). |
| [Mirror Validation](experiments/pathways/mirror_validation.md) | Can a second 9D-protocol instance (or the Engine red-teaming itself) catch the Engine's "correct math, infeasible reality" rigidity errors? | 🟡 Diagnosed (Amnesia run) and methodology proposed; first live demo in Musk-Altman Stroke 2. |
| [Offensive Architect](experiments/pathways/offensive_architect.md) | Stance shift — Engine *designs* the funnel against a target instead of auditing one. | ✅ Concept demonstrated (Conglomerate scenarios). |
| [Genie Protocol](experiments/pathways/genie_protocol.md) | Wish-fulfillment pathfinding — given (current state, wished-for state), Engine designs the *Inadvertent Path*. | ✅ One full demonstration (Zero-Budget Giant-Slayer). |

The meta-methodology underlying all four is the **Iterative Engine Vision** ([`concepts/Iterative_Engine_Vision.md`](concepts/Iterative_Engine_Vision.md)): the Engine is a piston, not a one-shot oracle. Single-pass output is idealistic; multi-stroke firing with human or contrast-notebook friction injection between strokes is what produces strategy that survives reality.

## State of build

### Wired and working

- **Backend service layer** — `ganymede-backend/app/services/orchestrator.py` exposes the four-phase Universal Logic Loop as explicit primitives (`triage`, `create_oracle`, `send_go`, `harvest`, `harvest_swarm`, `synthesize`, `resolution_check`). Runaway-prevention guardrail enforced in code: each `create_oracle` call creates exactly one notebook.
- **Backend HTTP API** — `ganymede-backend/app/main.py` wraps the orchestrator as 9 endpoints: `/api/health`, `/api/triage`, `/api/oracle`, `/api/oracle/{id}/go`, `/api/oracle/{id}/harvest`, `/api/swarm/harvest`, `/api/synthesize`, `/api/resolution-check`, plus the legacy `/api/orchestrate` for the existing frontend Cortex Clipboard.
- **`NotebookLMService`** — `create_notebook`, `query_notebook`, `configure_pki_oracle`, `query_chess_engine` (read-only against the hard-coded Engine ID).
- **`GeminiService`** — `identify_entities` and `generate_strategic_model`. Currently only invoked from `test_compiler.py`, not from `main.py`. Kept for future GSS-compilation work.
- **GSS visualization layer** — `GravityWell.tsx` (D_n inverted-radial-decay deformation, fracture state, entangled nodes, holographic legislative plane), `PhysicsCanvas.tsx` (3D stage, scanning HUD, live override sliders, "TOPOLOGICAL FAILURE" alert), `DevOverlay.tsx` (Cortex Clipboard — paste-in GSS JSON, "Apply To Topology"). GSS schema fully typed in `ganymede-ui/src/types/ganymede.ts`.

### Designed but not yet wired

- **`AnalystStream.tsx`** — exists as a static dummy chat component but isn't imported in `page.tsx`. The original "Analyst" left-panel experience is effectively missing from the live app. Per the user's clarification — different pages of the website will host different experiments; this component will land on whatever page needs a chat-style scenario interface.
- **Gallery exhibits** — 10 hard-coded titles in `GalleryPanel.tsx`, no payloads. Currently this is the placeholder content on the Hualapai-style topology page.
- **Scenario archive / persistence** — every GSS payload and every run is currently transient. No persistence layer yet.
- **Mirror Validation, end-to-end** — the contrast-notebook setup (a second 9D notebook used as fault-finder against the first) has been specified but not stood up.
- **Pre-registered prediction methodology** — the Cleanroom pathway has demonstrated the technique but not yet locked in pre-registration discipline (timestamped predictions before validation runs). The next pre-registered run is the methodological priority.

## Hard guardrails

These are non-negotiable rules baked into the project. Every contributor — human or agent — must respect them.

1. **The 9D Chess Engine is read-only.** Notebook ID `5967ce5d-f9eb-4f4e-b3e1-620f643d8390`. Hard-coded as `CHESS_ENGINE_ID` in `notebooklm_service.py`. Never create, rename, configure, or delete it. Only `query_chess_engine` is allowed against it.
2. **Manual approval before spawning notebooks.** PKI Oracles are created on demand, but never autonomously. The human approves each new oracle. This protects the Google account from ban risk and keeps the swarm curated. Enforced in code via the per-call shape of `create_oracle`.
3. **No browser-driven Gemini-Pro automation.** A previous experiment burned Pro queries by mis-firing keyboard events. The Cortex Clipboard exists specifically to keep the Gemini-Pro step a deliberate human paste action. *(Caveat: Gemini Pro is also explicitly excluded from the Prediction Cleanroom loop entirely — its only legitimate role is the post-hoc independent-research auditor.)*
4. **Surgical plain-language prompts to Oracles.** The Engine's internal jargon (DAI, ROEM, Horus Trap, etc.) does not survive contact with a research bot. The orchestrator translates jargon → plain English losslessly before any Oracle is invoked. Editorial summarization is forbidden — the orchestrator is a transparent pipe between Engine and Oracle, not an editor.
5. **Zero-degradation synthesis.** When Truth Packets come back from the Oracles, paste the *exact unmodified text* into the synthesis prompt. No summarization. No reordering. No cleanup. The Engine's resolution quality depends on the source-citation chain remaining intact.
6. **Holistic synthesis at the Engine.** Don't pre-frame Truth Packets with "find SDS only" or any goal-shaped instruction. Hand the Engine the authenticated facts and the original scenario, and let it run.

## Where to go next

| You want to… | Open |
| --- | --- |
| See past runs (Powell Cleanroom, Tokenized Land, Genie Giant-Slayer, Musk-Altman, Hualapai, Amnesia) | [`experiments/runs/`](experiments/runs/) |
| Read the active pathway hypotheses | [`experiments/pathways/`](experiments/pathways/) |
| Look at preserved-but-not-committed-to ideas | [`brainstorming/`](brainstorming/) |
| Read the conceptual foundation | [`concepts/`](concepts/) |
| Read operational protocols | [`protocols/`](protocols/) |
| See the product / service paths we *might* build later | [`visions/`](visions/) |
| Trace the project's evolution | [`history/Architecture_History.md`](history/Architecture_History.md) |
| Look up a term | [`GLOSSARY.md`](GLOSSARY.md) |

The next concrete experiment, per the [Prediction Cleanroom open methodology section](experiments/pathways/prediction_cleanroom.md#open-methodology-problems): a **pre-registered live prediction** in a domain that resolves within 4–8 weeks. The standing candidate is [Compute Autarky](experiments/runs/05_Pending_Compute_Autarky.md).
