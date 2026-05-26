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
