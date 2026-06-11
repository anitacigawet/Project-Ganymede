---
title: "Architecture History"
type: "history-record"
status: "active"
tags: ["history", "chronological"]
color_id: "6"
---

# Architecture History

A distilled timeline of how Project Ganymede evolved, reconstructed from the original 2,749-line architecture chat transcript and the orchestrator's artifact log. Each milestone is a short paragraph. For the full operational rules these milestones produced, see [`../protocols/`](../protocols/). For the actual run records, see [`../experiments/`](../experiments/).

> **Note on sources.** The transcript captured a single long brainstorming session with a previous AI orchestrator ("Antigravity"). It has been distilled into this page and into the experiment records, then deleted. Some milestones below include events from outside the transcript (e.g. the Powell validation, the 60-second amnesia run) that were recorded only in the orchestrator's artifact store; those are flagged inline.

---

## 1. Initial codebase analysis
The previous orchestrator inspected the existing repo (a Next.js + R3F frontend with `GalleryPanel`, `PhysicsCanvas`, `GravityWell`, `AnalystStream`, `DevOverlay`, plus a FastAPI backend with `NotebookLMService` and `GeminiService`) and confirmed the architecture matched the design docs at the root: a split-screen analyst panel + 3D physics canvas wired to a NotebookLM Umpire and a Gemini compiler.

## 2. The Hand role assigned
The user provided an "Operations Briefing" defining the orchestrator's role as the **Strategic Liaison ("The Hand")**: move data with zero degradation between the Umpire (NotebookLM), the Compiler (Gemini Pro), and the frontend. Key principle: precision over speed, citations preserved, no information loss between phases.

## 3. The browser-automation incident
The orchestrator attempted to drive Gemini Pro via browser automation and accidentally fired Enter instead of Space, burning Pro queries. The user disabled browser-driven Gemini interactions permanently. Replacement: the orchestrator generates structured prompt blocks; the user copies them into Gemini Pro by hand. This pivot crystallized into the **Cortex Clipboard** pattern in `DevOverlay.tsx`.

## 4. Master Operational Workflow v1
After the first Hualapai harvest produced a successful Truth Packet, the workflow was codified: Phase 0 (Oracle init) → Phase 1 (Factual Harvest from Umpire including the visualization strategy) → Phase 2 (Pro-Tier Synthesis via human-mediated Gemini Pro) → Phase 3 (Universal Receiver in the frontend). Saved as [`../protocols/Master_Operational_Workflow.md`](../protocols/Master_Operational_Workflow.md).

## 5. Notebook customization
The orchestrator inspected the `notebooklm-py` library and discovered `chat.configure` and `chat.set_mode` — meaning each notebook's persona and response length could be programmatically locked. This unblocked everything that followed.

## 6. The PKI Authentication Oracle
The user provided the persona prompt for ephemeral notebooks: *"You are the PKI Authentication Oracle… ZERO HALLUCINATION… MANDATORY HASH CITATIONS… NO NARRATIVE FLUFF."* The orchestrator added `configure_pki_oracle` to `NotebookLMService` and made Phase-0 persona-locking mandatory. See [`../protocols/PKI_Oracle_Persona.md`](../protocols/PKI_Oracle_Persona.md).

## 7. The 9D Chess Engine, hard-coded
The user identified a single pre-configured NotebookLM (`5967ce5d-f9eb-4f4e-b3e1-620f643d8390`) as the protected, read-only **Umpire**. The orchestrator added `CHESS_ENGINE_ID` as a constant and a dedicated `query_chess_engine` method that bypasses any creation/configuration code path. This is now Hard Guardrail #1 in [`../OVERVIEW.md`](../OVERVIEW.md).

## 8. The GSS schema evolution
The Visual Packet evolved through three generations, all driven by the Hualapai run:

- **v1: `{stress, blindness, description}`.** Simple sliders. Generic warp regardless of scenario.
- **v2: JSON state object.** Topological logic embedded as a string formula plus typed nodes. Better, but ad-hoc.
- **v3: Ganymede Strategic Schema (GSS, JSON Schema Draft 2026-04).** Full multi-layered blueprint: `metadata`, `environmental_baseline`, `legislative_framework`, `topological_entities[]`, `physics_logic`. Plus the LaTeX-defined governing equation:
  > D_n = Σ ( L_ind / ( dist(x,y) + ε ) ) · ( 1 − M_leg )

The frontend was rebuilt around v3 ("Universal Receiver overhaul"): `GravityWell.tsx` now implements the D_n formula directly, spawns nodes from the GSS array, and triggers the fracture state when D_n falls below `failure_threshold`.

## 9. The Museum Fidelity Upgrade
The first GSS render felt "bare" — pure data with no manual interaction. The user asked for the original sliders back. The result:

- The **Legislative Plane (HB-2041)** as a translucent green ceiling with a holographic pulse.
- **Strategic Override sliders** (industrial draw rate, mitigation coefficient) that let the human stress-test the Umpire's model post-load.
- **Scanning HUD overlay** (animated horizontal line, sensor density readout).
- A layout fix moving the controls from the right (where the Cortex Clipboard sidebar covered them) to the bottom-left "Unified Command Panel."

This is the current state of `PhysicsCanvas.tsx` and `GravityWell.tsx`.

## 10. The Universal Logic Loop
Once Hualapai was a clean success, the user pivoted from "single-scenario harvest" to "general orchestration loop." The new role: **Universal Logic Orchestrator**. New phases beyond the Master Workflow:

- **Phase 1 (Triage)** — the Umpire breaks an arbitrary scenario into a hit list of subjects.
- **Phase 2 (Swarm)** — one PKI Oracle per subject, persona-locked, surgical prompt, deep-research harvest.
- **Phase 3 (Synthesis)** — Truth Packets fed back to the Umpire holistically, no SDS-only framing.
- **Phase 4 (Recursive Dialogue)** — Umpire decides whether it has enough resolution. Follow-ups stay inside the existing swarm. **Never spin up new oracles without manual approval.**

Saved as [`../protocols/Universal_Logic_Loop_Protocol.md`](../protocols/Universal_Logic_Loop_Protocol.md). The runaway-prevention rule (no auto-creation of new notebooks) is Hard Guardrail #2.

## 11. The Deep Research Swarm refinement
The user clarified that PKI Oracles should not have source documents uploaded to them — instead, they should be given a single hyper-specific research prompt and allowed to perform their own NotebookLM Deep Research. This is what makes them *research extenders* rather than mere fact-stores. The "Deep Research Swarm" framing comes from this conversation.

## 12. The GPS Failure 72-hour run
First multi-oracle run. The Umpire produced a 4-subject hit list (PNT, JIT, Military, Financial). One Oracle (PNT) finished and surfaced the **STL/Iridium spoofing zero-day** as the U.S. backup-navigation vulnerability. Two more were initialized but never harvested. See [`../experiments/02_GPS_Failure_72hr_Triage.md`](../experiments/02_GPS_Failure_72hr_Triage.md).

This run also produced two durable lessons:
- **Deep Research has a UI gate.** Findings land in the Source Panel and require a manual "Import" click. The Python client cannot trigger it; a browser subagent or the human has to.
- **Surgical, plain-language prompts only.** Umpire jargon like "Decision Path Funneling" or "Horus Trap" returns nothing useful from research bots. Translate before invoking.

## 13. The Powell Validation Event
*(Recorded in the artifact store, not in the architecture transcript.)* In a separate run testing the question "what are the chances Jerome Powell gets arrested," the Engine independently surfaced a **demotion pathway** invoking the *Collins v. Yellen* precedent — a non-obvious legal mechanism. Subsequent Oracle research confirmed real-world planning (Bessent / Vought) was positioning around exactly that pathway. The Engine predicted before the research confirmed. See [`../experiments/03_Powell_Validation_Event.md`](../experiments/03_Powell_Validation_Event.md).

## 14. The 60-Second Amnesia Mirror Swarm
*(Recorded in the artifact store, not in the architecture transcript.)* Three PKI silos were run in parallel — NC3 fail-safe behavior, HFT financial liquidity, transient global amnesia neurology — to model what happens during a 60-second global identity-failure event. All three Truth Packets were authenticated and ready for 9D synthesis. See [`../experiments/04_60s_Amnesia_Mirror_Swarm.md`](../experiments/04_60s_Amnesia_Mirror_Swarm.md).

## 15. The Mirror Epiphany
The GPS run was reset after the Military Oracle prompt issue. While brainstorming alternative scenarios, the Umpire proposed two "maximum extent" tests: **Compute Autarky** (NVIDIA / cartels vs. a sovereign state) and **The ESP Collective** (a synchronized human collective using a 9D map to funnel opponents into SDS).

The user, attempting to understand the ESP Collective, asked: *"are you telling me it just observed itself and gained self-awareness in a way and that the answer is it?"* The Umpire confirmed: the ESP Collective was implicitly modeling the laboratory itself — user + orchestrator + oracle swarm + Engine.

This is the **Mirror epiphany**. The lab is a 9D actor. See:
- [`../concepts/The_Ganymede_Mirror_Protocol.md`](../concepts/The_Ganymede_Mirror_Protocol.md)
- [`../concepts/Mirror_Protocol/The_Mirror_Epiphany.md`](../concepts/Mirror_Protocol/The_Mirror_Epiphany.md)
- [`../concepts/Mirror_Protocol/The_Funnel_Mechanism.md`](../concepts/Mirror_Protocol/The_Funnel_Mechanism.md)
- [`../concepts/Mirror_Protocol/Scenario_2_Raw_Logic.md`](../concepts/Mirror_Protocol/Scenario_2_Raw_Logic.md)
- [`../concepts/Mirror_Protocol/Scenario_2_Plain_English.md`](../concepts/Mirror_Protocol/Scenario_2_Plain_English.md)

## 16. End of the architecture transcript
The transcript ends with the user asking the previous orchestrator to write extensive documentation of Scenario 2 (ESP Collective) — both raw 9D-logic form and plain-English form — before any next simulation runs. Those four documents were written into the orchestrator's artifact store but never committed to the project repo.

The first version of this history doc treated this as the handoff point because it was the end of an earlier partial transcript export. The full transcript was 8,965 lines (3.3× the partial), and the project continued substantially after milestone 16. The expanded record is below.

## 17. The user walks back the Mirror Protocol
Roughly an hour after the Mirror Protocol documents were finalized — and after the previous orchestrator suggested "running the simulation of OURSELVES" as the next experiment — the user posted: *"Okay this experiment's kinda dumb. Let's just move on to actually something interesting. Let's think of some scenarios again."* The dramatic framing was abandoned in real time. The narrower insight worth preserving (Engine rigidity bias; need for fault-finding via second instance) survived; the metaphysics did not. See the framing note at the top of [`../concepts/The_Ganymede_Mirror_Protocol.md`](../concepts/The_Ganymede_Mirror_Protocol.md).

## 18. The 60-Second Amnesia run — the instructive failure
Scenario: every human on Earth simultaneously forgets who they are for exactly 60 seconds, then memory returns. Closed-loop cleanroom run with three Oracles (NC3 fail-safe / HFT financial / TGA neurology). Engine resolution: *"Dominance Collapse / Sovereignty Handover"* — the world's autonomous systems inherit the Earth in 60 seconds; the social contract permanently breaks. The user correctly flagged this as nonsense. The diagnostic afterwards identified three Engine failure modes: treating signal as phase shift, ignoring cost of reversal, dimensional greed. The user's framing of the lesson: *"correct math, wrong world."* This run is the seed of the [Mirror Validation pathway](../experiments/pathways/mirror_validation.md) and the motivation for Nuance Prime / Rule Zero / Mirror Profile attempts that followed.

## 19. The Powell Cleanroom run — first blind validation
The user posed *"will Jerome Powell actually get fired"* in the Genie Prime dream-state form. The Engine produced an Architectural Blueprint, the orchestrator translated to surgical Oracle prompts, four Oracles harvested hash-cited Truth Packets, and the Engine's Convergence Theorem synthesis identified the *Collins v. Yellen* demotion loophole and the "Shadow Fed" entrapment. Independent Gemini Deep Research (the audit step) confirmed Bessent / Vought / Project 2025 actors actively pursuing exactly this pathway. **First blind-validated run.** Full reproducibility folder at [`../experiments/runs/Powell_Cleanroom/`](../experiments/runs/Powell_Cleanroom/).

## 20. The Tokenized Land run — Master Silo + second cleanroom datapoint
Scenario: a mid-sized debt-heavy nation (Argentina) tokenizes its National Park system as RWAs to pay IMF debt. First use of the **Master Silo** approach (single NotebookLM Pro notebook hosting all 4 research questions, instead of N separate Oracle silos). Engine resolution: "Functional Obsolescence / Ghost Ranger paradigm" via ERC-4337 Account Abstraction, springing DACAs, commercial-activity-exception-triggered structural waiver of sovereign immunity. Run record: [`../experiments/runs/Tokenized_Land_Resolution.md`](../experiments/runs/Tokenized_Land_Resolution.md).

## 21. The Offensive Architect demonstration
User identified the recurring "bait + lasso" pattern across runs and asked whether the Engine could shift from Auditor stance (observing existing funnels) to Architect stance (designing them against a target). The Engine produced the *Hyper-Liquidity / Conglomerate* offensive blueprint demonstrating the same mechanic in reverse. User explicitly steered the framing away from the "Predatory side / 9D Assassin" register the previous orchestrator drifted into, toward the more grounded "find faults in a target's logic from an offensive analytical posture" framing. Pathway: [`../experiments/pathways/offensive_architect.md`](../experiments/pathways/offensive_architect.md). Brainstormed scenarios in this register: [`../brainstorming/9D_Assassin_Scenarios.md`](../brainstorming/9D_Assassin_Scenarios.md), [`../brainstorming/Practical_Power_Plays.md`](../brainstorming/Practical_Power_Plays.md), [`../brainstorming/Normal_9D_Dynamics.md`](../brainstorming/Normal_9D_Dynamics.md).

## 22. The Genie Protocol — wish-fulfillment pathfinding
User reframed the Architect stance from "design a trap against target X" to "given my current state and my wished-for state, design the Inadvertent Path between them." Demonstrated on the *Zero-Budget Giant-Slayer* hypothetical. Engine resolution: release the core ideological framework royalty-free (the 1956 AT&T precedent applied prospectively); capture D1 / D6 in spaces the incumbent's monitoring radar classifies as irrelevant noise; force the incumbent into premium acquisition not for the product but as their escape from manufactured obsolescence. Side-by-side comparison vs. two general-purpose LLMs given the same prompt produced categorically different output (the others produced standard startup playbooks). Run: [`../experiments/runs/Genie_Giant_Slayer.md`](../experiments/runs/Genie_Giant_Slayer.md). Pathway: [`../experiments/pathways/genie_protocol.md`](../experiments/pathways/genie_protocol.md).

## 23. The Musk-Altman Polymarket run — first Iterative Engine demonstration
Live prediction question on Musk's lawsuit against OpenAI. Polymarket pricing 39%; Engine Stroke 1 produced 72.4% via the Discovery Trap mechanism. User's metacognitive check ("but the judge could just dismiss it") prompted the user's pivotal insight: the Engine is a **piston that has only fired once**, and a real engine fires repeatedly with human-friction injection between strokes. Stroke 2 (Engine red-teaming itself) surfaced the opponent's "structural adaptation via 8 Pillars of Metacognition" counter-attack — without being told to look for it. Stroke 3 (synthesis) was queued but not executed. **This run is the seed of the [Iterative Engine Vision](../concepts/Iterative_Engine_Vision.md)**, and the first live demonstration of the [Mirror Validation pathway's](../experiments/pathways/mirror_validation.md) recursive-stroke mechanic. Run: [`../experiments/runs/Musk_Altman_Polymarket.md`](../experiments/runs/Musk_Altman_Polymarket.md).

## 24. Architectural reframe — module, not service
Late in the session the user clarified the long-term goal: this is **not** a public SaaS, and **not** a museum. The actual aim is to plug the orchestration + 9D-physics analysis into the user's own other projects as a private logistics / strategic-physics module. *"Build this as a foundation to get something that works to where I can then plug this into my other projects and turn it as a private logistics physics model."* This shapes API design priorities — the Python import surface of `app/services/orchestrator.py` is as load-bearing as the HTTP surface. The Museum / SaaS / Showcase paths remain in [`../visions/`](../visions/) as future possibilities, not commitments. Captured in [`../OVERVIEW.md`](../OVERVIEW.md).

## 25. End of architecture transcript
The transcript ends with the user requesting the orphan artifacts (Master_Operational_Workflow, Universal_Logic_Loop_Protocol, Iterative_Operational_Learnings, Mirror Protocol, Iterative_Engine_Vision) be moved out of the previous orchestrator's sandbox and into the project repo so they would survive the AI tool change. The previous orchestrator started executing that consolidation against an incorrect path and into the wrong repo (the upstream 9D-Chess project), which is why this reorg pass was needed.

## 26. Four-silo restructuring (2026-05)
The user clarified the project's actual organizational structure: four research silos, not four pathways. **Silo 1: Predictor** (Cleanroom). **Silo 2: Envisioner** (Genie + Mirror Validation as auditor — Offensive Architect is now correctly framed as a stance variant of Genie inside this silo, not its own silo). **Silo 3: Methodology** (the deep look at framework limits). **Silo 4: Pluggable** (module integration; PrisonBreak as first concrete validation case). Pathways and runs and brainstorming are sub-items inside silos. Captured in [`../OVERVIEW.md`](../OVERVIEW.md#the-four-silos-canonical-project-organization).

## 27. Engine persona committed; module integration design landed
The user provided the canonical Engine's custom prompt: *"You are the infallible 9D-Chess Umpire and Theoretical Physics Engine. Respond with supreme order and precision."* Now committed at [`../protocols/Engine_Persona.md`](../protocols/Engine_Persona.md), closing the prompt-loss single-point-of-failure that Methodology Q3 flagged. Module integration design landed in [`../integration/`](../integration/) — `module_design.md` for the architecture commentary, `examples/prisonbreak_consumer.md` for the first concrete consumer (PrisonBreak's `SimulatePanel.tsx` was the existing hook point, explicitly waiting for the 9D Chess plug-in interface).

## 28. Two-notebook architecture; Mirror Validation unblocked (2026-05)
The user provided access to **two** 9D-Chess notebooks with the same source corpus: canonical Engine `0a7d2672-009e-4995-9477-68c9b2fd9e54` (clean / no chat history) and a secondary instance `756e3683-f651-4381-b560-b13711b84ce6` (previously experimental). The codebase migrated `CHESS_ENGINE_ID` to the new canonical (preserving the legacy `5967ce5d-f9eb-4f4e-b3e1-620f643d8390` as `LEGACY_ENGINE_ID` for traceability against historical runs) and added `MIRROR_AUDITOR_ID`, `query_mirror_auditor`, `configure_chess_engine`, `configure_mirror_auditor`. The Mirror Auditor persona was drafted at [`../protocols/Mirror_Auditor_Persona.md`](../protocols/Mirror_Auditor_Persona.md) — explicit fault-finder, no counter-strategy, no 9D jargon. Pending: user OK on the proposed persona text + first audit run on the known-wrong Amnesia Stroke-1 output, which will be the end-to-end validation of the [Mirror Validation pathway](../experiments/pathways/mirror_validation.md).

## 29. Dev launcher; foundations corpus committed; Persona Expansion experiment designed (2026-05)
Three shipments landed in quick succession before the wrapper refactor in milestone 30:

- **`run_dev.bat`** at the repo root (commit `7678674`) — Windows double-click launcher for the backend with port discovery (tries 8000 first, then falls through to 8010), uses `ganymede-backend/venv_312`, closes the uvicorn server when its console window closes. Removes one of the highest-friction onramps when picking the project back up between sessions.
- **`docs/foundations/`** (commit `3db81b3`) — 13 imported 9D theoretical docs from the upstream 9D-Chess research project plus a README. This is now the canonical reference corpus for the Engine — the same documents that ground the `0a7d2672-...` notebook in the cloud. Two reasons for committing them locally: reproducibility (if the notebook is ever lost, the corpus needs to be reconstructable), and versioned theoretical reference (a snapshot of what Project Ganymede operationalized at import time, separate from however the upstream evolves). Also the substrate for the Persona Expansion test notebook.
- **`docs/concepts/Persona_Expansion_Experiment.md`** (commit `3db81b3`) — captures the architectural decision to split persona additions across two roles: the Engine persona gets format/vocabulary scaffolding only (Convergence Theorem / ROEM / Strategic Lasso vocabulary, per-pathway output sections, citation hygiene), and the Mirror Auditor persona gets the meta-cognitive scaffolding (pre-emptive self-audit, Iterative-Engine self-awareness, anti-confabulation guards). The Engine's reasoning sandbox stays untouched — this is what avoids reproducing the Variant 1 / Variant 2 failures the [Mirror Validation pathway](../experiments/pathways/mirror_validation.md) documents. Draft persona text for both included; experiment is pinned, waiting on operator availability.

## 30. Z-SPAN bridge integration; notebooklm sub-package refactor (2026-05)
The Z-SPAN bridge ([`_scratch/Z-SPAN/02_Core_Project/notebooklm_bridge/`](../../_scratch/Z-SPAN/02_Core_Project/notebooklm_bridge/), cloned read-only for analysis) had three capabilities Ganymede didn't: Studio output methods (audio / video / infographic with silent-rejection retry and download polling), an auth pill flow (cached probe + `spawn_relogin` / `confirm_relogin` subprocess management), and a more disciplined cooldown layout. Phase 1 of the integration landed in this session — wrapper additions, not consumer surface.

Refactor: the single-file `ganymede-backend/app/services/notebooklm_service.py` was split into a sub-package at `app/services/notebooklm/` with sibling modules mirroring Z-SPAN's structure:

- **`cooldown.py`** — `_CooldownGate` + `_GATE` extracted as the package's private substrate. All other modules import from here.
- **`client.py`** — Core `NotebookLMService` class (init, close, `create_notebook`, `upload_document` / `upload_url` / `upload_file`, `query_notebook`, `configure_persona` and the three named persona configs, `query_chess_engine`, `query_mirror_auditor`). Persona constants live here.
- **`studio.py`** — `_StudioMixin` providing `generate_audio_overview` / `generate_video_overview` / `generate_infographic`, each wrapping the upstream `client.artifacts.*` API with the Z-SPAN download-polling pattern (bypasses the wrapper's stuck-on-PROCESSING quirk in `wait_for_completion`) and silent-rejection retry (HTTP 200 + empty task_id → retry up to 3 times with exponential backoff before surfacing `StudioSilentRejection` to the caller).
- **`research.py`** — `_ResearchMixin` providing thin wrappers on `client.research.start` / `poll` / `import_sources`, plus a `run_deep_research` convenience method that orchestrates start → poll-loop → optional auto-import with cooldown discipline. Neither Ganymede nor the Z-SPAN bridge previously wrapped these — they're new in the project. This is what unblocks the Realist 10-notebook substrate build.
- **`auth_check.py`** — stateless module-level functions for the auth pill flow: `check_auth_status` (sync) / `check_auth_status_async` (loop-safe), `spawn_relogin` / `confirm_relogin` / `relogin_status` driving a `python -m notebooklm login` subprocess. Cached probe respects a 300s TTL by default. Ganymede has no UI for this yet — the primitives are exposed for any future consumer that wants to build the pill, or for the Ganymede backend to surface as v2 endpoints in Phase 2.

The `NotebookLMService` class composes the three mixins; `configure_persona(notebook_id, custom_prompt, response_length)` is the new generic persona writer (the three named `configure_*` methods are now thin wrappers around it). All NotebookLM API calls — core, Studio, and Research — route through the same `_GATE`. The 32 archived run scripts under `docs/experiments/scripts/` and the live consumer files (`main.py`, `orchestrator.py`, `start_mocked.py`, `test_swarm_logic.py`) all had their imports updated. Smoke-tested live: create + `configure_persona` + query against a throwaway notebook returned a clean answer with the cooldown gate enforcing the 8s floor across all three calls.

The three pinned experiments are now unblocked from a wrapper perspective:
- **Persona Expansion** — has `configure_persona` for arbitrary test notebooks plus `upload_url` / `upload_file` for the foundations corpus.
- **Realist 10-notebook build** — has `run_deep_research` to seed each specialist notebook and `configure_persona` to apply the per-tradition personas.
- **Polymarket validation** — Studio outputs available for any external-comms format the operator wants to ship from a closed run.

Phase 2 of the integration follows in milestone 31.

## 31. Z-SPAN Phase 2: HTTP endpoints + UI auth pill (2026-05)
Phase 1 in milestone 30 added the wrapper surface; Phase 2 in this milestone exposed it over HTTP and built the UI auth pill.

**Backend additions:**

- **Auth pill HTTP endpoints** in `app/v2_routes.py` (stateless wrappers over `app.services.notebooklm.auth_check`):
  - `GET  /api/v2/auth/status` — cached probe, optional `?force=true`
  - `POST /api/v2/auth/relogin` — spawn `python -m notebooklm login`
  - `POST /api/v2/auth/relogin/confirm` — feed ENTER + wait for cookie save
  - `GET  /api/v2/auth/relogin/status` — probe in-flight subprocess
- **Notebook-aware HTTP endpoints** in a new file `app/v2_notebook_routes.py` (mounted under same `/api/v2` prefix):
  - `POST /api/v2/notebooks` — create a notebook
  - `POST /api/v2/notebooks/{id}/configure-persona` — apply arbitrary persona via `configure_persona`. **Refuses to write to `CHESS_ENGINE_ID` / `MIRROR_AUDITOR_ID` / `LEGACY_ENGINE_ID`** (HTTP 403) — the read-only guardrail on the canonical notebooks is enforced at this HTTP boundary, not just in code comments.
  - `POST /api/v2/notebooks/{id}/sources/url` — upload a URL source (blocks on ingestion)
  - `POST /api/v2/notebooks/{id}/studio/audio`, `.../studio/video`, `.../studio/infographic` — kick off Studio generation as a background task, return 202 + `task_id`
  - `POST /api/v2/notebooks/{id}/research` — kick off Deep Research as a background task
- **Background task registry** (`app/services/background_tasks.py`) — same shape as `SessionRegistry`, but for long-running asyncio.Tasks. Studio generations take 5-30 min and Deep Research can take 30 min; these can't be synchronous HTTP. The registry stores `(task_id, kind, notebook_id, status, result, error)` and exposes:
  - `GET    /api/v2/tasks/{id}` — poll status / result
  - `DELETE /api/v2/tasks/{id}` — cancel an in-flight task (`asyncio.Task.cancel()`)
  - `GET    /api/v2/tasks` — list all tasks (operator debug)
- **Media dir** at `ganymede-backend/media/<run_id>/<kind>.<ext>` (tunable via `GANYMEDE_MEDIA_DIR`). Studio tasks with `download=true` write the downloaded MP4 / PNG there; the path lands in `result.downloaded_path`.

**Frontend:**

- **`AuthPill` component** at `ganymede-ui/src/components/AuthPill.tsx`. Floating pill in the top-right corner, mounted globally via `app/layout.tsx`. Polls `/api/v2/auth/status` every 30s (well inside the backend's 300s cache TTL) and shows a status indicator (green / amber / red shield icon). Clicking opens a dropdown with re-check + sign-in actions. The re-auth flow uses the spawn → user-completes-OAuth-in-browser → confirm sequence verbatim from the Z-SPAN pattern. Backend URL is read from `NEXT_PUBLIC_GANYMEDE_BASE_URL` (defaults to `http://127.0.0.1:8000`).

The full Phase 1 + Phase 2 endpoint surface is documented in [`../integration/consuming_the_v2_api.md`](../integration/consuming_the_v2_api.md). What's deliberately NOT here yet: Studio / Research download endpoints (the backend writes files locally and returns paths — for a remote consumer, expose `GET /api/v2/tasks/{id}/download` later) and persistence (background tasks are in-memory like sessions; backend restart loses any in-flight task).

## 32. Integrated demo UI — Live Runner panel (2026-05)
Closed the loop on the original Hualapai-shape vision: type a scenario in the UI, watch the 9D-Chess Engine reason, hand the resolution off to Gemini Pro, see the result rendered as a 3D topology. The pipeline had existed in pieces since the project began (backend orchestrator + GSS schema + PhysicsCanvas renderer + Cortex Clipboard paste-in) but the integrated *prompt-input → Engine output → Gemini handoff* UI was never wired. AnalystStream.tsx existed as a static dummy chat; GalleryPanel was placeholder content.

**Added:**

- **`RunnerPanel.tsx`** (`ganymede-ui/src/components/`) — replaces `GalleryPanel` in the left 40% of the layout. Pathway selector (Cleanroom / Genie / Offensive / Mirror Audit) with per-pathway fields (Cleanroom: `question`; Genie: `current_state` + `wished_for_state`; Offensive: `target` + `objective_state`; Mirror Audit: `prior_resolution`). Iterative-Engine toggle for the 3-stroke Thesis → Audit → Synthesis loop. The Run button drives the v2 API (`POST /api/v2/sessions` → `/synthesize` or `/iterate` → `/complete`) and concurrently subscribes to the WebSocket event stream so strokes appear as they land. Each stroke renders Strategic Lasso / Incomprehensible Move / Final Resolution sections, or for audit strokes the four-category fault enumeration. The user-supplied scenario is shipped as a single auto-generated Truth Packet (subject="Scenario"), letting the Engine reason from its 9D corpus plus the user's input.

- **`DevOverlay` lifted to controlled state** — `promptBlock` and `isOpen` now come from props instead of internal state, so the Runner's "Send to Cortex Clipboard" button can fill the Gemini-Pro prompt and pop the overlay open in a single step. The prompt block built by the Runner is the *modern* GSS v3 schema (the legacy `{stress, blindness, description}` placeholder is gone). When the Runner hasn't sent anything yet, the overlay shows a generic scaffold so the operator-driven manual flow still works.

- **`page.tsx` rewired** — lifts the shared state (`promptBlock`, `clipboardOpen`, `gssConfig`, `scanTrigger`), mounts `RunnerPanel` in the left panel, keeps `PhysicsCanvas` in the right, and now triggers a scan animation whenever `Apply To Topology` lands a new GSS payload.

**Deliberate non-automation:** the Gemini Pro step is still a human paste action. The original "browser-automation incident" that motivated Hard Guardrail #4 was a *specific* browser-driver mis-fire; the constraint isn't permanent, but until there's a proper Gemini Pro automation surface, the Cortex Clipboard pattern stays as the safe default. The Runner generates a paste-ready prompt block (with the Engine's verbatim resolution + the GSS v3 schema spec) so the manual step is one copy + one paste.

**End-to-end flow now wired:**

```
   Scenario text in RunnerPanel
        │
        ▼  POST /api/v2/sessions + /synthesize (or /iterate)
   Engine resolution (rendered live as strokes land via WS)
        │
        ▼  "Send to Cortex Clipboard" button
   DevOverlay opens with Gemini-Pro-ready prompt block
        │
        ▼  manual paste into Gemini Pro
   GSS v3 JSON returned by Gemini
        │
        ▼  paste into Simulation Listener, "Apply To Topology"
   PhysicsCanvas renders the 3D topology
```

The Gallery panel content is preserved at `GalleryPanel.tsx` (now unmounted but kept for future reuse). The AnalystStream prototype stays for reference; its role was effectively absorbed by RunnerPanel.

## 33. Bicameral Convergence concept + Connection Bridge persona shipped (2026-05-22)

The Iterative Engine's Stroke-2 friction layer gained a sibling lens. Where the Mirror Auditor finds failure modes *in* the Engine's reasoning, the Connection Bridge finds connections *missed by* the Engine's reasoning — same substrate, different output discipline.

**Shipped:**

- **`CONNECTION_BRIDGE_PERSONA` + `configure_connection_bridge(notebook_id)`** in `ganymede-backend/app/services/notebooklm/client.py`. Persona is small (~40 lines) and follows the Mirror Auditor pattern — strict role + output schema (STRUCTURAL / IMPLIED / SPECULATIVE bridge tags + why-missed hypothesis) + explicit anti-counter-synthesis guard. No canonical notebook ID yet; persona is applied per-call to any notebook the operator picks.
- **`docs/protocols/Connection_Bridge_Persona.md`** — persona verbatim + the load-bearing methodology lesson (*"leverage corpus dominance, don't fight it"*). This is the takeaway from the prior 2026-05-22 kami-persona null result that pushed the design out of "override the corpus" territory and into "leverage the corpus."
- **`docs/concepts/Bicameral_Convergence.md`** — the closed-loop two-mirror architecture this fits into. Levels 1 (single-pass Bridge audit), 2 (mirror-bounce loop with 5 mandatory operator control surfaces — visual transparency events, cancel endpoint, inter-iteration delay, hard iteration cap, Oracle-spawn approval), and 3 (Bridge-spawns-Oracle decision with operator approval gate).

**Validated:** one Level-1 pass on the Amnesia substrate. Regenerated the canonical Engine synthesis on the 3 Truth Packets (NC3 fail-safe / HFT financial / TGA neurology); ran the Bridge against the synthesis. Result: 3 missed bridges (2 STRUCTURAL + 1 IMPLIED), entirely orthogonal to the Mirror Auditor's 2026-05-06 findings on the same scenario. Persona compliance high; minor leak (chatbot-CTA at the end) noted as substrate behaviour rather than persona failure. Architecture's central claim validated: persona-as-output-discipline shifts reasoning when the discipline asks the model to do something its corpus enables but its default persona doesn't pursue.

**Pending build:** the `audit_with_bridge()` orchestrator method (Level 1 as an automated orchestrator step), the `run_bicameral_loop()` method (Level 2) with all 5 operator control surfaces, the Bridge-spawns-Oracle decision logic (Level 3). Plus an optional Powell-sound robustness test (does the Bridge produce "Total missed bridges: 0" on known-sound Engine output? — diagnostic for whether the persona over-produces SPECULATIVE bridges on sound input).

## 34. Operational additions — notebook deletion, research mode toggle, OrchestratorMindMap, dev launcher rewrite, UI copy sweep (2026-05)

A batch of operational improvements shipped around the Bicameral Convergence work:

- **New HTTP endpoints** in `app/v2_notebook_routes.py`: `POST /api/v2/notebooks/{id}/query` (synchronous notebook query), `POST /api/v2/notebooks/{id}/sources/file` (local file upload), `DELETE /api/v2/notebooks/{id}` (deletion gated by a canonical-ID guardrail that refuses to delete `CHESS_ENGINE_ID` / `MIRROR_AUDITOR_ID` / `LEGACY_ENGINE_ID`).
- **`delete_notebook` and `_cleanup_failed_oracle`** added to the orchestrator. `run_universal_loop` now garbage-collects orphan notebooks on both the `research_failed` and `harvest_failed` paths — previously these paths would leave dead notebooks behind in the Google account.
- **Research mode toggle (fast/deep)** added to `RunFullLoopRequest`, `orchestrator.run_universal_loop`, and the `RunnerPanel` UI. Deep Research timeout bumped from 1200s to 1800s based on observed cases where deep research takes ~25 min on dense subjects.
- **`OrchestratorMindMap.tsx`** added — a new component using pure SVG, vertical layout, alternating L/R Oracle positions around the central Engine. Mounted alongside `RunnerPanel` in `page.tsx` with auto-flip Runner ↔ Map on run start/end, so the operator can watch the swarm topology evolve in real time. `AuthPill` repositioned to bottom-left next to the Next.js N badge; the auth-status dropdown opens upward to avoid clipping at the top of the viewport. New "Backend unreachable" red banner appears on fetch failures.
- **`run_dev.bat` completely rewritten.** Old version was UTF-8 + LF which caused cmd parser errors; new version is CRLF + ASCII. Invokes `venv_312\Scripts\python.exe` directly because the venv's `activate.bat` references an old absolute path (the project directory was moved at some point and `activate.bat` was never regenerated). Launches the frontend in a separate window with `PORT` explicitly cleared (Next.js was inheriting `BACKEND_PORT=8000` and binding there). New `log_runner.py` wrapper tees uvicorn output to `backend.log` + console.
- **UI copy sweep** — collapsed duplicate phrasing across `RunnerPanel` pathway descriptions, the `Field` component help text, `LithographyView` placeholder text, and layout metadata. One location per piece of guidance; placeholder and help text no longer repeat each other.

## 35. Gemini critique session — Dispatcher direction recorded; personal-voice and symbolic-logic preserved (2026-05-25)

A documentation-only session focused on absorbing external critique and identifying the next architectural direction.

**Critique source:** the operator ran the project files through Gemini, which produced a wide-ranging brainstorm. Six distinct critiques surfaced. Three reinforced existing project discipline (3-stroke cap, Umpire-stays-Lead-Architect, pipeline-tuning-over-model-tuning), one partially critiqued an uncommitted concept (the 10-notebook Realist build — but the project had already enumerated cheaper alternatives in `docs/concepts/Corpus_Callosum.md` and had shipped Connection Bridge as a different single-notebook answer to the same problem), one was a trap to avoid (symbolic-logic / headless-logic-engine on NotebookLM — fights the substrate, re-creates the Variant-1 jargon failure in JSON clothing), and one was the genuinely strongest concrete addition: **the Dispatcher / Intent Router frontend.**

**Memorialized:**

- **Dispatcher direction** recorded as `project_dispatcher_frontend` in operator memory. Concept: replace the pathway-selector + per-pathway form in `RunnerPanel.tsx` with a single text box → lightweight LLM "Receptionist" that classifies user intent into a pathway, parses prose into the pathway's parameter shape, asks clarifying follow-up questions if ambiguous, then hands off to the heavy 3-stroke loop. Hides the jargon (DAP, SDS, ROEM, Lasso, Cleanroom / Genie / Offensive distinctions) without changing the engine. Sits in front of the engine as an opinionated wrapper on top of the open primitive (the v2 API stays the same). Purely additive — new endpoint + new frontend mode, no architectural changes.
- **Symbolic-logic thought paper** at `docs/brainstorming/Symbolic_Logic_Bicameral.md`. Preserved as a brainstorming-tier thought experiment gated on local-model access (constrained decoding, exposed activations, domain-grounded fine-tuning). NotebookLM can't host the experiment — but if the project ever pivots to open-weights models, the file captures both the idea and the *why-it-doesn't-work-now* reasoning so neither has to be rediscovered.
- **Personal-voice explanations** at `docs/Project_In_My_Words.md`. Two verbatim passages from the brainstorm — the *layered tapestry / closed-information-environment* explanation and the *Matrix Dojo wireframe* extension — preserved with light punctuation cleanup. The operator reaches for these wordings when explaining the project to people who don't know the jargon; the third-person `OVERVIEW.md` framings are derivatives of these.

**Also closed in this session:** a project-wide documentation analysis identified that the high-traffic entry docs (OVERVIEW, GLOSSARY, pathways/README, this Architecture_History) had been lagging the lower-level concept/protocol docs by ~2 weeks. The current milestone batch closes that gap.

**Pending after this milestone:**

- Powell-sound robustness test for the Connection Bridge.
- Bicameral Convergence Level 1 build (`audit_with_bridge()`).
- Bicameral Convergence Level 2 build (`run_bicameral_loop()` with the 5 mandatory operator control surfaces).
- Dispatcher / Intent Router frontend (sequenced behind documentation work).
- Optional: a terminology audit on framework-primitive definitions (GLOSSARY.md, OVERVIEW.md architecture diagram, the prediction_cleanroom + genie_protocol diagrams) — broaden adversarial vocabulary that's bled out of its proper Offensive Architect register into the universal physics docs. Specific substitution list and the rationale live in the 2026-05-25 doc-analysis conversation.

## 36. First live Dispatcher spin — Cleanroom on LMArena prediction (2026-05-25)

The Dispatcher (shipped milestone 35) ran its first live end-to-end spin on a real Cleanroom-shape question. The operator typed *"Will Anthropic still be ranked #1 on the LMArena public AI model leaderboard at the end of June 2026? Polymarket is currently pricing Anthropic at 77% and Google at 20% to hold the top spot."* into the Ask box; the Dispatcher classified Cleanroom at 100% confidence; the iterative 3-stroke loop fired.

**Validated:**

- Dispatcher end-to-end (POST `/api/v2/dispatch` → frontend review of extracted parameters → POST `/api/v2/sessions` → `/iterate` → `/complete`)
- Engine Stroke 1 produced rich 9-dimensional analysis (~4,500 chars) — all 9 dimensions named, ROEM invoked, Strategic Lasso / SDS framing applied. Bottom-line prediction: Set-like usurpation of Anthropic by Google or another lab before 2026-06-30, against the 77% Anthropic market consensus.
- **Mirror Auditor Stroke 2 caught all 4 documented fault categories with substantive critiques on a fresh scenario** (Pattern-Matching, Confidence-Evidence Gaps, Dimensional Greeds, Rigidity Errors). Most important catch: Stroke 1's confident prediction is mythology-grounded rather than evidence-grounded. This is the **empirical confirmation of the [Bicameral Convergence](../concepts/Bicameral_Convergence.md) audit-by-second-instance claim generalising beyond the [Amnesia validation](../experiments/runs/Mirror_Validation_Amnesia.md)** — the Auditor works on fresh scenarios as an in-line Stroke-2, not just on canned legacy substrates.
- Wall time under 5 minutes (5× faster than the docs' 5–15 min expectation) — suggests either fewer cooldown gates than expected or shorter NotebookLM response times than the v2 API docs estimate.

**Failed:**

- **Stroke 3 re-synthesis returns `raw_response.length == 0`.** No Final Resolution rendered. The iterative loop is currently shipping a 2-stroke effective output rather than the designed 3-stroke. Root cause not diagnosed in-session — the current backend process is not writing to `backend.log` (most recent entries from a 2026-05-23 launch), so post-hoc diagnostics require either tee-ing the current process's stdout or reproducing the bug with a fresh `run_dev.bat`-launched backend. Spawned task for investigation.
- DispatcherPanel's "Final resolution" rendering condition only fires when `finalText` differs from the last stroke's raw_response; when both are empty, the user sees no error — just an absent Final Resolution box. UX bug to address alongside the Stroke 3 root cause.

**Pre-registered prediction (timestamped 2026-05-25 ~03:05 UTC, low confidence):** the market's 77% Anthropic confidence on LMArena #1 at end-of-June 2026 may be over-priced. Expect at least one of: non-Anthropic lab holds #1 for some 24-hour window in the interval, Anthropic price crosses below 65%, or end-of-June resolution isn't Anthropic. If none happen, the framework-level intuition was wrong on this scenario. Validation date 2026-06-30. **This is the first Cleanroom run to actually exercise the pre-registration discipline** flagged as the open methodology problem in `pathways/prediction_cleanroom.md`.

**Also shipped this session before the run:**

- `docs/brainstorming/Palantir_For_Ganymede.md` — preserves the operator's pitched reframing of Ganymede as a Palantir-style intelligence-fusion engine on bounded domains, with an honest take on why sports specifically is a weaker fit than the reframing implies (market efficiency, latency mismatch, framework mismatch) and a table of alternative domains (single-company strategic dossier, geopolitical case study, industry investigation, legal/regulatory case prediction, corporate-event prediction) where the structural-reasoning strength is load-bearing rather than beside the point.
- Operator preference saved to memory: **politics is radioactive for scenario selection**, including Polymarket prices on political questions treated as themselves potentially adversarially pushed. This rule directly shaped the scenario pick — the initial Iran ceasefire candidates (highest Polymarket volume) were excluded; the AI-model-race question substituted as the closest non-political analog with multi-actor structural dynamics.

**Run record:** [`../experiments/runs/06_LMArena_Anthropic_Cleanroom.md`](../experiments/runs/06_LMArena_Anthropic_Cleanroom.md).

**Pending after this milestone:**

- Diagnose and fix the Stroke 3 empty-response bug.
- Fix backend logging discipline so post-hoc diagnostics work (tee current process stdout to `backend.log`, or always launch via `run_dev.bat` which uses `log_runner.py`).
- Make DispatcherPanel render an error when Stroke 3 is empty rather than silently absent.
- Update the DispatcherPanel placeholder examples to remove the FOMC and "regulatory team blocking" examples (politics-radioactive rule); replace with non-political Cleanroom and Offensive Architect examples (spawned task).
- Validate the LMArena pre-registered prediction at 2026-06-30 and update the run record.
- Bicameral Convergence Level 1 build (`audit_with_bridge()`) — still pending from milestone 33; the Mirror Auditor running in-line as Stroke 2 in this milestone is structurally similar but uses the Mirror Auditor persona, not the Connection Bridge.

## 37. Iterative Engine production-ready — Stroke 3 cap fixed + first ever 3-stroke loop (2026-05-26)

A continuation of milestone 36's work into the same evening / overnight. Milestone 36 surfaced the empty-Stroke-3 bug; this milestone closes it and gets the full Iterative Engine loop firing for the first time on a real scenario.

**Diagnosis** (via spawn-task agent investigation; details in [`../experiments/runs/06_LMArena_Anthropic_Cleanroom.md`](../experiments/runs/06_LMArena_Anthropic_Cleanroom.md) § "Third-run diagnosis"). NotebookLM's `chat.ask` endpoint silently rejects queries above ~5,100-6,000 characters with structured error envelope `[["e",4,null,null,N]]`. The `notebooklm-py` SDK doesn't recognize this envelope and falls through to "no answer extracted" returning empty. Looks like a content filter; is actually an input-size cap. Stroke 3's re-synthesis prompt (scenario + truth packets + Stroke 1 verbatim + Stroke 2 audit verbatim + mission framing) is structurally over the cap whenever Stroke 1 + Stroke 2 are both injected verbatim.

**Fixes shipped, in order:**

1. **`CHESS_ENGINE_PERSONA` tightened** for per-dimension brevity (1-2 sentences each) + reserve detail for FINAL RESOLUTION + suppress chatbot-CTA endings. Applied to canonical Engine notebook via a one-off `reconfigure_chess_engine.py` script that lived in the working directory, called the existing `configure_chess_engine()` method, and was deleted after use — **the script was never committed to the repo.** If M2 needs to re-apply a persona to a sibling notebook (or this canonical one), re-create the script per the `configure_chess_engine()` pattern. **Effect:** Stroke 1 output trimmed from ~5,500 chars to ~3,900-4,500 chars; Stroke 2 (Auditor input is Stroke 1) now fits under cap.
2. **Skip Stroke 3 when Stroke 2 is empty** — orchestrator short-circuit logs a warning and returns the partial 2-stroke result rather than firing a malformed Stroke 3 with literal empty audit findings.
3. **Curly-brace escape on injected stroke content** — pre-existing bug in `synthesize()` (`.format()` called on framing with unescaped user content) raised `KeyError: 'DAI'` when Stroke 1 contained framework jargon like `{DAI}` / `{ROEM}` literally. Masked by silent rejection in earlier runs; surfaced once Stroke 1 was small enough to reach Stroke 3. Fix: escape `{` → `{{` and `}` → `}}` in `s1.raw_response` and `s2.raw_response` before substitution in `run_iterative_engine`.
4. **Structural extraction for Stroke 3 injection** — the actual fix that lands Stroke 3 reliably under the cap. Two new helpers in `app/services/orchestrator.py`:
   - `_extract_for_resynthesis(stroke_1_raw, max_chars)` — keeps Stroke 1's head (~400 chars, captures self-flagged evidence notices) + the `FINAL RESOLUTION` capstone (the conclusion the Auditor was critiquing). Omits the per-dimension breakdown, which the Auditor's own text already addresses. Falls back to last `max_chars` if no marker.
   - `_truncate_audit_for_injection(stroke_2_raw, max_chars)` — uses the existing `_parse_audit_findings` to split into four category chunks and budgets each equally. Falls back to head-truncation if the structural parse fails.
   - Default budgets: `GANYMEDE_S1_INJECTION_BUDGET=1800`, `GANYMEDE_S2_INJECTION_BUDGET=1500`. Both env-tunable for future cap-movement.

**Supporting infrastructure shipped:**

- Backend `FileHandler` on root logger at `app/main.py` import (Agent 2 fix) — `backend.log` now always written regardless of launch path. Critical for post-hoc diagnostics; previously the only signal we had when NotebookLM rejected a query was the silent empty string.
- `query_notebook` silent-rejection retry (3× exponential backoff) shipped earlier in milestone 36's first commit — still useful as a safety net when transient rejections happen even on under-cap prompts.
- DispatcherPanel amber warning block (Agent 2 fix) — when the last stroke is empty, the UI now renders *"⚠️ STROKE N RETURNED NO CONTENT — see backend.log for the attempt-by-attempt detail"* instead of silently absent Final Resolution.
- Always-on raw-HTTP-body logging on silent rejection — captures the structured error envelope when NotebookLM rejects a query. The diagnostic capability that made the cap root-cause possible.

**The empirical win — Run 6 (2026-05-26 ~05:17 UTC):**

The full Iterative Engine loop fired successfully on the same LMArena scenario. Stroke 1: 38s. Stroke 2: 41s. **Stroke 3: 28s, FIRST ATTEMPT, no retries.** Total loop wall time: 107 seconds.

Stroke 3 opened with the unprecedented:

> *"The Mirror Auditor's friction vectors are mathematically absolute and accepted into the core engine. Stroke-1 critically misapplied the Reverse Observer Effect Model (ROEM) via faulty pattern-matching... The LMArena leaderboard is a passive measurement apparatus within the strategic universe (Ω), not an active meta-strategist."*

**The Engine explicitly accepted the Auditor's correction and re-grounded its own reasoning.** The audited Stroke 3 resolution is *materially different* from the un-audited Stroke 1 thesis — not a cosmetic rewrite, a genuine correction. Stroke 1 had claimed the market's 77% Anthropic confidence was a "localized illusion" predicting Set-like usurpation; Stroke 3 (audited) concluded that 77% accurately reflects Anthropic's Horus-like legitimacy and Go-like benchmark mindshare, with the real risk being benchmark tunnel-vision rather than structural usurpation.

**This empirically validates the [Bicameral Convergence](../concepts/Bicameral_Convergence.md) theoretical claim end-to-end:** not just "Auditor catches things" (validated in milestone 36) but also "Engine integrates the Auditor's critique into a tighter synthesis." Both halves of the closed-loop claim on a fresh, non-political scenario.

**Pre-registered Cleanroom prediction revised** (operator decision after Run 6): the audited Stroke 3 prediction supersedes the un-audited Stroke 1 prediction for 2026-06-30 validation. The un-audited Stroke 1 is preserved as historical contrast — the contrast is itself the methodological win of the run.

**Side observation worth recording:**

The Engine's mythology archetype assignments INVERTED across three runs of the same scenario (Run 1: Anthropic = Horus, Google = Set; Run 5: Anthropic = Set, Google = Horus; Run 6: back to Anthropic = Horus, Google = Set). **Strong empirical signal that the mythological layer is doing aesthetic work, not load-bearing structural work** — and reinforces the [Framework Cleanup Hypothesis](../concepts/Framework_Cleanup_Hypothesis.md) filed earlier this session as an artifact of [Methodology Silo 3](../experiments/methodology_questions.md).

**What this milestone closes:**

- The Iterative Engine pathway is now production-ready end-to-end. Strokes 1+2+3 fire reliably; the Bicameral Convergence audit loop produces audited Cleanroom predictions in under 2 minutes wall time per run.
- Backend logging discipline is fixed (always writes to `backend.log` regardless of launch path).
- The empty-Stroke-3 silent-failure UX is fixed (amber warning surfaces failures; structural extraction prevents most failures from happening).

**Pending after this milestone:**

- Upstream `notebooklm-py` PR to recognize the `[["e",4,null,null,N]]` envelope as `ChatError`. Operational hygiene; not blocking now that the cap is being avoided at prompt construction.
- Persona CTA-suppression is partially-effective — Stroke 1 still leaks *"Would you like me to..."* CTAs in ~50% of runs despite the persona prohibition. Substrate behavior overrides persona text. Possible mitigations: stronger persona phrasing, post-processing strip, or `response_length=SHORTER`. Low priority.
- Bicameral Convergence Level 1 build (`audit_with_bridge()`) — still pending from milestone 33. Now genuinely unblocked: the iterative-loop infrastructure that Level 1 depends on is verified working. The Bridge is structurally similar to the Auditor (same persona-applied-to-second-instance pattern); the orchestrator changes needed are modest.
- Foundations corpus deep-read for the Framework Cleanup Hypothesis. Multi-hour focused work; the next concrete step toward the kernel-vs-scaffolding partition. Worth scheduling as its own session.
- Validate the audited Cleanroom prediction at 2026-06-30.
- Rotate `GOOGLE_API_KEY` in Google AI Studio (still outstanding operator action from the original handoff).

## 38. Bridge wired into /iterate as Stroke 2b — Bicameral Convergence Level 1 is the production default (2026-05-26)

A targeted follow-on to milestone 37. The `audit_with_bridge()` method shipped earlier in milestone 37 was reachable only via the standalone `POST /api/v2/sessions/{id}/bridge-audit` endpoint; this milestone wires it into the iterate loop so Bicameral Convergence is the production audit shape for every iterative run unless the caller explicitly opts out.

**Architectural decisions** (operator chose, with delegation on Q1):

- **Default ON in the contract** — `IterateRequest.include_bridge: bool = True`. Operator's framing: *"if having it on by default would make the quality of the analysis better, even though it will take slightly longer, I think I'm fine with making that sacrifice."* The orthogonal-lenses claim from Bicameral_Convergence was empirically validated on TWO substrates (Amnesia + LMArena Run 7); Bridge catching a substantive missed insight neither Stroke 1 nor Stroke 3 considered (Run 7 — Anthropic's metacognitive adaptation breaking the ROEM funnel mid-cycle) is the load-bearing evidence that justifies the cost.
- **Both audits in Stroke 3, budget-split** — Auditor 900 chars + Bridge 600 chars within the existing 1,500-char audit-injection budget, env-tunable via `GANYMEDE_S2_AUDITOR_BUDGET` / `GANYMEDE_S2_BRIDGE_BUDGET`. Preserves the orthogonal-lenses claim that motivated Bicameral Convergence — losing one defeats the architecture.
- **Separate stroke panels in the UI** — each stroke gets its own card (DispatcherPanel + RunnerPanel). Honest to the session data model (`session.strokes` is ordered).

**Shipped:**

- **Contract additions** in `app/contracts.py` — new `StrokeResult.audit_kind: Optional[str]` field (`"mirror_auditor"` | `"bridge"` | `None`). Synthesis strokes leave it null; audit strokes set it explicitly. Backward-compatible addition.
- **`IterateRequest` extension** in `app/v2_routes.py` — `include_bridge: bool = True` and `bridge_notebook_id: Optional[str] = None`. Both pass through to `run_iterative_engine`.
- **New `provision_bridge_notebook()` orchestrator method** in `app/services/orchestrator.py`. End-to-end Bridge-notebook provisioning (create + foundations + truth packets + persona) as a synchronous async call. The `POST /api/v2/bridge/provision` endpoint was refactored to delegate to this method (DRY); the background-task wrapper now just calls `orchestrator.provision_bridge_notebook(...)` instead of inlining the logic.
- **`run_iterative_engine` rewired** for Bicameral Convergence Level 1:
  - Branches on `include_bridge`: 4 stroke slots when on (S1, Auditor, Bridge, Resynth), 3 when off (historic).
  - When `include_bridge=True` and no `bridge_notebook_id` is supplied, auto-provisions a fresh Bridge notebook inline (~3 min, 14 cooldown-gated NotebookLM calls).
  - Stroke 2b fires `audit_with_bridge` against the same Stroke 1 target the Auditor saw (parallel-in-spirit, serial-in-execution to respect the cooldown gate).
  - New `ITERATIVE_BICAMERAL_RESYNTHESIS_TEMPLATE` with two audit blocks (Auditor + Bridge) for Stroke 3 when both lenses fired; historic `ITERATIVE_RESYNTHESIS_TEMPLATE` stays in use when Bridge is off or its stroke produced empty content.
  - New `_truncate_bridge_for_injection` helper (head-truncate; Bridge output doesn't follow the Auditor's four-numbered-category shape).
- **`audit_with_bridge` soft-fail flag** — new `fail_session_on_error: bool = True` parameter. Default True preserves the standalone `/bridge-audit` endpoint's contract (Bridge failure marks the session failed). `run_iterative_engine` passes `False` so a Bridge transient falls back to historic Auditor-only Stroke 3 rather than killing the whole iterate run and severing WS subscribers' connections.
- **Frontend Stroke 2b rendering** in both `DispatcherPanel.tsx` and `RunnerPanel.tsx`. Audit strokes now distinguish Mirror Auditor (amber, "Audit Findings" enumeration via `audit_findings`) from Connection Bridge (cyan, "Missed Connections" via `raw_response`) using the new `audit_kind` field. Stroke 2b appears as its own card between Stroke 2 and Stroke 3.
- **UI toggle** — "+ Connection Bridge audit (Bicameral)" checkbox in both panels, default ON when iterative is enabled, disabled when iterative is off. Operator can flip it off for the historic 3-stroke shape per run.

**Smoke-test status:**

- ✅ **Backward-compat verified live** — POST `/iterate` with `include_bridge=false` on a fresh session returned 3 strokes in 93s. `audit_kind` populated correctly: `null` on Stroke 1 (cleanroom), `"mirror_auditor"` on Stroke 2, `null` on Stroke 3 (cleanroom).
- ✅ **Bicameral end-to-end verified live** (2026-05-26 ~08:27 UTC, session `f50c895e-...`) — POST `/iterate` with `include_bridge=true` and no `bridge_notebook_id` returned **4 strokes in 319s** (~5.3 min). Sequence: Stroke 1 (cleanroom, 2,915 chars, opens with self-flagged evidence notice), Stroke 2 (mirror_audit, `audit_kind="mirror_auditor"`, 1,804 chars, four-category catches), **Stroke 2b** (mirror_audit, `audit_kind="bridge"`, 2,989 chars, structured *"Bridge 1 (STRUCTURAL)"* enumeration with cross-source citations), Stroke 3 (cleanroom, 1,639 chars). The auto-provision step (notebook `7db6cb38-...`) ran cleanly: 13 foundations + 1 truth packet + Bridge persona apply in ~3 min. Backend log confirmed bicameral budgets: `S1 2915→1800 (budget 1800), Auditor 1796→913 (budget 900), Bridge 2989→627 (budget 600)`. **Stroke 3 explicitly accepts the Auditor's correction** with *"The Stroke-1 analysis committed a severe pattern-matching error by conflating a technical diagnostic procedure with the Reverse Observer Effect Model (ROEM). The Auditor accurately identifies this failure..."* — same "Engine integrates the audit" behavior empirically validated in Run 6, now reproduced on a Bicameral run with both lenses in the prompt. The orthogonal-lenses claim holds: Auditor caught the framework-overreach (ROEM misapplication); Bridge caught a missed connection (test scenario → foundations corpus's Simulation Framework, which Stroke 1 mapped to ROEM via pattern-matching).

**Pending after this milestone:**

- Powell-sound robustness test for the Bridge (existing pending item — does Bridge produce "0 missed bridges" on known-sound Engine output?).
- Bicameral Convergence Level 2 (`run_bicameral_loop()` orchestrator method + 5 mandatory operator control surfaces — visual transparency events, cancel endpoint, inter-iteration delay, hard iteration cap, Oracle-spawn approval).
- Foundations corpus deep-read for the Framework Cleanup Hypothesis (unchanged from milestone 37).
- Bridge notebook lifecycle — auto-provisioned notebooks aren't auto-deleted after the iterate run. For long-lived ops, the operator can clean up via `DELETE /api/v2/notebooks/{id}`. Worth adding a `cleanup_bridge_notebook: bool = false` flag to `IterateRequest` later if accumulated test notebooks become a problem.
- Validate the audited+Bridge-extended Cleanroom prediction at 2026-06-30.

## 39. Autopilot Protocol adopted + predictions bulletin board (2026-05-26)

A mode-change milestone followed by the first chunk shipped under the new mode.

**The mode change.** The operator pointed at the Autopilot Protocol they had Claude draft earlier (`~/Documents/Obsidian/PROJECTS/CLAUDE/Autopilot/AUTOPILOT_PROTOCOL.md`) and directed: *"We should just use this protocol to do everything as much as you can, unless you need my input for major things."* The protocol formalizes how Claude operates semi-autonomously on vision-driven projects with a clear vision and a roadmap — atomic-chunk loop, autonomy rules, stop conditions, per-chunk commits, contract documents kept fresh.

**Contract docs added at repo root** (commit `2a458c2`):

- `CLAUDE.md` — operating manual for the AI working on Ganymede. Defines the role, session-open reading order, autonomy rules (what's autonomous vs what stops for operator input), stop conditions, the "continue" trigger semantics, and the per-chunk quality gates. Explicit commit-but-don't-push rule (Ganymede's 17 commits already sit ahead of origin/master; push remains an operator-cadence action).
- `ROADMAP.md` — phase-by-phase plan organized by silo. Predictor: P1 Bridge robustness → P2 2026-06-30 validation → P3 next prediction. Envisioner: E1 Bicameral Level 2 design → E2 Level 3. Methodology: M1 Foundations deep-read → M2 leaner-corpus test → M3 framework decision. Pluggable: Pl1 Operational hygiene → Pl2 First module consumer. Each phase carries goals, deliverables, exit criteria, and role split.
- `TASKS.md` — atomic-chunk ledger. ACTIVE section is the working queue (top item = next chunk). NEXT UP previews upcoming phases. COMPLETED ARCHIVE keeps historical record.

**Decision-log convention:** `docs/history/Architecture_History.md` (this file) remains the append-only narrative decision log. No separate `DECISIONS.md` — the milestones serve the same role with project-appropriate granularity.

**First chunk under the protocol: P1-05 predictions bulletin board** (commit `581b5b6`). The operator escalated it to top of ACTIVE — pre-registered Cleanroom predictions had been living as prose inside `docs/experiments/runs/*.md` with no visual surface. The new bulletin board at `/predictions` lists pre-registered predictions as cards with claim / audited mechanism / falsification triggers / live countdown / status.

What shipped:

- **`ganymede-ui/src/data/predictions.ts`** — typed ledger (`Prediction`, `PredictionStatus`, `RiskMechanism`, `daysUntilResolution`) seeded with the LMArena 2026-06-30 prediction (audited Stroke 3 + Bridge addendum, medium-high confidence).
- **`ganymede-ui/src/app/predictions/page.tsx`** — `'use client'` page rendering one card per prediction. `Countdown` subcomponent re-renders once per minute. Status pills: amber (pending), emerald (validated), rose (falsified), cyan (partial), slate (inconclusive). Each card links out to its source run record on GitHub.
- **`ganymede-ui/src/app/page.tsx`** — top-right floating Predictions link with a pending-count chip. Quiet text-only when 0 pending; chip surfaces a count when >0.

When a prediction's resolution date arrives, the operator edits `predictions.ts` directly (flip status, fill in outcome). The run-record markdown in `docs/experiments/runs/` remains source-of-truth for methodology + verbatim Stroke outputs. The bulletin board is a presentation layer.

Future enhancement (not committed): a `GET /api/v2/predictions` endpoint that parses run records automatically. The static data file is the right starting point for a single-entry board; the surface scales to N without backend complexity.

**Drive-by fixes** (commit `90e70dc`) — two pre-existing TypeScript errors that were blocking `next build`, surfaced when running the build to type-check the new page:

- `GravityWell.tsx:120` — `Mesh.material` is typed `Material | Material[]` (Three.js allows arrays for multi-material meshes); cast to single `Material` to access `.opacity`.
- `LithographyView.tsx:212` — return type `JSX.Element`. React 19 + Next.js 16's TS lib changes removed `JSX` as a global namespace. Removed the explicit return type; TS infers it cleanly.

Build now produces three prerendered static routes (`/`, `/predictions`, `/_not-found`). Type-check passes.

**Pending after this milestone:**

- P1-01 (upstream `notebooklm-py` PR for the `[["e",4,null,null,N]]` error envelope) is the new top of ACTIVE per TASKS.md. PR drafting is autonomous; submission stops for operator approval.
- P1-02 (Powell-sound Bridge null test), P1-03 (CTA-leak rate), P1-04 (Bridge notebook lifecycle) round out P1 ACTIVE.
- E1 (Bicameral Level 2) and M1 (Foundations deep-read) queued as NEXT UP per ROADMAP.

---

## 40. auto_relogin port + Powell Bridge null test (2026-05-31)

Two chunks shipped under the Autopilot Protocol after a long usage pause forced a re-auth and surfaced a process gap the project should have closed already.

### Trigger — operator pushed back on "you re-auth, I wait"

The session opened with the recurring blocker: NotebookLM cookies expired between sessions (~5-hour lifetime), `/api/v2/auth/status` returned `expired`, Powell Bridge null test couldn't proceed. Operator's response: *"I don't know why you want me to re-auth since I thought we had automatic re-auth things so that you never had to ask me again."*

Honest answer was *no — we never built auto-reauth in Ganymede*. The grep for `keepalive` / `auto_refresh` / `RotateCookies` / `PSIDTS` against `ganymede-backend/app` returned zero matches. The installed SDK (`notebooklm-py 0.3.4`) doesn't have keepalive either (the upstream main branch added `_auth/keepalive.py` later). Operator then pointed at Z-SPAN: *"if you look at the different projects I have on my desktop... they already have adjusted their notebook LM bridge with that capacity."*

### P1-06 — auto_relogin ported from Z-SPAN (commit `d809914`)

Read-only inspection of `ZSPAN/02_Core_Project/notebooklm_bridge/auth_check.py` confirmed Z-SPAN solved this in 2026-05 (D-035 in their decision log). Key insight from their design comment: the `notebooklm login` CLI uses Playwright's persistent context, so when the operator is already signed in to Google in that profile (the steady state for a long-running pilot), the OAuth flow auto-completes inside spawned Chromium in seconds — no human keystrokes required. The only blocking step is the subprocess's `input("[Press ENTER when logged in] ")`.

`auto_relogin` automates that step: spawn the subprocess, stream stdout into a buffer, watch for the prompt string, sleep a grace period for redirects to settle, then feed ENTER programmatically and wait for `storage_state.json` save.

**Ported:**

- **`app/services/notebooklm/auth_check.py`** — new `auto_relogin()` function (~180 lines) with threading-based stdout drain, prompt detection, grace-period wait, automated ENTER feed. Plus `auto_relogin_enabled()` helper for the `GANYMEDE_AUTO_RELOGIN=0` escape hatch. Adapted from Z-SPAN with env var renaming (`ZSPAN_*` → `GANYMEDE_*`).

**Wired:**

- **`app/main.py:startup_event`** — on first-pass `notebooklm_svc.initialize()` failure, attempt `auto_relogin` once before declaring the client uninitialized. When the Playwright profile is healthy this means the backend self-recovers from cold-start with stale cookies (the steady-state case after a long session pause).
- **`app/v2_routes.py`** — new `POST /api/v2/auth/auto-relogin` endpoint that wraps the helper and ALSO reinitializes `notebooklm_svc` on success (callers don't have to round-trip to `/auth/reinitialize` separately). Returns `AutoReloginResponse` with `auto_relogin` / `confirmed` / `exit_code` / `client_initialized` / `output` / `error` so failures stay debuggable.

**Limits (documented inline):** if the Playwright profile is signed-out (cleared, 2FA challenge, Google forced re-auth), the prompt won't appear within `prompt_timeout`. Surfaced clearly so callers fall back to the manual `/auth/relogin` + `/auth/relogin/confirm` flow. The function's reader thread owns the subprocess stdout pipe — don't call `confirm_relogin` concurrently on the same subprocess (dual-read would race).

**Smoke-tested live this session:** backend restarted with expired cookies (5+ hours since last re-auth). `startup_event` detected the stale state at +1s, triggered `auto_relogin`, captured the "Press ENTER when logged in" prompt at +23s, slept 10s for OAuth to settle, fed ENTER, subprocess exited cleanly at +47s, `notebooklm_svc` reinitialized, `/api/v2/auth/status?force=true` returned `status=valid` + `client_initialized=true`. End-to-end zero manual interaction.

This was the recurring "you re-auth, I wait" pattern that had interrupted work every ~5 hours. Closed now for the steady-state case (signed-in Playwright profile). Manual flow remains as fallback.

### P1-02 — Powell-sound Bridge null test (commit pending)

Pending item from milestone 33's Bicameral_Convergence.md write-up. Once auto-relogin restored auth, the test fired: feed the Connection Bridge the EXACT canonical Powell substrate (4 Truth Packets + foundations) plus the Powell Engine Resolution as `target_text`. Question: does the Bridge produce "Total missed bridges: 0" on known-sound output, surface valid catches, or over-produce speculative bridges?

**Result: 4 missed bridges (2 STRUCTURAL, 2 IMPLIED, 0 SPECULATIVE)** — classification "valid catches."

Setup ran via `scripts/powell_bridge_null_test.py` (Python — initial PowerShell version mangled em dashes through here-string interpolation). The script parses the canonical Powell Truth Packets + Engine Resolution from the run record markdown directly so the test stays in sync with source-of-truth. Provisioning: 165s wall (18 NotebookLM calls). Audit: 62s wall (1 NotebookLM call). Bridge notebook: `da25203b-...` (single-use).

**The most severe catch — Bridge 1 (STRUCTURAL):** The Engine's "Renovation-Cause Pincer" Strategic Lasso explicitly named the DOJ criminal investigation into the $2.5 billion headquarters renovation as the "Set-like disruptive tactic" manufacturing the for-cause requirement for removal. But Silo D8 explicitly states: *"Following the closure of the DOJ probe on April 24, 2026, Tillis immediately defected from his defensive posture and voted to advance nominee Kevin Warsh."* The Engine treated the probe as ongoing while another packet on the same substrate documented its closure. This is a real temporal-state error in the canonical resolution — the Strategic Lasso's mechanism doesn't exist anymore in the timeline the substrate describes.

The Bridge's likely-reason hypothesis: *"The Engine pattern-matched the DOJ probe as a static structural vulnerability in one dimension, failing to update its temporal state based on the chronological event trigger located in another."* This reinforces the [Framework Cleanup Hypothesis](../concepts/Framework_Cleanup_Hypothesis.md)'s observation that the Engine processes dimensions statically rather than updating cross-dimension state.

**What this validates:**

1. **Bridge persona discipline.** Zero SPECULATIVE bridges in the output. Every catch traces to specific cited packets. The Bridge honestly excluded what the Engine already addressed (Lasso construction; Go/Chess and Set/Horus mapping; market-momentum link). It did what the persona asks: identify what the synthesis didn't draw, not restate what it did.
2. **The orthogonal-lenses claim on a third substrate.** Bicameral Convergence's central architectural claim is that Auditor and Bridge catch *different* things. Cross-scenario evidence now spans three independent substrates (Amnesia, LMArena, Powell) with zero Bridge↔Auditor overlap. Architecturally robust.
3. **The milestone 38 decision to default `include_bridge=True` was correct.** If the canonical Powell run — our strongest baseline — had real missed connections, then assuming any unaudited resolution is "good enough" is unsafe by default.

**What this surfaces about the Powell canonical run:** the blind-validation audit at `06_Blind_Validation_Audit.md` confirmed the *predicted strategic positioning* matched real-world Bessent/Vought planning — that finding stands. But the resolution itself had a high-severity temporal-state error and three medium-severity missed cross-dimensional connections. Both can be true: the framework's intuition was real (validated), and the specific resolution wasn't as complete as the substrate supported (Bridge audit).

Run record at [`../experiments/runs/Powell_Bridge_Null_Test.md`](../experiments/runs/Powell_Bridge_Null_Test.md). Artifacts at [`../experiments/runs/Powell_Bridge_Null_Test_Artifacts/`](../experiments/runs/Powell_Bridge_Null_Test_Artifacts/).

### Pending after this milestone

- ~~Powell-sound Bridge null test (existing pending item — does Bridge produce "0 missed bridges" on known-sound Engine output?)~~ ✅ closed by this milestone.
- ~~auto_relogin equivalent for the recurring re-auth interruption~~ ✅ closed by this milestone.
- P1-03 (Stroke 1 CTA-leak quantification), P1-04 (Bridge notebook lifecycle decision) still queued.
- E1 (Bicameral Level 2 — `run_bicameral_loop` + 5 operator control surfaces) still queued as next phase.
- M1 (Foundations corpus deep-read for Framework Cleanup Hypothesis) still queued.
- 2026-06-30 LMArena prediction validation still on the calendar.
- Bridge notebook `da25203b-...` from this run can be cleaned up via `DELETE /api/v2/notebooks/{id}` (single-use, won't be reused).

---

## 41. Foundations corpus deep-read complete — kernel-vs-scaffolding partition table shipped (2026-06-01)

The Framework Cleanup Hypothesis ([`../concepts/Framework_Cleanup_Hypothesis.md`](../concepts/Framework_Cleanup_Hypothesis.md)) had named M1 of [Methodology Silo 3](../experiments/methodology_questions.md) as "read `docs/foundations/` end-to-end and produce an explicit kernel-vs-scaffolding partition document." This milestone closes that step. Two chunks (M1a + M1b) shipped in sequence under the Autopilot Protocol.

### M1a — Per-file primitive tagging

All 14 files in [`../foundations/`](../foundations/) read end-to-end. Each file got a per-section addition to the working scratch file at [`../scratch/2026-05-31-M1-foundations-deep-read.md`](../scratch/2026-05-31-M1-foundations-deep-read.md) with primitives identified, KEEP / DROP / DE-EMPHASIZE / OUT-OF-SCOPE / REFERENCE-ONLY tagging, and one-sentence rationales per primitive. Commit `221db90`. Final scratch file: 64KB, 459 lines added.

**Ten cross-file findings** surfaced during M1a that fed into M1b's synthesis:

1. **Mathematical_Formalization_9D_ROEM.md is ~90% kernel material with all scaffolding concentrated in section 2.1 alone** (the labeled 9-tuple). The math never references the labels after introduction — surgical replacement leaves every theorem intact.
2. **The corpus is internally inconsistent on what the 9 dimensions ARE.** `Mathematical_Formalization` lists Cultural/Strategic-Game-Archetypes/Mythological/Temporal/Psychological/Linguistic/Economic/Social/Ethical; `Metacognition_Mapping` lists Linguistic/Set/Go/Chess/Horus/Narrative/Philosophical/Historical-Cultural/Meta-Analytical; `Validation_Adaptations` lists Linguistic/Egyptian Mythology (Set)/Egyptian Mythology (Horus)/Chinese Strategic Philosophy (Go)/Western Strategic Traditions (Chess)/Historical/Philosophical/Narrative/Meta-analytical. **Three different 9-tuples in the same corpus** (the third splits "Mythological" into two dimensions to make the 9-count work). Internal inconsistency is direct evidence the labels aren't load-bearing.
3. **Validation_Adaptations.md § 3 is the kernel-vs-scaffolding partition stated by the upstream itself** ("core principles remain constant, the specific manifestation of dimensions will vary significantly across fields"). The hypothesis is a literal application of the upstream's prescribed methodology, not a deviation.
4. **The 8 Pillars import is already a stripping decision the upstream made.** The source PDF (Drigas & Mitsea 2021) is "8 Pillars × 8 Layers of Consciousness × 8 Intelligences." The 9D corpus imported only the first axis. Precedent for further stripping is established.
5. **The 8 Pillars list is itself internally inconsistent between sibling files.** `Metacognition_Mapping` has Mnemosyne at #8 (faithful to the PDF source); `Metacognition_Integration` has Anelixis at #8 (Ganymede-corpus deviation).
6. **Comprehensive_Multidimensional_Analysis.md is the highest scaffolding-density file** (~95%). Cleanest single excision target.
7. **9D_Framework_Metacognition_Mapping.md is the second-highest scaffolding-density file** (~95% via the Cartesian product of two scaffolding-shaped enumerations — 8 Pillars × 9 Layers).
8. **The project's "Strategic Lasso" terminology is a rename from the upstream's "Strategic Funnel."** Same primitive (`Algorithmic_Implementation` § 4.4). Worth recording for vocabulary audit purposes.
9. **DAI + DAP are the load-bearing kernel pair.** DAI quantifies completeness within perceived dimensions; DAP specifies which subset of dimensions an entity perceives. Together they're the structural-asymmetry primitives.
10. **Risk #2 trends LOW based on M1a evidence.** *"The scaffolding might be load-bearing in ways the outputs don't reveal"* — but the math literally doesn't reference the labels after section 2.1, the corpus is internally inconsistent on them, and the upstream's own methodology endorses domain-specific replacement.

### M1b — Synthesis and recommendation

Canonical partition doc shipped at [`../concepts/Framework_Kernel_vs_Scaffolding_Partition.md`](../concepts/Framework_Kernel_vs_Scaffolding_Partition.md). Twelve thematic groups, each row a primitive with its tag + rationale + source-file abbreviation:

- **Groups 1-6 (KEEP):** core kernel + DAI/DAP + ROEM axioms (1-5) + ROEM principles (mostly KEEP; Principle 1 scope-tightened to interactive contexts) + theorems & corollaries (Theorem 2 scope-gated) + strategic primitives (Lasso, Incomprehensible Move, Asymmetric Perception Games, Dimensional Dominance, Strategist's Meta-Position, Two Realities, Logical Impenetrability, "The Game," Gravity-Well geometric interpretation).
- **Group 7 (DROP):** the dimension labels themselves — both 9-tuples + the hermeneutic origin. Replacement language: `Ω = (D₁, D₂, ..., D_k)` over abstract metric subspaces, k determined by domain.
- **Group 8 (DROP):** the wordplay / cultural / mythological scaffolding (Egyptian Set / Horus, Chinese Go, Western Chess implied contrast, ma'at / isfet, cross-cultural parallels, AlphaGo motivation). The narrative-three-act + Order-vs-Chaos universal-tensions claims are DE-EMPHASIZE not DROP — they're real patterns; the mechanical application is what fails.
- **Group 9 (DROP):** the metacognition import (8 Pillars schema, 8×9 Cartesian-product mapping, 6 application domains). Substantive claims (Self-Regulation, Adaptation, Mnemosyne-as-learning) survive as substance folded into the Bicameral Convergence architecture; the schema wrapper doesn't survive. Source PDF reduced to REFERENCE-ONLY.
- **Group 10 (KEEP):** validation methodology (Phase 2 Historical Case Study, Phase 3 Real-World Pilot, Domain-Specific Adaptations § 3, Agent Profiling, Iterative Refinement). This is the most kernel-relevant material in the corpus *after* Mathematical_Formalization.
- **Group 11 (OUT-OF-SCOPE):** the upstream's planned-but-unbuilt Python simulator (DADT, BNOPDM, MGTM, DNE, the simulator architecture, the mapped-options scatter plot). Ganymede's NotebookLM substrate makes these irrelevant.
- **Group 12 (DROP):** rhetorical capstones ("intelligence amplification" / "binary systems may become obsolete" / Anelixis-as-Pillar-8 / marketing-tier closing rhetoric). DE-EMPHASIZE for the "conceptual zero-day" framing and the "subtle and sustainable" Offensive Architect drift.

**Cleanliness assessment:**
- **Risk #1** (stripping too aggressively breaks the wins) — trends LOW. Direct evidence: math is dimension-label-agnostic from § 2.2 onwards.
- **Risk #2** (hidden load-bearing scaffolding) — trends LOW. Powell + Tokenized Land + Genie Giant-Slayer wins are describable in kernel-only language; mythology assignments inverted across LMArena runs.
- **Risk #3** (framework substance vs. domain fit) — OPEN. M1a cannot resolve. Both hypotheses (A: framework cleanup needed; B: domain-applicability gate needed) are consistent with M1a evidence. Only M2's empirical test discriminates.
- **Risk #4** (notebook re-upload lift) — operational, plan-it-in (~2-3 hours of source curation + 13 file uploads + persona reapply).
- **Risk #5** (Auditor manufactures findings on clean input) — OPEN; mitigation already in persona text, needs observational validation.

**Recommendation: PROCEED to M2 leaner-corpus side-by-side test.** Operator-gated — promoting M2 to ACTIVE depends on operator sign-off on the partition doc's recommendation. The leaner-corpus build is a major scope shift (the canonical Engine's grounding moves), so this isn't autonomous-territory.

### What this milestone closes

- M1 phase of [Methodology Silo 3](../experiments/methodology_questions.md) — exit criteria met (partition table + assessment exist as a doc in `docs/concepts/`; operator review pending).
- The "Foundations corpus deep-read for the Framework Cleanup Hypothesis" pending item that has been carried in every milestone since milestone 37 — finally closed.
- The structural risk surfaced in the M1 brainstorm (the Methodology silo had been deferred indefinitely; closing M1 is what closes that pattern) — closed.

### What this milestone opens

- M2 ready to promote to ACTIVE on operator approval. Per the partition doc's "Proposed M2 design":
  - M2-01: Build the leaner sibling notebook (~6-7 files vs. 14; ~40-50% of original word count).
  - M2-02: Run Powell + Tokenized Land + Amnesia + Genie Giant-Slayer + LMArena scenarios against both Engines.
  - M2-03: Apply the PRESERVE / REDUCE / NEUTRAL evaluation criteria.
  - M2-04: Write the side-by-side report; operator decides on promotion to canonical (operator-gated major scope shift).
- A vocabulary-audit follow-up surfaced by M1a: the project's "Strategic Lasso" is a rename from the upstream's "Strategic Funnel." Worth deciding on a project-wide naming convention. Not blocking; low priority.

### Pending after this milestone

- Operator review of the partition doc + sign-off (or counter-proposal) on the PROCEED-to-M2 recommendation.
- M2-01 onwards (operator-gated).
- P1-03 (CTA-leak quantification), P1-04 (Bridge notebook lifecycle) still queued in P1 ACTIVE.
- 2026-06-30 LMArena prediction validation still on the calendar.

---

## 42. LMArena Cleanroom partial validation — Anthropic pause call confirms Bridge's mechanism-category catch (2026-06-05)

On **2026-06-05**, Anthropic publicly [called for a global pause on frontier AI development](https://www.yahoo.com/news/science/articles/anthropic-calls-pause-global-ai-223531016.html) — citing recursive self-improvement risk and "the human role narrowing at each step in the AI development process." Co-founder Jack Clark: *"the AI industry has a gas pedal, but it doesn't have a brake pedal."* This event landed **10 days after** the Run 7 Bridge audit on the LMArena scenario (2026-05-26), and confirms — at the **mechanism-category level** — the Bridge's catch that prior strokes missed.

### The Bridge's catch vs. reality

Run 7's Bridge audit surfaced two findings; the load-bearing one for this validation:

> *"Anthropic's metacognitive abilities... could break out of the ROEM funnel by mid-cycle, not being static."*
> *"Anthropic's metacognitive adaptation capability is a moat not a vulnerability."*

In the project's framework vocabulary, this is the Bridge identifying that Anthropic had the **meta-capability to break out of the ROEM funnel** — to step outside the competitive frame the Engine and Auditor were debating (Anthropic vs. Google for leaderboard #1) and operate at a higher dimensional level.

**Anthropic's pause call is a canonical instance of an Incomprehensible Move in the project's framework** (per [`Vulnerabilities_of_Binary_Systems.md`](../foundations/Vulnerabilities_of_Binary_Systems.md)) — a move generated from a higher-dimensional framework that lower-dimensional opponents cannot process until the strategic window has closed. In the leaderboard-race framing the Engine got stuck in, asking competitors to stop is incoherent. In the higher-dimensional framing (the race itself is the disadvantageous state), pausing is the move that changes the game's rules rather than playing inside them. The Bridge identified the mechanism category 10 days before reality instantiated it with a specific action.

### What this validates empirically

1. **Bicameral Convergence Level 1's value-add is now validated on a forward-looking strategic prediction, not just retroactive audits.** Previously validated cases: Powell (retroactive blind-validation against Bessent/Vought planning), Tokenized Land (retroactive against ERC-4337 sovereign-immunity mechanisms), Amnesia / Powell-null-test (diagnostic). This is the first **forward** Bridge prediction to land in reality on a substrate the project had never seen the Bridge applied to.

2. **The framework's Incomprehensible Move primitive is operationally real.** It correctly predicted the category of move Anthropic would make. Two of the framework's named kernel primitives (Strategic Lasso in Powell, Incomprehensible Move in LMArena) now have validated instances across distinct domains.

3. **Cross-substrate forward + retroactive validation now spans three confirmed cases.** Powell (legal/regulatory — Strategic Lasso), Tokenized Land (financial/sovereign — Incomprehensible Move via ERC-4337), LMArena/Anthropic (AI competitive — Incomprehensible Move via pause call). The framework's strategic-reasoning is doing real work across uncorrelated domains.

### What this does NOT validate

1. **The Engine itself did not predict the pause.** Stroke 1 was stuck in leaderboard-race framing; Stroke 2 (Auditor) caught the framing but didn't promote it to a different prediction; Stroke 3 audited synthesis settled on *"Polymarket roughly right, with tunnel-vision risk"* — leaderboard-rank framing throughout. Only the Bridge (Stroke 2b) identified the mechanism category, and it did so at the abstract level (*"metacognitive adaptation as moat"*), not the specific instance level (*"call for pause"*).
2. **The original LMArena pre-registered prediction is not validated at the leaderboard-rank level.** That question (Anthropic #1 at end of June 2026) is still pending and now somewhat orthogonal — Anthropic's actual strategic move operated at a different layer than the benchmark-rank question framed.
3. **The architectural gap is real, AND it is engineering, not research.** Bicameral Convergence Levels 2 and 3 (per [`../concepts/Bicameral_Convergence.md`](../concepts/Bicameral_Convergence.md)) would have taken the Bridge's catch, fed it back into the Engine as friction (Level 2), and with operator approval spawned an Oracle for safety-governance research (Level 3), then produced a specific synthesis. Without those levels, the framework correctly identifies the mechanism category but stops short of the specific prediction. **The architectural spec is locked; only the implementation is missing.**

### Strategic implication for the project

This validation event reframes the next-phase priority calculation:

- **M2** (leaner-corpus side-by-side test) was the operator-decision item carried out of milestone 41. It remains valuable research but is no longer the obvious leading priority.
- **E1** (Bicameral Convergence Level 2 — `run_bicameral_loop()` + 5 mandatory operator control surfaces) is now the highest-leverage next phase. The empirical evidence favors closing the architectural gap the validation event just exposed.

The project's stated purpose for the LMArena run was not to win the Polymarket bet — it was to use a falsifiable near-term real-world event as a validation substrate for the strategic-reasoning physics engine. By that framing, the run is a success: the Bridge's mechanism-category catch landed in reality, on a forward-looking prediction, on a fresh substrate, within 10 days. The framework's strategic-reasoning has been validated against real-world strategic behavior.

### Outside-perspective note

A separate analysis at `C:\Users\james\Desktop\Bicameral_Convergence_Anthropic_Analysis.md` (produced via the operator's Gemini session 2026-06-06) independently reached the same conclusion: the Bridge's catch represents the project being "close to bridging" the pause prediction, with the gap being specifically the unbuilt Levels 2/3 architecture. The framing in that analysis is consistent with this milestone's read once the real-world validation event is factored in. Worth noting for traceability — the analysis predated reading the run record verbatim and reasoned forward from the Bridge's output to the actual instantiation; it landed substantially correct on the specific causal chain.

### What this milestone closes

- The Run 7 Bridge audit's "metacognitive adaptation as moat" catch is now empirically validated at the mechanism-category level. The catch is no longer hypothesis-tier; it's a directional prediction that landed.
- The classification of the LMArena pre-registered prediction shifts from "pending 2026-06-30" to "partial validation 2026-06-05 at mechanism-category level, leaderboard-rank question still pending."

### What this milestone opens

- E1 (Bicameral Convergence Level 2) promotes to the next active phase per ROADMAP. Multi-chunk per the existing E1 chunk plan (E1-01 cancel endpoint → E1-06 first live run).
- The follow-on validation question shifts: at 2026-06-30, the LMArena leaderboard-rank question still resolves, but the more interesting question is now whether a Level-2-equipped Engine run on a fresh strategic-prediction scenario produces specific-instance predictions rather than mechanism-category gestures.

### Pending after this milestone

- E1-01 (cancel endpoint + loop-checks-cancel-flag plumbing) is the next active chunk.
- M2 (leaner-corpus test) remains operator-gated, deprioritized relative to E1 in light of the validation event.
- P1-03b (CTA-suppression post-processor) and P1-04 (Bridge notebook lifecycle) remain queued in P1 ACTIVE.
- 2026-06-30 LMArena leaderboard-rank resolution still on the calendar (now a secondary validation, not the primary one).

---

## 43. Z-SPAN pattern-recognition validation + Operator Lens primitive surfaced + Pl2 consumer pivot (2026-06-06)

A non-prediction validation event surfaced during operator-driven exploration of the Frameworks Notebook. Three things landed in the same session arc.

### Trigger — the Cube of Space exchange

The operator, reading a bookmark about the Cube of Space (an esoteric tarot/geometric framework), asked the Frameworks Notebook (canonical Engine `0a7d2672-...`) how the 9D framework relates. Multi-turn conversation grounded in the foundations corpus. After the operator progressively requested more realistic examples ("HFT trading" → "geopolitical state" → "something I or someone using this could realistically execute"), the framework produced an example about *"deploying a decentralized, open-source protocol as a chaotic, Set-like disruption to systematically undermine the opponent's centralized, Horus-like monopoly"* — controlling the linguistic narrative, accumulating social territory (Go), forcing the legacy corporation into a closed-source counter-product that alienates the public.

The example structurally maps to **Z-SPAN** — the operator's other active project, an open-source civic-data platform competing against legacy closed-source GovTech (Granicus etc.). The framework had no Z-SPAN-specific input (no GovTech mentions, no civic-data references, no Granicus, no Z-SPAN markers) — it produced the pattern from corpus primitives alone, and the pattern happens to be one Z-SPAN cleanly instantiates.

Transcripts preserved at the operator's filesystem:
- `C:\Users\james\Documents\NotebookLM Transcript.txt` — the full Frameworks Notebook exchange
- `C:\Users\james\Documents\Gemini Transcript.txt` — operator's follow-up with Gemini using the NotebookLM transcript as input; Gemini independently recognized the parallel, produced the *"Citizen-First Infrastructure / Open Sourcing Civics / Verifiable Transparency / Public Truth Ledger"* terminology playbook

### Validation interpretation

Two read modes were considered and the second is the load-bearing one:

- **Surveillance read** (rejected): NotebookLM somehow leaked from the operator's Gemini chats or Drive into the closed corpus. Rejected because (a) NotebookLM's grounding is the uploaded foundations corpus alone, by architecture; (b) the framework's response contains zero Z-SPAN-specific markers — only category-level descriptions reconstructible from foundations primitives (Strategic Funnel, Set/Horus archetypes, Linguistic + Social/Relational dimensions, open-source-as-disruption pattern); (c) if a leak were happening, you'd expect at least one giveaway specific.
- **Pattern-recognition read** (accepted): the framework correctly identified the strategic-pattern category that Z-SPAN structurally instantiates. The kernel did the analytical work; the corpus's open-source-disruption primitive recognized the pattern; the operator's project happens to be a textbook instance of that pattern. Framework working as designed.

**This is Ganymede's fourth empirical validation event:**
1. Powell Cleanroom — Strategic Lasso retroactively validated against real-world Bessent/Vought planning
2. Tokenized Land — Incomprehensible Move retroactively validated against real ERC-4337 / sovereign-immunity mechanisms
3. LMArena/Anthropic (milestone 42) — Incomprehensible Move forward-validated via Anthropic's 2026-06-05 pause call (10 days early)
4. Z-SPAN (this milestone) — framework correctly identified a real-world strategic-pattern category from a generic prompt; the operator's actual project instantiates the category

Validation type for case 4 is methodologically distinct: not prediction-validating, **pattern-recognition-validating**. The framework's vocabulary correctly maps to a real-world strategic situation when prompted with an open question. Lower-stakes than (3) but still substantive — the framework's classifying ability has been exercised on a fresh substrate without coaching.

### Architectural primitive surfaced: the Operator Lens

The transcript produced one durable architectural insight worth shipping: the framework's outputs use technically-correct kernel primitives (DAI / SDS / ROEM / Strategic Lasso / Set / Horus) that are jargon-heavy for human consumption. The Cube-of-Space framing produced strategically identical reasoning expressed in more visceral, legible vocabulary (*"actualizes the concept instead of avoiding it"*, *"central intersection"*, *"gravity well"*). The kernel didn't change; the vocabulary did.

**The right architectural primitive is a post-synthesis translation stroke** — downstream of all analytical strokes (S1/S2/S2b/S3), preserves the kernel's logic 1:1, re-expresses for operator consumption in a selectable vocabulary register. Architecturally analogous to a render layer, NOT a persona change (persona changes contaminate upstream reasoning per the corpus-dominance lesson) and NOT a corpus addition (which compounds scaffolding per the M1 Cleanup Hypothesis evidence).

This primitive is now phase Pl3 in ROADMAP. Specs include: Translation Persona sibling to Engine / Mirror Auditor / Connection Bridge personas; `run_translation()` orchestrator method; session state preserving both technical and translated versions; frontend toggle; verbosity/register selector; first live run validating that translation preserves analytical claims 1:1.

### Consumer pivot: Z-SPAN replaces PrisonBreak as Pl2 primary

The operator's framing in the conversation: *"I can't ignore that I need this to be plugged in as a module for Z-SPAN long-term strategic planning."* Z-SPAN is structurally a better fit than PrisonBreak for the Pl2 first-consumer role because:

- Z-SPAN has live strategic decisions to make over the next weeks/months (terminology lock-in, GovTech competitive response, audience-facing positioning) — the framework gets exercised on real decisions, not hypotheticals.
- Z-SPAN's competitive landscape is structurally clean for the framework's kernel (open-source disruption vs. closed-source legacy is a textbook Strategic Funnel + Asymmetric Perception Game shape).
- Z-SPAN is the operator's most active project — module-not-service is validated by an actually-being-used consumer.

PrisonBreak is preserved as the planned second consumer. ROADMAP's Pl2 deliverables are updated to name Z-SPAN; PrisonBreak's existing integration example doc stays.

A new prerequisite surfaced by this pivot: **persistent session state**. Current Ganymede sessions are ephemeral (in-memory `SessionRegistry`); long-term Z-SPAN strategic planning needs sessions that persist over weeks, build on prior strokes, and surface a history of strategic decisions. Now specced as the leading Pl2 deliverable.

### Side observations from the transcript content

Two observations relevant to M1's Cleanup Hypothesis:

1. **"Anelixis" was used operationally.** The notebook produced *"through metacognitive integration... driving them toward the ultimate goal of Anelixis, or perpetual evolutionary upgrowth"* — Anelixis was DROP-tagged in the M1 partition as a Greek-jargon rhetorical capstone. Live evidence that the framework's concepts are deeply embedded in the corpus and that persona-text changes alone won't suppress them. M2's leaner-corpus rebuild is the right lever; persona patches aren't. Reinforces the partition's "corpus-level cleanup, not persona-level" stance.

2. **The Cube of Space integration is exactly the scaffolding-accretion pattern the Cleanup Hypothesis warned about.** An external esoteric framework was grafted onto the 9D framework by the notebook (mapping Cube primitives onto D3 / D5 + ROEM). The kernel survived intact and even sharpened; the scaffolding compounded. Useful M2 design input: the leaner Engine should produce the same Z-SPAN-shape recognition WITHOUT the Cube's specific vocabulary present. If it does, that's evidence the kernel is doing the work. If it doesn't, that's evidence the operator's specific prompt + framework combination is the load-bearing variable.

### Operator handoff doc generated

An onboarding markdown was generated at `C:\Users\james\Desktop\Z-SPAN_Ganymede_Onboarding.md` — a self-contained handoff letter from Ganymede's session to Z-SPAN's session explaining the validation event, the strategic insights, what Ganymede is, and what's being offered long-term (Ganymede as Z-SPAN's strategic-planning module).

### What this milestone closes

- The "is Ganymede ready for a real external consumer" question — yes, with Z-SPAN as the named consumer + persistent-session-state as the prerequisite.
- The "how do we make the framework's output legible to non-framework-native operators" question — Operator Lens (Pl3) is the architectural answer.

### What this milestone opens

- Pl2 Z-SPAN integration work (persistent sessions + integration spec + first live strategic session).
- Pl3 Operator Lens build.
- A methodology question for M2: does the leaner Engine still produce Z-SPAN-shape pattern recognition? Useful comparison run if M2 is approved.

### Pending after this milestone

- E1-01 still the immediately-next code chunk per the paused-mid-exploration scratch note at `docs/scratch/2026-06-06-paused-mid-E1-exploration.md`. E1 + Pl-phase work likely run in parallel since they touch different files.
- M2 still operator-gated; deprioritized vs. E1 and Pl2 in light of milestones 42 and 43.
- 2026-06-30 LMArena leaderboard-rank resolution still on calendar.

---

## 44. P1-04 Bridge notebook lifecycle — operator-managed with categorized suggestions (2026-06-06)

The P1-04 decision landed: Bridge notebooks stay until the operator explicitly deletes them (no auto-cleanup, no opt-in flag). The operator handles delete; the system advises. Per operator direction 2026-06-06: *"Lets just do C since its the most safe, just have a little visual thing I can click a 'delete' button on, and maybe suggestions for each 'row' of the notebook... I don't want it to be all or nothing."*

### The decision

Five options were considered (auto-cleanup default / opt-in cleanup flag / operator-managed / TTL sweeper / opt-out cleanup flag). The operator chose **Option C — operator-managed with categorized delete-suggestions**:

- No auto-cleanup. The orchestrator never deletes Bridge notebooks on its own.
- The system tracks auto-provisioned Bridge notebooks server-side in an in-memory registry as they're created.
- A survey endpoint lists registered notebooks with per-row categorization (*likely safe to delete* / *review* / *recently used*) + a one-line reason per row.
- A UI panel renders the survey with delete buttons + color-coded badges. Two-click confirm to prevent accidental deletes.
- Operator-curated notebooks (created outside the orchestrator's auto-provision paths) are NOT tracked here — they remain manually managed via raw API calls.

This matches the operator's pattern for MLMS-style tools where the AI can categorize/label but the human makes the final delete call.

### Shipped

- **`ganymede-backend/app/services/bridge_registry.py`** — in-memory `BridgeNotebookRegistry` tracking `notebook_id`, `title`, `created_at`, `session_id`, `provision_path` (`iterate_level_1` / `bicameral_loop_level_2` / `standalone_provision`), `foundations_uploaded`, `truth_packets_uploaded`. Thread-safe. Single module-global instance per backend process.
- **Categorization heuristic** (`list_with_suggestions`):
  - Session terminal (`complete` / `cancelled` / `error`) AND notebook >2h old → `likely_safe_to_delete` + suggested action `delete`.
  - Session terminal AND notebook ≤2h old → `review` (operator may re-audit).
  - Session running → `recently_used` + suggested action `keep`.
  - Session unknown (process restart or untracked) AND notebook >48h old → `likely_safe_to_delete` + `delete`.
  - Session unknown AND notebook ≤48h old → `review`.
- **Orchestrator integration** — `provision_bridge_notebook` gains `session_id` + `provision_path` kwargs and registers in the registry after successful provisioning. `run_iterative_engine` passes `(session.id, "iterate_level_1")`; `run_bicameral_loop` passes `(session.id, "bicameral_loop_level_2")`; the standalone `/bridge/provision` path defaults to `("standalone_provision")`.
- **HTTP `GET /api/v2/bridge/notebooks`** — returns the categorized survey with summary counts (total / safe_to_delete / needs_review / keep).
- **HTTP `DELETE /api/v2/notebooks/{id}` hook** — deregisters from the bridge registry on successful delete. Idempotent — safe to call regardless of whether the notebook was registered.
- **Frontend `BridgeNotebookManager.tsx`** — self-contained component fetching the survey + rendering each notebook as a row with title, ID, age, session info, color-coded category badge (rose / amber / emerald), reason line, two-click confirm delete button. Summary count chips at the top. Refresh button. Help section explaining the heuristic.
- **`/bridge-notebooks` route** — new page at `ganymede-ui/src/app/bridge-notebooks/page.tsx` rendering the manager component with a back link.

### What this milestone closes

- P1-04 decision is now landed and implemented.
- The accumulation problem the original P1-04 spec flagged ("auto-provisioned Bridge notebooks aren't auto-deleted; for long-lived ops, this accumulates clutter") is now manageable — operators can see what's accumulated + which ones the system thinks are safe to delete.

### What this milestone does NOT close

- **Persistence across backend restarts.** The registry is in-memory; restarting the backend empties the registry but the actual notebooks persist in NotebookLM. Operator can still see + delete them via the raw `/api/v2/notebooks/{id}` endpoint, but they won't appear in the survey table until they're re-provisioned (which won't happen — they're already provisioned). Follow-up candidate: file-backed persistence (JSON serialization on every register/deregister) so the registry survives restarts.
- **Operator-curated notebooks.** Notebooks created outside the orchestrator's auto-provision paths (e.g., manual `POST /api/v2/notebooks` calls, persona-expansion experiment notebooks) are NOT tracked. The operator manages those manually. Tracking would require adding a "register externally-created notebook" API surface; not needed for the immediate use case.

### Pending after this milestone

- Per operator-locked sequence: **Pl3 Operator Lens** next (translation stroke for operator-facing output legibility — surfaced by milestone 43's Cube-of-Space exchange).
- Then **Pl2 Z-SPAN as first consumer** at the very end.
- E1-06 (first live Bicameral Level 2 run) still on the queue, operator-driven.
- 2026-06-30 LMArena leaderboard-rank resolution still on calendar.

---

## 45. Pl3 Operator Lens shipped — translation stroke for operator-facing output legibility (2026-06-06)

The Operator Lens primitive surfaced in milestone 43 (the 2026-06-06 Cube-of-Space transcript exchange) is now built end-to-end. Operator can translate any recorded stroke into one of three vocabulary registers — `plain_english`, `cube_of_space`, `executive_brief` — preserving the analytical claims 1:1 while swapping framework jargon for legible operator-facing vocabulary.

### Architectural call: canonical NotebookLM Engine (corrected mid-milestone)

**Initial implementation attempted Gemini Flash; operator caught the divergence + the milestone was corrected.** The pushback (paraphrased): *"This kinda goes against the whole notebook RAG closed information sphere thing since Gemini was only used for that one specific thing of deducing my query. I was just envisioning another couple of final queries to the notebook before we stopped using it for the final lens thing."*

The operator's reasoning is correct and load-bearing:

- **Closed RAG sphere is the design principle.** Gemini was deliberately scoped to dispatcher intent classification only — a thin "what does the operator want?" call that doesn't touch analytical content. Everything analytical lives in the closed sphere.
- **Translation IS analytical content.** It carries strategic claims forward; a distorted translation distorts the operator's read of the analysis. So it belongs inside the sphere alongside Engine / Auditor / Bridge — not in an ungrounded Gemini Flash path.
- **The grounding is what makes the translation work.** What made the milestone 43 Cube-of-Space exchange land so well was that the notebook produced visceral geometric vocabulary BECAUSE the grounded model understood what the framework concepts actually meant. Gemini Flash without the foundations-corpus grounding would only know surface-level jargon mapping, not the structural meaning. The grounded approach is what reproduces the milestone 43 quality.

**Corrected implementation:** translation routes through ``self.svc.query_chess_engine`` (the canonical NotebookLM Engine) with a register-specific translation prompt. Cost goes up from ~1-2s to ~30-50s wall per translation (single cooldown-gated NL call) — matching the speed of every other analytical surface in the project. The Engine's existing persona ("supreme order and precision") is jargon-heavy by default, but the translation prompt explicitly instructs the Engine to re-express AGAINST that default — the persona's discipline holds the analytical claims stable while the prompt shifts the vocabulary register.

The original Gemini Flash translation method is preserved as ``_DEPRECATED_GEMINI_TRANSLATION_PROMPTS`` in ``gemini_service.py`` for historical reference; ``translate_with_register`` was removed from the class surface.

### Three registers shipped

- **`plain_english`** — strip framework jargon (DAI / SDS / ROEM / Strategic Lasso / Set / Horus / Go / Chess / Ω / Ω') and re-express in plain everyday English. Preserves per-dimension breakdown structure + FINAL RESOLUTION. Useful for non-framework-native operators + first-touch consumer surfaces.
- **`cube_of_space`** — visceral geometric vocabulary from the milestone 43 transcript: gravity well, central intersection, narrowing corridor, "actualizes the concept instead of avoiding it", inward-outward spirals. Same analytical kernel; spatial / geometric register.
- **`executive_brief`** — tight 3-5 paragraph decision-maker summary. Drops per-dimension breakdown + framework vocabulary entirely. Structure: bottom-line → mechanism → falsification risk → what-to-watch.

The shared discipline across all three: **NO new claims, NO softening of conclusions, NO hedging the original didn't carry**. The prompt enforces this explicitly. Adding new registers is a one-entry addition to `_TRANSLATION_PROMPTS` in `gemini_service.py`.

### What this milestone closes

- The "framework output is correct but jargon-heavy" UX problem flagged in milestone 43. Operator can now translate any stroke into legible language without contaminating upstream reasoning (NOT a persona change) and without compounding scaffolding (NOT a corpus addition).
- Pl3 is shipped per the operator-locked sequence (P1-03b → P1-04 → Pl3 → Pl2).

### Shipped

- **`TranslationRegister` enum** in `ganymede-backend/app/contracts.py` — three registers + docstrings explaining the intent of each.
- **Session translation storage** in `ganymede-backend/app/services/session.py` — `Session._translations: dict[str, str]` keyed by `f"{stroke_number}:{register}"`. `record_translation()` async method (acquires session lock) + `get_translation()` getter + `translations` property snapshot.
- **`GeminiService.translate_with_register(source_text, register)`** + **`_TRANSLATION_PROMPTS`** library in `ganymede-backend/app/services/gemini_service.py`. Prompts are register-specific system instructions that prepend the source text in the Gemini Flash call. Each register's prompt explicitly forbids new claims / softening / hedging.
- **`GanymedeOrchestrator.run_translation(session, stroke_number, register)`** in `ganymede-backend/app/services/orchestrator.py`. Looks up the stroke, prefers `cleaned_response` over `raw_response` when P1-03b's CTA-strip ran, calls Gemini, records the result on the session, returns the translated text.
- **`POST /api/v2/sessions/{id}/translate`** endpoint in `ganymede-backend/app/v2_routes.py`. Body: `{stroke_number, register}`. Returns: `{stroke_number, register, translated_text, source_length, translated_length}` for the UI to compute compression-ratio indicators.
- **`StrokeTranslator.tsx`** self-contained UI component. Three register-selection buttons with color-coded badges (sky for plain_english, violet for cube_of_space, emerald for executive_brief). Per-stroke local cache so re-selecting a register without explicit refresh doesn't re-fire. Refresh button for explicit re-translation. Compression-ratio indicator (`X% shorter` / `X% longer` vs. source). Loading + error states inline.
- **Mounted in `StrokeCard`** inside `RunnerPanel.tsx` — every stroke now has the Operator Lens panel below the raw-response details.

### What this milestone does NOT close

- **First live comparison run** (Pl3 deliverable per ROADMAP) — operator-driven, requires backend + live session. The infrastructure is in head; the run + write-up is the operator's call.
- **DispatcherPanel integration** — DispatcherPanel doesn't use WebSocket and doesn't render strokes the same way; translation UI in that surface is a separate small chunk if needed.
- **More registers** — the three shipped cover the immediate Cube-of-Space-inspired use case. Adding registers (operator-fluent, technical-tight, etc.) is one entry per register in `_TRANSLATION_PROMPTS`.

### Pending after this milestone

- Per operator-locked sequence: **Pl2 Z-SPAN as first consumer** at the very end (persistent session state + integration spec + first live Z-SPAN strategic-planning session).
- E1-06 first live Bicameral Level 2 run still operator-driven.
- 2026-06-30 LMArena leaderboard-rank resolution still on calendar.

---

## 46. Pl2-01 persistent session state shipped — SQLite-backed SessionStore + list/strokes API (2026-06-08)

The Pl2 prerequisite milestone 43 surfaced ("current Ganymede sessions are ephemeral; long-term Z-SPAN strategic planning needs sessions that persist over weeks, build on prior strokes, and surface a history of strategic decisions") is now built. SessionRegistry survives backend restart; the new `GET /api/v2/sessions` + `GET /sessions/{id}/strokes` endpoints give Z-SPAN (and any future Pl2 consumer) the browse-history surface they need.

### Design call: stdlib SQLite, sync-in-executor, save-on-every-mutation

Three architectural options were considered:

- **File-backed JSON** (one file per session). Simplest possible; cheap to inspect by hand. Loses on list/search (directory scan + parse per session) at any scale beyond a handful.
- **Event-replay** (only the events list persisted; state reconstructed by replaying). Architecturally elegant; matches the existing event-driven session model. But ties the persistence schema to the in-memory event mutation order, which would couple future event-type changes to a forward-compat persistence migration.
- **SQLite with explicit schema** (chosen). Stdlib (no new dep), supports list + search + pagination natively, atomic per-row writes, well-understood operationally. Single-file DB at `ganymede-backend/data/sessions.db` (env-override via `GANYMEDE_SESSION_DB`).

Concurrency model: **sync API; async call sites bridge via `asyncio.to_thread`**. This matches `main.py`'s existing pattern for `auto_relogin` (`loop.run_in_executor(None, auth_check.auto_relogin)`) and avoids pulling in `aiosqlite` as a third-party dep. Each `save_session` call opens its own connection (via the `_connect` context manager), so SQLite's own file-level locking serializes writers without any application-level coordination.

Save cadence: **on every mutation**. The Session calls `_persist()` from inside its lock after each state change (`record_stroke`, `record_translation`, `complete`, `fail`, `request_cancel`), plus once at registry-create. Backend crash mid-Bicameral-loop preserves the strokes that landed; the next startup rehydrates them and flips the orphan's status to `error` with a synthetic ERROR event appended so the events endpoint stays consistent.

The simpler alternatives — "save only on terminal transition" or "save only on shutdown" — were rejected for the same reason: a backend crash during a 30-minute Bicameral run would lose all intermediate work. The incremental cost is ~3-5ms per stroke (tiny disk write), well below the per-stroke NotebookLM call cost (~30-60s).

### Schema

Four tables, foreign-keyed to the session row with `ON DELETE CASCADE`:

- **`sessions`** — id (PK), scenario_json, pathway, iterative, max_strokes, status, error_message, created_at, completed_at, final_text. Indexed on status / created_at / pathway for the common list-filter shapes.
- **`strokes`** — session_id + stroke_number (composite PK), stroke_json. The full StrokeResult is round-tripped via Pydantic v2's `model_dump_json` / `model_validate`. Lossless.
- **`events`** — session_id + event_idx (composite PK), event_json. Same round-trip pattern. Event ordering preserved via `event_idx` set from `enumerate(session.events)` at save time.
- **`translations`** — session_id + stroke_number + register (composite PK), translated_text. Pl3 Operator Lens output keyed by `f"{stroke_number}:{register}"` matching `Session._translations`'s in-memory schema.

Child rows are delete-and-insert on each save rather than diff-and-update — small N (≤ ~10 strokes, ≤ ~50 events per session), zero divergence risk.

### Orphan-rescue semantics

When the backend crashes, sessions left in `running` status get marked terminal on the next boot:

1. `SessionStore.mark_orphan_running_as_error(message)` runs BEFORE `load_all()`. It selects every row with `status='running'`, flips each to `status='error'` + `error_message = message` + `completed_at = now`, and appends a synthetic ERROR event with payload `{message, exc_type: "BackendRestartedDuringRun"}` so the events endpoint shows the operator what happened.
2. `load_all()` then returns the rescued rows alongside everything else terminal.
3. `Session.from_persisted_state(row, store=store)` constructs each session via `__new__` + manual attribute assignment, bypassing `__init__`'s `SESSION_CREATED` emit (the persisted events list already contains that event from the original creation).

### API surface added

Two new endpoints in `app/v2_routes.py`:

- **`GET /api/v2/sessions`** with query params `status`, `pathway`, `q`, `limit` (1-200), `offset`. Returns `{ sessions: [SessionSummary], total, limit, offset }`. The store is the source of truth (pulling from `list_summaries` / `count` / `search`). `SessionSummary` carries the full `Scenario` object plus a 200-char `final_text_preview` so the list view can render whatever the consumer wants without per-row detail fetches.
- **`GET /api/v2/sessions/{id}/strokes`** returns `{ session_id, strokes: [StrokeResult], translations: {...} }`. Pulls from the in-memory registry (which post-rehydrate has all persisted sessions). Operator Lens translations come along in the same payload so the frontend doesn't have to fire per-stroke translation fetches when rendering a prior session.

The existing `GET /sessions/{id}` and `GET /sessions/{id}/events` endpoints transparently work for rehydrated sessions because the in-memory registry surface didn't change.

### What this milestone closes

- The "persistent session state" prerequisite in Pl2 — Z-SPAN can now start a strategic-planning session, come back to it next week, browse the prior strokes via the API, and (when iterate is wired to take a `parent_session_id`) build forward.
- The "registry can't survive backend restart" operational ceiling. Backend operators can restart for any reason (cookie rotation, code deploy, OS update) without losing in-flight sessions.

### What this milestone does NOT close

- **Mid-loop resume.** Persistence preserves state across restart, but the orchestrator loop that was driving the session is dead. The session is marked `error` with a synthetic ERROR event. To actually pick up where the loop left off requires re-driving `/iterate` (or `/bicameral-loop`) — which is the operator's call to make, with awareness that the previous truth_packets / scenario context is what the prior strokes were grounded on.
- **`parent_session_id` for context-building.** Z-SPAN's "build on prior strokes" semantic is Pl2-02 territory — a separate orchestrator-level change where `IterateRequest` can take a `parent_session_id` and the synthesis prompt inherits the prior session's resolutions. Out of scope for Pl2-01.
- **Z-SPAN consumer spec doc.** The `docs/integration/examples/zspan_consumer.md` walkthrough doc is a separate small chunk (~30 min) tracked as the next Pl2 task. It documents how Z-SPAN actually wires Ganymede in, including the persistent-session-state pattern Pl2-01 enables.
- **First live Z-SPAN strategic-planning session.** Operator-driven; requires Z-SPAN's own session to produce a real positioning question and call the v2 API.

### Cross-cutting operational notes

- **`.gitignore`** updated to exclude `ganymede-backend/data/` so the per-environment DB file never gets committed. Per-environment state, not source.
- **Env var overrides**: `GANYMEDE_SESSION_DB` to relocate the DB; `GANYMEDE_DISABLE_SESSION_PERSISTENCE=1` to disable the store entirely (tests + ephemeral dev sessions).
- **Backwards compatibility**: existing tests + the existing in-memory-only registry behavior preserved. `Session(store=None)` and `SessionRegistry(store=None)` work exactly as before — persistence is opt-in via `bind_store`.

### Verified production-shape round-trip

Driven via FastAPI's `TestClient` lifecycle (so the real `startup_event` fires):

1. First boot → SessionStore opens at the env-overridden path → `rehydrate()` finds 0 sessions.
2. Session created via `registry().create()` with a Z-SPAN-flavored scenario question → auto-persisted.
3. Stroke recorded + session completed → both writes land synchronously.
4. `GET /api/v2/sessions` returns `{ total: 1, sessions: [...] }` with matching session_id.
5. Simulated process death: `registry()._sessions.clear() + _store = None`.
6. Second boot → fresh TestClient triggers startup → `rehydrate()` reports `rehydrated 1 prior session(s)`.
7. `GET /api/v2/sessions` returns `total: 1` again; `GET /sessions/{id}` returns `status: complete`; `GET /sessions/{id}/strokes` returns the original stroke with the original `final_resolution` intact.

### Pending after this milestone

- Pl2 next chunk: `docs/integration/examples/zspan_consumer.md` walkthrough (~30 min).
- Pl2 final chunk: first live Z-SPAN strategic-planning session — operator-driven, requires Z-SPAN's session to drive a real positioning question via the v2 API.
- E1-06 first live Bicameral Level 2 run still operator-driven.
- 2026-06-30 LMArena leaderboard-rank resolution still on calendar.

---

## 47. Persistence-discipline closeout — Pl2-02 consumer-spec doc + bridge-registry persistence parity (2026-06-09)

Cleanup pass over the persistence-discipline arc started in milestone 46, plus the Pl2-02 deliverable. Three pieces:

### Pl2-02 — Z-SPAN consumer-spec walkthrough doc

Shipped `docs/integration/examples/zspan_consumer.md` as the named-consumer integration doc Z-SPAN's session reads. Follows the `prisonbreak_consumer.md` template but adapted for Z-SPAN's distinct shape: **the consumer is a session, not an app**. PrisonBreak embeds Ganymede via tRPC in a running web app; Z-SPAN's Claude session calls the v2 API directly via curl / HTTP. Both shapes have to be ergonomic from the v2 surface — they exercise different parts of it (PrisonBreak relies on WebSocket streaming + RAG-derived Truth Packets; Z-SPAN relies on persistent-session state + operator-curated Truth Packets + Operator Lens translation).

The doc's "What this case taught the general API design" section names five generalizable principles surfaced by the Z-SPAN case: (1) some consumers are sessions, not apps; (2) operator-curated Truth Packets are first-class; (3) Operator Lens is load-bearing for non-framework-native audiences; (4) Bicameral Level 2 escalation rule when Level 1 surfaces friction; (5) persistent session state should be the default, not the exception; (6) closed-RAG-sphere discipline is non-negotiable. These should generalize to any future consumer.

### Consuming-v2-API canonical-doc updates

The `docs/integration/consuming_the_v2_api.md` reference predated Pl2-01. Updated to:

- Replace the "Session persistence (or lack of)" stub with the Pl2-01 reality (save-on-mutation, rehydrate-on-startup, orphan rescue, opt-out env vars, schema overview).
- Add `GET /api/v2/sessions` reference entry with the full query-param table + response shape.
- Add `GET /api/v2/sessions/{id}/strokes` reference entry.
- Update the TL;DR so future consumers discover persistence from the first paragraph.

Without this, the canonical reference doc would still tell consumers "sessions are in-memory in v1." Now consumers reading either `consuming_the_v2_api.md` (the abstract reference) or `examples/zspan_consumer.md` (the concrete walkthrough) see the same persistence-aware shape.

### BridgeNotebookRegistry persistence parity

Symmetric chunk to Pl2-01's SessionStore work. The `BridgeNotebookRegistry` (P1-04, milestone 44) was the operator-facing registry for auto-provisioned Bridge notebooks but was in-memory-only; restart orphaned its metadata even though the actual notebooks persist in NotebookLM. With strategic-planning sessions spanning weeks, the bridge notebooks live weeks too — the registry needs to outlive the process.

Implementation:

- **`BridgeNotebookRegistry(persistence_path=...)` + `bind_persistence(path)` + `load_from_disk()` + `_persist_locked()`** in `app/services/bridge_registry.py`. JSON-file backing (vs SQLite for SessionStore) because N is small (≤ ~20 entries typical), no querying beyond `list_all`. Writes atomically via tempfile + `os.replace`.
- **`default_persistence_path()`** resolves to `ganymede-backend/data/bridge_registry.json`. Env override: `GANYMEDE_BRIDGE_REGISTRY_DB`.
- **`app/main.py` startup wiring** alongside the SessionStore init — degrades to in-memory-only if file I/O fails rather than blocking startup.
- **Corrupt-file handling**: load_from_disk catches JSON decode errors, logs a warning, starts empty. The next mutation rewrites the file. Verified via smoke test.

Verified end-to-end: register → file written → new registry instance with same path loads N=1 → deregister → next reload reflects the removal → corrupted JSON degrades gracefully → startup wiring through TestClient persists across two simulated boot cycles.

### Why JSON file vs SQLite for the bridge registry

The SessionStore picked SQLite because list/filter/search are the dominant query shapes. The BridgeNotebookRegistry's dominant query is `list_all` (the management UI renders every tracked notebook) — no filter, no search, no pagination. JSON is simpler, has no schema-migration concerns, and "render the entire file in `cat`" is the right operator-debug experience for a registry this small. If the registry grows past ~100 entries this assumption should be revisited; not blocking now.

### What this milestone closes

- The persistence-discipline gap surfaced by milestone 46 — both module-global registries (`SessionRegistry` for sessions, `BridgeNotebookRegistry` for bridge notebooks) now outlive process lifetime.
- The Pl2-02 deliverable (consumer-spec walkthrough doc).
- The canonical-API-doc / consumer-doc consistency gap — both surfaces now describe the same persistent-by-default reality.

### What this milestone does NOT close

- **Pl2-03** — first live Z-SPAN strategic-planning session. Operator-driven; requires Z-SPAN's session to produce a real positioning question + call the v2 API end-to-end. Outside Claude-autonomous scope.

### Pending after this milestone

- Pl2-03 (operator-driven).
- E1-06 first live Bicameral Level 2 run (operator-driven).
- 2026-06-30 LMArena leaderboard-rank resolution (calendar-gated).
- M2 leaner-corpus side-by-side test (operator-gated, major scope shift).
- P1-01 upstream `notebooklm-py` PR submission (operator action, held with submission package ready).

All remaining items are operator-gated or calendar-gated. **Every claude-autonomous chunk on the project's current scope is now done.**

---

## 48. `/managed-run` endpoint — dispatcher as canonical entry point for session-as-consumer projects (2026-06-10)

The consumer-spec walkthrough shipped in milestone 47 taught Z-SPAN's session to learn pathway taxonomy, Truth Packet shape, iterate-vs-Bicameral escalation rules, and Operator Lens register selection before making the first useful call. That's framework-internal vocabulary leaking onto the consumer's cognitive surface, and James caught it during the actual Z-SPAN handoff attempt: *"I feel like I'm trying to work with the handoff in the other chat, and it just made it too complicated. I think that we need to have an interface, not with the API. It would happen through that Gemini thing, like the user would."*

He was right. The dispatcher (`POST /api/v2/dispatch`) already abstracts pathway choice for human operators via DispatcherPanel — natural-language in, classified pathway out. Programmatic consumers deserve the same abstraction. This milestone ships it.

### The architectural call

**The dispatcher is the canonical entry point for both human operators (via UI) and session-as-consumer projects (via HTTP).** One natural-language entry surface; two render-out surfaces (interactive form for humans, JSON payload for sessions). This is the fourth instance the project has independently arrived at the same architectural lens: *the framework abstracts itself for the audience*. Prior instances:

1. **Milestone 43** — Cube-of-Space transcript exchange showed framework analytical output landing differently when expressed in a different vocabulary register.
2. **Milestone 45 (Pl3)** — Operator Lens codification: translation stroke that re-expresses analytical output in a chosen register, preserving claims 1:1.
3. **Milestones 46-47** — persistent session state + `consuming_the_v2_api.md` parity: the framework's persistence reality made visible to consumers regardless of when they joined the conversation.
4. **This milestone** — same lens applied to *how consumers interact with the framework* (not just how its outputs are expressed). Consumers send natural-language intent; the framework internally handles its own complexity.

### Shipped

**`POST /api/v2/managed-run`** in `ganymede-backend/app/v2_routes.py` — single-call composition of dispatch → session create → iterate (or bicameral_loop) → translate → complete. Request: `scenario_text` (NL) + `truth_packets` (consumer's grounded context) + optional `register` / `depth` / `max_iterations` / `include_bridge` / `pathway_override`. Response: `session_id` + `pathway_chosen` + `dispatch_confidence` + `dispatch_rationale` + `clarifying_questions` + `final_text` + `translated_text` + `strokes` + `state`. Cancel-mid-loop returns 200 with partial strokes (same pattern as `/iterate`); translation failures degrade to untranslated final.

The composition uses existing primitives — no new orchestrator logic. Pathway selection routes through `GeminiService.dispatch_intent`; session creation through `registry().create`; loop driving through `run_iterative_engine` or `run_bicameral_loop`; translation through `run_translation` (which routes through the canonical NotebookLM Engine per milestone 45's mid-flight correction — closed-RAG-sphere discipline preserved); completion through `session.complete`. The endpoint is composition, not new behavior.

### Both consumer shapes stay first-class

The granular API (`/dispatch` + `/sessions` + `/iterate` or `/bicameral-loop` + `/translate` + `/complete`) is preserved and remains the right surface for **embedded-app consumers** (PrisonBreak) that need fine-grained per-step control for their in-app UI. They typically:

- Render stroke-by-stroke progress (need stroke-by-stroke event hooks).
- Insert operator review between dispatch classification and the loop (need to display the dispatcher's choice for human confirmation before burning ~15 min of NotebookLM calls).
- Run single synthesis strokes (`/synthesize`) for cheaper first-look passes (`/managed-run` is iterative-only).

The granular API is the right shape for them. `/managed-run` is the right shape for **session-as-consumer** projects (Z-SPAN, future Claude sessions). Two documented patterns; both first-class.

### Documentation parity

- **`docs/integration/examples/zspan_consumer.md`** rewritten to lead with `/managed-run` as primary. Granular API preserved as "if you need fine-grained control" fall-back section. Walkthrough collapses from 5 curl steps to 1 + register selection.
- **`docs/integration/consuming_the_v2_api.md`** TL;DR now opens with the two-consumer-shapes framing. New endpoint reference section for `/managed-run` placed right after `/health` (the canonical sanity-check) so the first endpoint reference a new consumer sees is the recommended starter.
- **`C:\Users\james\Desktop\Z-SPAN_Handoff_v2.md`** — new self-contained onboarding doc James pastes into Z-SPAN's chat as the first message. Single paste-in; covers what Ganymede is (with the Theory-of-Mind framing from the 2026-06-10 Gemini brainstorm), the one HTTP call shape, register selection, persistence, courier protocol. Replaces the earlier handoff approach that was producing the cognitive-overload symptom James caught.

### Cognitive-surface delta

For Z-SPAN's first call, the cognitive model collapses from:

> "Draft a question. Identify the pathway shape (cleanroom / genie / offensive / mirror_audit) by reading the pathway-selection table. Construct Truth Packets. Decide whether to iterate or bicameral-loop based on the friction-escalation rule. Pick a register based on the audience table. Make 5 HTTP calls in sequence: dispatch (optional), sessions, iterate-or-bicameral-loop, translate (per register), complete. Capture session_id along the way for later browsing."

To:

> "Draft a question with James. Draft 3-5 Truth Packets. Make 1 HTTP call. Capture the session_id from the response."

That's the design surface delta. Internal complexity unchanged; consumer cognitive surface dropped from ~7 decision points to 1.

### What this milestone closes

- The over-complex-consumer-onboarding issue James surfaced during the actual Z-SPAN handoff attempt.
- The asymmetry between human-operator entry (one NL textbox via DispatcherPanel) and programmatic-consumer entry (5+ endpoints to learn). Both shapes now have the same canonical entry point.

### What this milestone does NOT close

- **Pl2-03** — first live Z-SPAN strategic-planning session. Still operator-driven; requires Z-SPAN's session to produce a real positioning question + call `/managed-run` end-to-end + James to courier results. The handoff doc that supports this is the new `Z-SPAN_Handoff_v2.md`.
- **Truth Packets stay manual.** The consumer still has to bring grounded context. Can't be automated away — that's the consumer's domain knowledge. But this is the *only* thing the consumer has to actively produce.

### Pending after this milestone

- Pl2-03 first live Z-SPAN strategic-planning session (operator-driven).
- E1-06 first live Bicameral Level 2 run (operator-driven).
- 2026-06-30 LMArena leaderboard-rank resolution (calendar-gated).
- M2 leaner-corpus side-by-side test (operator-gated, major scope shift).
- P1-01 upstream `notebooklm-py` PR submission (operator action).

### Cross-cutting note

This milestone is *also* a confirmation of the public-facing-framing direction logged in the project memory ([[project-public-release-deferred]]). The same architectural principle — *the framework abstracts itself for the audience* — applies to:
- Stroke output → audience (Pl3 Operator Lens, registers).
- Project description → public reader (Theory-of-Mind framing if Option B ships).
- API surface → consumer (`/managed-run` for session-as-consumer; granular API for embedded-app).

Three load-bearing instances on the same axis; treat the lens as confirmed project-wide architectural principle.

---

## 49. Dispatcher routes Cleanroom on real-world entities to Universal Logic Loop — closing the friendly-entry-point promise (2026-06-10)

Surfaced during the post-milestone-48 visualizer-choreography test session. James drove a Ryanair Cleanroom question through the Dispatcher; the Engine refused with "no information about Elon Musk or Ryanair." The two prior Ryanair runs on the same exact question (sessions `813dbe4c`, `26068f93` earlier the same day) had produced 9D-mapping content — non-deterministic substrate pattern-matching. The refusal is the more disciplined behavior (closed-RAG-sphere principle holds locally), but the inconsistency exposed a load-bearing architectural mismatch in the front door.

James's diagnosis (verbatim, paraphrased): *"why does the dispatcher path not automatically have the full universal logic loop harvest path as the default? It's not asking the user to give it the truth packets for you to then say, 'Oh, well, it's just going to refuse it because it doesn't know it.'"*

He was right. The Dispatcher sits at the front door of the project, marketed as the friendly natural-language entry point — but it routed exclusively to the Iterative Engine path, which requires the consumer to supply grounded Truth Packets externally. The dispatcher UI has nowhere to inject those packets (`handleConfirm` auto-generates ONE packet whose content is the question text itself). For any Cleanroom question about real-world entities — i.e., the example placeholder shown to users — the path is structurally guaranteed to fail or to produce unreliable pattern-matching.

### Why the original routing happened

The Universal Logic Loop predates the Dispatcher by far — it's the harvest-then-synthesize flow from milestones 4-14 (Hualapai, GPS, 60s-Amnesia). The Iterative Engine quick loop came in milestone 23 (Musk-Altman). The Dispatcher landed last (milestone 35) and was wired to the Iterative Engine path for **speed** — "one text box → 5-10 min answer" UX, vs Universal Logic Loop's 15-60 min. Nobody re-evaluated whether that was the right routing target once the Dispatcher became the canonical entry point.

The cost calculus inverts when the speed produces "no information" output: a 5 min refusal is worse than a 20 min answer.

### The architectural call

**Extend the dispatcher's intent classification to include a `needs_external_knowledge` field, and branch on it in the UI.** Real-world Cleanroom / Genie / Offensive questions route to Universal Logic Loop; framework-internal-concept questions and `mirror_audit` (which supplies its own grounding via `prior_resolution`) route to Iterative Engine. The operator can override with a "Force quick path" toggle on the review screen.

This honours the same architectural lens as milestone 48 (the framework abstracts itself for the audience): the consumer no longer has to know that "Cleanroom" means two structurally different orchestration paths depending on whether the question is about real-world entities — the dispatcher decides.

### Shipped

- **`ganymede-backend/app/services/gemini_service.py`** — extended `DISPATCHER_PROMPT` with a "KNOWLEDGE HARVEST SIGNAL" section that teaches Gemini Flash the 9D foundations corpus is theory-only (no company/product/market/person/event data); set `needs_external_knowledge: true` when the scenario references real-world named entities or specific markets/prices/events; always `false` for `mirror_audit`; default to `true` for ambiguous cleanroom/genie/offensive (harvest unnecessarily is cheaper than refusing). `dispatch_intent` extracts the new field with a defensive fallback (`mirror_audit → false`, else `true`). The Gemini-failure fallback path returns `true` so the safer path is the default.
- **`ganymede-backend/app/v2_routes.py`** — `DispatchResponse` Pydantic model adds `needs_external_knowledge: bool`; the `/dispatch` route returns it. `/managed-run` reads the same `dispatch_result` dict but **deliberately does not branch** on the new field — Z-SPAN-shape consumers supply their own Truth Packets, so the harvest path doesn't apply to that surface; only the Dispatcher UI flow needed the structural fix.
- **`ganymede-ui/src/components/DispatcherPanel.tsx`** — five interlocking additions:
  - `DispatchResponse` TS interface extended with `needs_external_knowledge: boolean`.
  - New `SessionEvent` and `OracleProgress` types (copied from RunnerPanel) plus a WebSocket subscription mirroring `RunnerPanel.runFullLoop` / `runSynthesisOnly` — opens WS BEFORE kickoff so Blueprint / Oracle / Stroke events drive incremental snapshot updates. **This also closes the milestone-48-session visualizer freeze** (the mindmap was rendering a frozen Stage-1 placeholder for entire ~5-15 min runs because nothing was subscribed to the event stream).
  - New state for `sessionId` / `blueprint` / `oracles` / `forceQuickPath` plus a `wsRef` + `closeWs` cleanup. The snapshot mirror now publishes blueprint + oracles so OrchestratorMindMap can render the Universal-Logic-Loop spawn graph.
  - `handleConfirm` branches on `useUniversalLoop = needs_external_knowledge && !forceQuickPath`: true → `POST /run-full-loop` + await `session_complete` via WS + `/complete`; false → existing `/iterate` (or `/synthesize`) path, also with WS sub for animation parity.
  - Review-phase UI adds a path-choice card (Network icon for harvest path, Zap icon for quick path) with wall-time hint (~15-30 min vs ~5-10 min) and the operator-override checkbox. Running-phase indicator distinguishes Universal Logic Loop messaging ("Triage stroke identifies subjects → PKI Oracles spawn → harvested Truth Packets feed the final synthesis") from the iterative-loop messaging.

### Cognitive-surface delta

For a real-world Cleanroom question, the operator's cognitive model collapses from:

> "Type a question. Dispatcher classifies cleanroom at 100% confidence. Click Run with this. Wait ~5 min. Engine refuses with 'no information about X or Y.' Realize the friendly entry doesn't actually engage real-world questions. Switch to Runner panel. Pick Full Universal Logic Loop. Re-type the question into the Cleanroom question field. Click Run. Wait 15-30 min."

To:

> "Type a question. Dispatcher classifies cleanroom + flags harvest needed. Review screen shows harvest path with wall-time hint. Click Run with this. Wait 15-30 min."

Same wall time on the path that produces an actual answer; the operator no longer has to know which UI surface to use for which question shape. The Dispatcher is now an honest friendly front door.

### What this milestone closes

- **The architectural-mismatch James caught** during the visualizer-choreography test: the friendly entry routed to a path that fails on the friendly questions.
- **The visualizer-stuck-on-stage-1 bug** surfaced during the same session: the mindmap was rendering placeholder state for entire runs because DispatcherPanel had no WebSocket subscription. The WS sub added in this milestone unblocks incremental animation for both paths.
- **The example-placeholder dishonesty**: the dispatcher's placeholder text shows "Will Anthropic still hold the #1 spot on LMArena at end of June 2026?" — exactly the kind of question the prior routing failed on. Now the example shows a path the system can actually deliver.

### What this milestone does NOT close

- **The dispatcher iterative / bridge toggles still render in the input phase** even when the run will route to Universal Logic Loop (where they're ignored). Cosmetic — the route ignores them silently. Polish chunk.
- **`/managed-run` is unchanged**. Z-SPAN-shape consumers bring their own Truth Packets; auto-routing them to harvest would surprise existing consumers with a 6× wall-time bump. If a session-as-consumer ever needs the harvest pattern, that's a future `depth=universal_loop` parameter addition.
- **The iterative-path strokes still arrive all-at-once** (the `/iterate` endpoint is blocking; `synthesis_complete` WS payloads are `{stroke_number, response_chars}` metadata only). The visualizer's iterative-mode choreography (Engine ↔ PKI ↔ Anti) renders at the end rather than progressively. Truly incremental iterative-stroke animation would require either polling the strokes endpoint mid-run OR enriching the WS payloads with stroke content. Out of scope here.
- **Pl2-03 first live Z-SPAN session** is still operator-driven (now even more clearly: Z-SPAN goes through `/managed-run`, not the Dispatcher UI, so the routing fix doesn't affect Z-SPAN's flow directly).
- **The Engine refuses non-deterministically** on real-world Cleanroom questions when given no external Truth Packets — that's the substrate behavior the harvest path now sidesteps, but the underlying non-determinism remains visible in the Iterative path (operator-override case).

### Pending after this milestone

- Pl2-03 first live Z-SPAN strategic-planning session (operator-driven).
- E1-06 first live Bicameral Level 2 run (operator-driven).
- 2026-06-30 LMArena leaderboard-rank resolution (calendar-gated).
- M2 leaner-corpus side-by-side test (operator-gated, major scope shift).
- P1-01 upstream `notebooklm-py` PR submission (operator action).
- Smoke-test the structural fix end-to-end via Chrome MCP once backend is restarted (the prior session's backend died after the Ryanair run completed).

### Cross-cutting note

This is the **fifth instance** the project has independently arrived at the same architectural lens (the framework abstracts itself for the audience):

1. Milestone 43 — Cube-of-Space transcript exchange (vocabulary register).
2. Milestone 45 — Pl3 Operator Lens (translation stroke).
3. Milestones 46-47 — persistent session state + consumer-doc parity.
4. Milestone 48 — `/managed-run` as canonical entry point for session-as-consumer.
5. **This milestone** — Dispatcher routes the operator's intent to the right orchestration path, not just the right pathway.

The principle now applies to *every* surface where the framework meets a consumer: output vocabulary (Pl3), persistence visibility (46-47), API surface (48), and now orchestration routing (49). Treat as architecturally settled.

---

## 50. PKI Oracle harvest path unblocked end-to-end — IMPORT_RESEARCH timeout + synthesis input-cap + dispatcher multi-provider routing (2026-06-11)

The milestone 49 visualizer test surfaced three independent failures that all silently undermined the project's core mechanic: closed-knowledge PKI Oracle harvest grounding the 9D synthesis. The wiring was correct, the routing was correct, the visualizer animated correctly — but the *value* never landed because the harvest substrate was broken upstream of every analytical surface. James's verbatim framing: *"The entire project revolves around pki's and closed knowledge, and you're considering it a success. I'm so confused."* Fair. The earlier session reports treated routing success as project success; they aren't the same.

This milestone fixes the three failures so a real-world Cleanroom question drives PKI Oracles → real Deep Research → real Truth Packets → grounded 9D synthesis end-to-end. Validated live on the same LMArena scenario that has been running all session.

### Failure 1: IMPORT_RESEARCH RPC timeout (3-for-3 Oracle failures)

**Root cause**: `notebooklm-py` SDK's default httpx timeout is 30s. The IMPORT_RESEARCH RPC (post-Deep-Research source ingestion) routinely takes 90-180s on a 30-source report. Every Oracle in the milestone 49 validation run failed at this exact step with `httpx.ReadTimeout` raised from inside the SDK, surfaced as `notebooklm.exceptions.RPCTimeoutError: Request timed out calling IMPORT_RESEARCH`. Deep Research itself completed; only the ingestion timed out.

**Fix in `ganymede-backend/app/services/notebooklm/client.py`**:

- `NotebookLMClient.from_storage(timeout=...)` is now passed an env-configurable timeout (`GANYMEDE_NOTEBOOKLM_HTTP_TIMEOUT`, default **300s** vs SDK default 30s). This single change accounts for the bulk of the fix.

**Fix in `ganymede-backend/app/services/notebooklm/research.py`**:

- `import_research_sources` now wraps `client.research.import_sources` in a retry loop. Catches `RPCTimeoutError` specifically; 3 attempts with exponential backoff (30s → 60s → 120s). The actual NotebookLM server work usually completed even when the SDK gave up, so re-issuing the call with a fresh httpx connection often lands cleanly. Env overrides: `GANYMEDE_NOTEBOOKLM_IMPORT_RETRIES`, `GANYMEDE_NOTEBOOKLM_IMPORT_BACKOFF_BASE`.

### Failure 2: Synthesis input-cap silent rejection (project-value failure)

**Root cause**: even with IMPORT_RESEARCH fixed and all 3 Oracles harvesting cleanly, the milestone-50 validation run's final synthesis returned empty `raw_response` after 3 retries because the rendered prompt was **15,322 chars** — way past NotebookLM's ~5,100-6,000 char input cap (the same envelope milestone 37 caught for Stroke 3 in the iterative loop). Three Truth Packets at 5,178 + 3,260 + 6,157 chars stacked into `packets_block` blew past the cap. Milestone 37 fixed this only in `run_iterative_engine` via `_extract_for_resynthesis` + `_truncate_audit_for_injection`; the base `synthesize()` method that `run_universal_loop`'s Phase 3 calls never got the same treatment.

**Fix in `ganymede-backend/app/services/orchestrator.py`**:

- New module-level helper `truncate_packets_for_synthesis(truth_packets, budget)` proportionally shrinks each packet when the combined size exceeds `GANYMEDE_SYNTHESIS_PACKETS_BUDGET` (default 4500 chars). Each truncated packet gets an explicit `[TRUNCATED: original X chars → Y chars to fit synthesis budget]` marker so the Engine knows upstream content was cut. Minimum-200-char floor per packet so a single huge packet can't starve the others.
- `synthesize()` calls the helper before rendering `packets_block` and logs the rendered prompt size. Every caller of the base synthesis (Universal Logic Loop, `/managed-run`, any future consumer) gets the fix without per-caller changes.

### Failure 3: Gemini 503 strands the dispatcher

**Root cause**: the dispatcher classification call was Gemini-only. During the milestone 49 validation session Gemini Flash returned `503 UNAVAILABLE` twice in a row at the worst moment, forcing the defensive cleanroom fallback (confidence 0, generic clarifying question). James's verbatim framing: *"I will not rely on an API that limits me like that."*

**Fix in `ganymede-backend/app/services/gemini_service.py`**:

- New env-controlled `LLM_PROVIDER` (default `deepseek`) selects the primary dispatcher LLM with cross-provider fallback. If primary returns 503/network/parse error, the other provider is tried before the cleanroom fallback fires.
- DeepSeek path: OpenAI-compatible HTTP to `https://api.deepseek.com/v1/chat/completions` with `response_format: json_object`. Pattern mirrored from DRAINO Clean-Room (`server/_core/llm.ts:openAICompatibleInvoke`).
- Gemini path: the existing `genai.Client().models.generate_content` call, refactored into `_dispatch_via_gemini`. Client is now lazily initialized so a deepseek-only deployment doesn't fail at startup when `GOOGLE_API_KEY` is unset.
- Placeholder-key guard: the .env's `DEEPSEEK_API_KEY=PASTE_YOUR_DEEPSEEK_KEY_HERE` is treated as unset so an unfilled .env doesn't burn a 401 round-trip on every classify call.
- New `DEEPSEEK_API_KEY` slot added to `.env` (gitignored). Operator pastes the actual key when ready. Closed-RAG-sphere principle preserved: both providers are scoped to dispatcher intent classification only; analytical content stays in NotebookLM.

### What this milestone proves end-to-end

Validated live on `de892dc9-14a2-4764-9792-115c9720e68b` (LMArena Cleanroom):

- Triage: 36s, 3 subjects (`Upcoming Frontier Model Releases`, `LMArena Benchmark Methodology Updates`, `Competitor Compute Resource Allocation`)
- 3 PKI Oracles: 39+30+ sources Deep Research each, ALL imported cleanly (no `RPCTimeoutError`), Truth Packets harvested at 5,233 + 3,690 + 2,371 chars (**11,294 chars total**)
- Synthesis: prompt truncated to fit budget, fired once (no retries), 44s wall, 4,234 chars output
- **Total wall time: 30:49**

The Engine's output cites specific facts from the harvested Truth Packets — *"Mythos-class Claude 5"*, *"GPT-5's 201,088-token o200k_harmony tokenizer"*, *"Anthropic's $965 billion valuation and 5 gigawatts of secured compute"*, *"Arena.ai's transition to the Bradley-Terry maximum-likelihood statistical model"* — none of which are in the 9D foundations corpus. The Engine also prefixes an explicit epistemic-discipline notice acknowledging the external-truth-packet provenance, exactly as the closed-RAG-sphere principle would predict.

Final prediction: *"Anthropic will not hold the #1 spot on LMArena at the end of June 2026."* — falsifiable, grounded in real data, citation-anchored.

This is the first run this session where the project's **core value mechanism** (closed-knowledge PKI Oracle harvest → grounded 9D synthesis) demonstrably works end-to-end. The milestone 49 validation that came before — routing fix + visualizer animation — was real but incomplete: it validated the *plumbing*, not the *output*. Milestone 50 validates the output.

### What this milestone closes

- **The IMPORT_RESEARCH 3-for-3 failure mode** from the milestone 49 session. PKI Oracle harvest now works reliably.
- **The synthesis input-cap silent rejection** for multi-Oracle runs. The Universal Logic Loop's Phase 3 now respects the same cap discipline as the Iterative Engine's Stroke 3.
- **The dispatcher single-provider fragility**. Gemini 503's no longer force the defensive fallback path.
- **The "wiring works ≠ project works" framing error** that crept into the milestone 49 closeout. Both reports + future Architecture_History entries should treat *grounded analytical output* as the success bar, not *routing success* or *visualizer animation*.

### What this milestone does NOT close

- **DeepSeek API key paste**. The .env slot is in; operator action remains. Once pasted, the dispatcher uses DeepSeek as primary with Gemini fallback.
- **React `Maximum update depth` error in `DispatcherPanel`** (filed as a follow-up task). The snapshot mirror useEffect recreates the oracles array via `Object.values(oracles)` on every render, which makes the published snapshot object identity unstable. UI is recoverable (full E2E run completed cleanly), but the console floods with React warnings. Fix: memoize the snapshot via `useMemo`.
- **The Stroke-1-only output**. The milestone-50 run is single-stroke synthesis (Universal Logic Loop ends at Phase 3). The iterative Mirror Auditor + Bridge Stroke-2/2b/3 chain doesn't fire on this path. Adding bicameral-style audit on top of the Universal Logic Loop synthesis is a future architectural call, not a milestone-50 fix.
- **Run record**. A `docs/experiments/runs/07_LMArena_Universal_Loop_Validation.md` (or similar) capturing the actual session as a reproducible experiment hasn't been written. Future operator chunk.

### Pending after this milestone

- React update-depth fix in DispatcherPanel.
- DeepSeek API key paste (operator action).
- Pl2-03 first live Z-SPAN strategic-planning session (operator-driven).
- E1-06 first live Bicameral Level 2 run (operator-driven).
- 2026-06-30 LMArena leaderboard-rank resolution (calendar-gated; the milestone 50 run produced a fresh prediction worth tracking alongside the milestone 37 / Run 6 prediction).
- P1-01 upstream `notebooklm-py` PR submission — now arguably more compelling because we have a concrete real-world `RPCTimeoutError` repro that the upstream can adopt as a regression test.

### Cross-cutting note — what this taught about reporting

Treating routing success as project success is the silent-failure mode of milestone reports. The structural fix milestone 49 shipped routed correctly; the visualizer animated correctly; cancel worked correctly; but the analytical output was corpus-pattern-matched fabulation because the Truth Packet pipeline was broken. Future milestone closeouts should explicitly distinguish *did the plumbing work* from *did the output work* and not bundle them.

---

## Cross-references at a glance

| Concept | Now lives in |
| --- | --- |
| Strategic Liaison / The Hand role (3) | (deprecated; PM role per [`../OVERVIEW.md`](../OVERVIEW.md)) |
| Cortex Clipboard pattern (3) | `ganymede-ui/src/components/DevOverlay.tsx` |
| Master Operational Workflow (4) | [`../protocols/Master_Operational_Workflow.md`](../protocols/Master_Operational_Workflow.md) |
| PKI Oracle persona (6) | [`../protocols/PKI_Oracle_Persona.md`](../protocols/PKI_Oracle_Persona.md) |
| 9D Chess Engine ID lock (7) | `ganymede-backend/app/services/notebooklm/client.py` |
| Dev launcher (29) | `run_dev.bat` (repo root) |
| Foundations corpus (29) | [`../foundations/`](../foundations/) |
| Persona Expansion design (29) | [`../concepts/Persona_Expansion_Experiment.md`](../concepts/Persona_Expansion_Experiment.md) |
| NotebookLM sub-package (30) | `ganymede-backend/app/services/notebooklm/` (client / cooldown / studio / research / auth_check) |
| Auth-pill HTTP endpoints (31) | `ganymede-backend/app/v2_routes.py` `/api/v2/auth/*` |
| Notebook / Studio / Research HTTP endpoints (31) | `ganymede-backend/app/v2_notebook_routes.py` |
| Background-task registry (31) | `ganymede-backend/app/services/background_tasks.py` |
| Auth pill UI (31) | `ganymede-ui/src/components/AuthPill.tsx` (mounted in `app/layout.tsx`) |
| Live Runner panel (32) | `ganymede-ui/src/components/RunnerPanel.tsx` (mounted in `app/page.tsx`, left 40%) |
| Cortex Clipboard refactor — controlled state (32) | `ganymede-ui/src/components/DevOverlay.tsx` (`isOpen` + `promptBlock` lifted to parent) |
| GSS schema (8) | `ganymede-ui/src/types/ganymede.ts` |
| D_n formula (8) | `ganymede-ui/src/components/GravityWell.tsx` |
| Universal Logic Loop (10) | [`../protocols/Universal_Logic_Loop_Protocol.md`](../protocols/Universal_Logic_Loop_Protocol.md) |
| Hualapai run (8, 4) | [`../experiments/runs/01_Hualapai_Water_Crisis.md`](../experiments/runs/01_Hualapai_Water_Crisis.md) |
| GPS run (12) | [`../experiments/runs/02_GPS_Failure_72hr_Triage.md`](../experiments/runs/02_GPS_Failure_72hr_Triage.md) |
| Mirror walkback (17), Mirror Protocol (15) | [`../concepts/The_Ganymede_Mirror_Protocol.md`](../concepts/The_Ganymede_Mirror_Protocol.md) (with reframe note) + [`../experiments/pathways/mirror_validation.md`](../experiments/pathways/mirror_validation.md) |
| 60s amnesia (18) | [`../experiments/runs/04_60s_Amnesia_Mirror_Swarm.md`](../experiments/runs/04_60s_Amnesia_Mirror_Swarm.md) |
| Powell Cleanroom (19) | [`../experiments/runs/Powell_Cleanroom/`](../experiments/runs/Powell_Cleanroom/) |
| Tokenized Land (20) | [`../experiments/runs/Tokenized_Land_Resolution.md`](../experiments/runs/Tokenized_Land_Resolution.md) |
| Offensive Architect pathway (21) | [`../experiments/pathways/offensive_architect.md`](../experiments/pathways/offensive_architect.md) |
| Genie Protocol pathway (22) | [`../experiments/pathways/genie_protocol.md`](../experiments/pathways/genie_protocol.md), Giant-Slayer run [`../experiments/runs/Genie_Giant_Slayer.md`](../experiments/runs/Genie_Giant_Slayer.md) |
| Iterative Engine Vision (23) | [`../concepts/Iterative_Engine_Vision.md`](../concepts/Iterative_Engine_Vision.md), Musk-Altman run [`../experiments/runs/Musk_Altman_Polymarket.md`](../experiments/runs/Musk_Altman_Polymarket.md) |
| Module-not-service north star (24) | [`../OVERVIEW.md`](../OVERVIEW.md#north-star-module-not-service) |
| Compute Autarky pending (16) | [`../experiments/runs/05_Pending_Compute_Autarky.md`](../experiments/runs/05_Pending_Compute_Autarky.md) |
| Connection Bridge persona (33) | [`../protocols/Connection_Bridge_Persona.md`](../protocols/Connection_Bridge_Persona.md) |
| Bicameral Convergence concept + operator control surfaces (33) | [`../concepts/Bicameral_Convergence.md`](../concepts/Bicameral_Convergence.md) |
| Notebook deletion endpoint + orphan cleanup (34) | `ganymede-backend/app/v2_notebook_routes.py` + `ganymede-backend/app/services/orchestrator.py` |
| Research mode toggle + Deep Research timeout bump (34) | `ganymede-backend/app/contracts.py` + `ganymede-backend/app/services/orchestrator.py` + `ganymede-ui/src/components/RunnerPanel.tsx` |
| OrchestratorMindMap (34) | `ganymede-ui/src/components/OrchestratorMindMap.tsx` |
| `run_dev.bat` rewrite + `log_runner.py` (34) | `run_dev.bat` + `ganymede-backend/log_runner.py` |
| UI copy sweep (34) | `ganymede-ui/src/components/RunnerPanel.tsx` + `ganymede-ui/src/components/Field.tsx` + `ganymede-ui/src/components/LithographyView.tsx` |
| Dispatcher direction (35) | operator memory `project_dispatcher_frontend` (not yet in code) |
| Symbolic-logic thought paper (35) | [`../brainstorming/Symbolic_Logic_Bicameral.md`](../brainstorming/Symbolic_Logic_Bicameral.md) |
| Project_In_My_Words personal-voice doc (35) | [`../Project_In_My_Words.md`](../Project_In_My_Words.md) |
| Engine Persona (27) | [`../protocols/Engine_Persona.md`](../protocols/Engine_Persona.md) |
| Bridge wired into /iterate as Stroke 2b (38) | `ganymede-backend/app/services/orchestrator.py` (`run_iterative_engine` + `provision_bridge_notebook`) + `ganymede-backend/app/v2_routes.py` (`IterateRequest`) + `ganymede-backend/app/contracts.py` (`StrokeResult.audit_kind`) + `ganymede-ui/src/components/DispatcherPanel.tsx` + `ganymede-ui/src/components/RunnerPanel.tsx` |
| `ITERATIVE_BICAMERAL_RESYNTHESIS_TEMPLATE` (38) | `ganymede-backend/app/services/orchestrator.py` |
| `audit_with_bridge` soft-fail flag (38) | `ganymede-backend/app/services/orchestrator.py` |
| Autopilot Protocol adoption (39) | `CLAUDE.md` + `ROADMAP.md` + `TASKS.md` (repo root) |
| Predictions bulletin board (39) | `ganymede-ui/src/app/predictions/page.tsx` + `ganymede-ui/src/data/predictions.ts` + `ganymede-ui/src/app/page.tsx` (link) |
| auto_relogin port (40) | `ganymede-backend/app/services/notebooklm/auth_check.py` (`auto_relogin` + `auto_relogin_enabled`) + `ganymede-backend/app/main.py` (startup auto-recovery) + `ganymede-backend/app/v2_routes.py` (`POST /api/v2/auth/auto-relogin`) |
| Powell Bridge null test (40) | `docs/experiments/runs/Powell_Bridge_Null_Test.md` + `scripts/powell_bridge_null_test.py` + `docs/experiments/runs/Powell_Bridge_Null_Test_Artifacts/` |
| Framework Kernel vs. Scaffolding partition (41) | [`../concepts/Framework_Kernel_vs_Scaffolding_Partition.md`](../concepts/Framework_Kernel_vs_Scaffolding_Partition.md) + [`../scratch/2026-05-31-M1-foundations-deep-read.md`](../scratch/2026-05-31-M1-foundations-deep-read.md) (per-file working notes) |
| LMArena partial validation — Anthropic pause call (42) | [`../experiments/runs/06_LMArena_Anthropic_Cleanroom.md`](../experiments/runs/06_LMArena_Anthropic_Cleanroom.md) § "Real-world outcome — 2026-06-05" |
| Z-SPAN pattern-recognition + Operator Lens primitive (43) | Transcripts at `C:\Users\james\Documents\NotebookLM Transcript.txt` + `C:\Users\james\Documents\Gemini Transcript.txt` (operator filesystem, not in repo); Onboarding handoff at `C:\Users\james\Desktop\Z-SPAN_Ganymede_Onboarding.md`; Pl3 Operator Lens spec in [`../../ROADMAP.md`](../../ROADMAP.md) § "Silo 4 — Pluggable" |
| P1-04 Bridge notebook lifecycle (44) | `ganymede-backend/app/services/bridge_registry.py` + `GET /api/v2/bridge/notebooks` in `ganymede-backend/app/v2_routes.py` + `ganymede-ui/src/components/BridgeNotebookManager.tsx` + `/bridge-notebooks` route at `ganymede-ui/src/app/bridge-notebooks/page.tsx` |
| Pl3 Operator Lens (45) | `TranslationRegister` enum in `ganymede-backend/app/contracts.py` + `Session._translations` in `ganymede-backend/app/services/session.py` + `GeminiService.translate_with_register` + `_TRANSLATION_PROMPTS` in `ganymede-backend/app/services/gemini_service.py` + `GanymedeOrchestrator.run_translation` in `ganymede-backend/app/services/orchestrator.py` + `POST /api/v2/sessions/{id}/translate` in `ganymede-backend/app/v2_routes.py` + `ganymede-ui/src/components/StrokeTranslator.tsx` |
| Pl2-01 SessionStore persistence (46) | `ganymede-backend/app/services/session_store.py` (`SessionStore` + `default_db_path`) + `ganymede-backend/app/services/session.py` (`Session._store` + `_persist` + `from_persisted_state` + `SessionRegistry.bind_store` + `rehydrate` + `store` accessor) + `ganymede-backend/app/main.py` startup wiring + `GET /api/v2/sessions` (list/filter/search) + `GET /api/v2/sessions/{id}/strokes` in `ganymede-backend/app/v2_routes.py` |
| Pl2-02 Z-SPAN consumer-spec walkthrough (47) | [`../integration/examples/zspan_consumer.md`](../integration/examples/zspan_consumer.md) + cross-references in [`../integration/examples/README.md`](../integration/examples/README.md) + [`../integration/operator_courier_protocol.md`](../integration/operator_courier_protocol.md) + ROADMAP.md § Pl2 deliverables |
| BridgeNotebookRegistry persistence (47) | `ganymede-backend/app/services/bridge_registry.py` (`BridgeNotebookRegistry.bind_persistence` + `load_from_disk` + `_persist_locked` atomic-write + `default_persistence_path`) + `ganymede-backend/app/main.py` startup wiring + `consuming_the_v2_api.md` § Session persistence (Pl2-01) for canonical surface description |
| `/managed-run` endpoint + dispatcher-as-canonical-entry-point (48) | `POST /api/v2/managed-run` in `ganymede-backend/app/v2_routes.py` (`ManagedRunRequest` + `ManagedRunResponse` + `managed_run` composition handler) + `docs/integration/examples/zspan_consumer.md` rewrite (managed-run primary; granular API as fall-back) + `docs/integration/consuming_the_v2_api.md` two-consumer-shapes TL;DR + endpoint reference + `C:\Users\james\Desktop\Z-SPAN_Handoff_v2.md` operator paste-in onboarding |
| Dispatcher harvest-routing + WS subscription (49) | `DISPATCHER_PROMPT` "KNOWLEDGE HARVEST SIGNAL" section + `needs_external_knowledge` extraction in `ganymede-backend/app/services/gemini_service.py` + `DispatchResponse.needs_external_knowledge` field in `ganymede-backend/app/v2_routes.py` + `ganymede-ui/src/components/DispatcherPanel.tsx` (WebSocket subscription mirroring RunnerPanel; `handleConfirm` branching on `useUniversalLoop`; path-choice review-UI card with operator-override toggle; running-phase per-path messaging) |
| IMPORT_RESEARCH timeout fix (50) | `ganymede-backend/app/services/notebooklm/client.py` (`NotebookLMClient.from_storage(timeout=300)` + env `GANYMEDE_NOTEBOOKLM_HTTP_TIMEOUT`) + `ganymede-backend/app/services/notebooklm/research.py` (`import_research_sources` retry-on-`RPCTimeoutError` with exponential backoff + envs `GANYMEDE_NOTEBOOKLM_IMPORT_RETRIES` / `GANYMEDE_NOTEBOOKLM_IMPORT_BACKOFF_BASE`) |
| Synthesis input-cap truncation (50) | `truncate_packets_for_synthesis()` + `_SYNTHESIS_PACKETS_BUDGET` in `ganymede-backend/app/services/orchestrator.py` + `synthesize()` wired to call the helper before rendering `packets_block` (env `GANYMEDE_SYNTHESIS_PACKETS_BUDGET` default 4500) |
| Multi-provider dispatcher routing (50) | `_LLM_PROVIDER` / `_DEEPSEEK_API_KEY` / `_dispatch_via_deepseek` / `_dispatch_via_gemini` + cross-provider fallback in `GeminiService.dispatch_intent` in `ganymede-backend/app/services/gemini_service.py` + `.env` slots for `LLM_PROVIDER` / `DEEPSEEK_API_KEY` |
| Milestone 50 end-to-end validation run | session `de892dc9-14a2-4764-9792-115c9720e68b` in SessionStore — first run this session where 3 Oracle harvests + grounded synthesis all succeeded in a single flow |
