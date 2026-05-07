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

---

## Cross-references at a glance

| Concept | Now lives in |
| --- | --- |
| Strategic Liaison / The Hand role (3) | (deprecated; PM role per [`../OVERVIEW.md`](../OVERVIEW.md)) |
| Cortex Clipboard pattern (3) | `ganymede-ui/src/components/DevOverlay.tsx` |
| Master Operational Workflow (4) | [`../protocols/Master_Operational_Workflow.md`](../protocols/Master_Operational_Workflow.md) |
| PKI Oracle persona (6) | [`../protocols/PKI_Oracle_Persona.md`](../protocols/PKI_Oracle_Persona.md) |
| 9D Chess Engine ID lock (7) | `ganymede-backend/app/services/notebooklm_service.py` |
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
