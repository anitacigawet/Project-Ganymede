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

This was the handoff point. With the artifact ingestion completed in this reorganization pass, the Mirror Protocol documentation is now in the repo as [`../concepts/The_Ganymede_Mirror_Protocol.md`](../concepts/The_Ganymede_Mirror_Protocol.md) plus the four sub-docs. The next intended run, **Compute Autarky**, is recorded in [`../experiments/05_Pending_Compute_Autarky.md`](../experiments/05_Pending_Compute_Autarky.md).

---

## Cross-references at a glance

| Concept introduced in milestone | Now lives in |
| --- | --- |
| Strategic Liaison / The Hand role (3) | (deprecated; see [`../OVERVIEW.md`](../OVERVIEW.md)) |
| Cortex Clipboard pattern (3) | `ganymede-ui/src/components/DevOverlay.tsx` |
| Master Operational Workflow (4) | [`../protocols/Master_Operational_Workflow.md`](../protocols/Master_Operational_Workflow.md) |
| PKI Oracle persona (6) | [`../protocols/PKI_Oracle_Persona.md`](../protocols/PKI_Oracle_Persona.md) |
| 9D Chess Engine ID lock (7) | `ganymede-backend/app/services/notebooklm_service.py` |
| GSS schema (8) | `ganymede-ui/src/types/ganymede.ts` |
| D_n formula (8) | `ganymede-ui/src/components/GravityWell.tsx` |
| Universal Logic Loop (10) | [`../protocols/Universal_Logic_Loop_Protocol.md`](../protocols/Universal_Logic_Loop_Protocol.md) |
| Hualapai run (8, 4) | [`../experiments/01_Hualapai_Water_Crisis.md`](../experiments/01_Hualapai_Water_Crisis.md) |
| GPS run (12) | [`../experiments/02_GPS_Failure_72hr_Triage.md`](../experiments/02_GPS_Failure_72hr_Triage.md) |
| Powell run (13) | [`../experiments/03_Powell_Validation_Event.md`](../experiments/03_Powell_Validation_Event.md) |
| 60s amnesia run (14) | [`../experiments/04_60s_Amnesia_Mirror_Swarm.md`](../experiments/04_60s_Amnesia_Mirror_Swarm.md) |
| Mirror Protocol (15) | [`../concepts/The_Ganymede_Mirror_Protocol.md`](../concepts/The_Ganymede_Mirror_Protocol.md) and `concepts/Mirror_Protocol/` |
| Compute Autarky proposal (15, 16) | [`../experiments/05_Pending_Compute_Autarky.md`](../experiments/05_Pending_Compute_Autarky.md) |
