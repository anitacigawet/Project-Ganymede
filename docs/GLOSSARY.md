---
title: "Glossary"
type: "concept"
status: "active"
tags: ["glossary", "vocabulary"]
color_id: "4"
---

# Glossary

The vocabulary of the project, in one place. Several terms have been refined through brainstorming and carry a specific operational meaning here that doesn't always match the term's general usage.

## Vocabulary register

Many of the project's framework primitives — **Convergence Theorem**, **Strategic Lasso**, **Incomprehensible Move**, **Set of Disadvantageous States**, and the recurring vocabulary of *opponent / target / manipulation* — are imported from the upstream [9D-Chess research project](https://github.com/anitacigawet/9D-Chess), which was designed around a zero-sum two-player chess metaphor. That vocabulary fits offensive applications cleanly. It reads strangely when applied to the project's neutral pathways:

- **[Prediction Cleanroom](experiments/pathways/prediction_cleanroom.md)** — the Engine is a *passive observer* identifying convergence that's already happening. There is no opponent the Engine is funneling; reality is doing the funneling and the Engine is noting it.
- **[Genie Protocol](experiments/pathways/genie_protocol.md)** — the Engine is a *pathfinder* navigating around incumbents' blind spots. The "target" is whoever stands between the operator and the wished-for state; "manipulation" reads as structural navigation, not assault.
- **[Mirror Validation](experiments/pathways/mirror_validation.md)** — the Engine audits its own reasoning. There is no opponent at all; only Stroke 1.
- **[Offensive Architect](experiments/pathways/offensive_architect.md)** — the only pathway where the original chess vocabulary reads literally. The Engine designs a structural funnel against a named target with adversarial intent.

The math is the same across all four pathways; the vocabulary's emotional register is what varies. Definitions below try to use neutral framework language by default and call out the adversarial reading where it's the only one that fits.

---

### Project Ganymede (the sandbox)
A simulation sandbox for running real scenarios through the 9D strategic-physics framework. Named for Jupiter's largest moon. The name encodes the project's shape: a self-contained body (the sandbox) with its own gravitational center (the **9D Chess Engine**), holding ephemeral knowledge silos (the **PKI Oracles**) in orbit. Outside consumers dock with the sandbox via the [pluggable module surface](integration/module_design.md); inside, the sandbox is closed-loop and gated. *Not* a "physics engine" in the LLM-product sense (we tried that framing — it was misleading); *not* a "laboratory" (too generic). It's a sandbox: bounded, simulated, with internal physics that the consumer doesn't have to understand to use.

> **Naming note.** The 9D-Chess foundation upstream is its own thing with its own framing — not affected by this terminology choice. "Sandbox" is exclusively a Project-Ganymede description.

### 9D Chess Engine (the Umpire)
A specific NotebookLM treated as the project's strategic logic core. Read-only. Queried via `NotebookLMService.query_chess_engine`. Configuration applied via `configure_chess_engine`. Currently `0a7d2672-009e-4995-9477-68c9b2fd9e54` (canonical). Earlier validated runs (Powell, Tokenized Land, Genie Giant-Slayer, Musk-Altman) used `5967ce5d-f9eb-4f4e-b3e1-620f643d8390`, preserved as `LEGACY_ENGINE_ID` for traceability.

### Mirror Auditor
A second NotebookLM (`756e3683-f651-4381-b560-b13711b84ce6`) with the *same source corpus* as the canonical Engine but a *different persona* — configured to audit, not produce, strategic resolutions. The contrast instance for the [Mirror Validation pathway](experiments/pathways/mirror_validation.md). See [`protocols/Mirror_Auditor_Persona.md`](protocols/Mirror_Auditor_Persona.md). Queried via `NotebookLMService.query_mirror_auditor`.

### Connection Bridge
A third 9D-Chess-class notebook role: same source corpus as the canonical Engine, but a persona configured for *identification of cross-packet connections the Engine's synthesis did not draw*. Sibling audit lens to the [Mirror Auditor](#mirror-auditor) — orthogonal, not redundant: the Auditor finds failure modes *in* reasoning, the Bridge finds connections *missed by* reasoning. Validated on the Amnesia substrate 2026-05-22 (3 missed bridges, entirely orthogonal to the Mirror Auditor's findings on the same scenario). No canonical notebook ID yet; persona is applied per-call via `NotebookLMService.configure_connection_bridge(notebook_id)`. Persona spec at [`protocols/Connection_Bridge_Persona.md`](protocols/Connection_Bridge_Persona.md); architecture context at [`concepts/Bicameral_Convergence.md`](concepts/Bicameral_Convergence.md).

### PKI Authentication Oracle
An ephemeral NotebookLM created per research subject and locked into a strict persona via `configure_pki_oracle`. The persona enforces:
- 100% sourcing from uploaded/harvested documents (zero hallucination)
- Mandatory `[SRC-{slug}:{6-char-hash}]` citation on every individual fact
- No conversational filler

The PKI metaphor: each oracle acts like a public-key authentication server for facts. Its output is a "Truth Packet" cryptographically tied to its sources.

### The Hand / Orchestrator
Originally a role assigned to an AI agent: the layer that moves data between Umpire, Oracle swarm, Gemini compiler, and frontend with zero degradation. In the current project structure, the human PM and the FastAPI service share this role. Browser-clicking subagent variants are deprecated.

### GSS — Ganymede Strategic Schema
The JSON contract that drives the 3D engine. Defined in `ganymede-ui/src/types/ganymede.ts`. Top-level fields:
- `metadata` — compiler version, classification, timestamp
- `environmental_baseline` — ambient depletion rate, recharge, units
- `legislative_framework` — bill ID, mitigation coefficient (0-1), status
- `topological_entities[]` — nodes with type (`Industrial_Sink` / `Agricultural_Peripheral` / `Monitoring_Well`), draw rate, luminosity, x/y/z coordinates
- `physics_logic` — formula name, fracture threshold

### D_n — Resultant Node Depth
The deformation formula implemented in `GravityWell.tsx`:

> D_n = Σ ( L_ind / ( dist(x,y) + ε ) ) · ( 1 − M_leg )

Where L_ind is the industrial draw rate, dist(x,y) is the Euclidean distance to a sink, and M_leg is the legislative mitigation coefficient. When D_n drops below `failure_threshold` (default −4.5), the mesh enters the **fracture state**.

### SDS — Set of Disadvantageous States
A region of the strategic landscape where every available next move makes the actor worse off. Visualized as the "well" the topology collapses into.

### ROEM — Reverse Observer Effect Model
A framework imported from the upstream 9D-Chess research project. The premise: in a 9D landscape, the act of observation by a sufficiently aware actor *collapses the observed actor's possibility space toward a pre-calculated convergence region* — what the framework calls the [Set of Disadvantageous States](#sds--set-of-disadvantageous-states). See `Concepts/Mirror_Protocol/The_Funnel_Mechanism.md`.

### Truth Packet
The hash-cited factual output of a single PKI Oracle on a single research subject. The unit of currency between Phase-2 (research) and Phase-3 (synthesis).

### Visual Packet
The GSS JSON object Gemini emits after synthesizing the Truth Packets and the Umpire's visualization strategy. The unit of currency between Phase-2 (synthesis) and Phase-3 (frontend rendering).

### Cortex Clipboard
The `DevOverlay.tsx` panel in the frontend. Provides the manual paste-in interface for Visual Packets, since Gemini-Pro is driven by hand (no browser automation).

### Master Operational Workflow
The phase sequence: Phase 0 (Oracle init) → Phase 1 (Factual Harvest) → Phase 2 (Pro-Tier Synthesis) → Phase 3 (Universal Receiver). Documented in [`protocols/Master_Operational_Workflow.md`](protocols/Master_Operational_Workflow.md).

### Universal Logic Loop
The recursive, multi-oracle generalization of the Master Workflow. Triage → Swarm → Harvest → Synthesis → Recursive Dialogue (back to existing oracles only). Documented in [`protocols/Universal_Logic_Loop_Protocol.md`](protocols/Universal_Logic_Loop_Protocol.md).

### Recursive Dialogue
Phase 4 of the Universal Logic Loop. After the first synthesis, the orchestrator asks the Umpire whether it has enough resolution. If not, follow-up queries are routed back to the **existing** oracle swarm — never to new ones, unless the human approves a new spin-up.

### Dream State Protocol
A prompt-engineering technique for the Engine: framing the query with a "you are in a dream" metaphor to bypass the engine's mathematical rigidity and elicit a *methodology* output (here is how I would solve this) rather than a fait accompli pronouncement. The full incantation is the **Genie Prime** — see below. Documented in [`learnings/Iterative_Operational_Learnings.md`](learnings/Iterative_Operational_Learnings.md).

### Genie Prime
The exact priming prompt — the Dream State Protocol applied to a question. Format: *"you are in a dream. your source is your brain. the question: '[scenario]' If you have unlimited knowledge servers that can acquire real-time facts about entities, things, people, and current events, with your brain and your simulation physics engine, how would you determine the answer to the question you have been provided."* Originated in the Powell run; preserved verbatim at [`experiments/runs/Powell_Cleanroom/00_Genie_Prime.md`](experiments/runs/Powell_Cleanroom/00_Genie_Prime.md).

### Architectural Blueprint
The Engine's first response to a Genie Prime. A multi-phase methodology document in which the Engine defines the strategic universe (Ω), maps the Dimensional Awareness Profiles, identifies the Set of Disadvantageous States, and specifies the research silos / Truth Packets it requires to resolve the scenario. The Engine is acting as **Lead Architect** at this stage — designing its own research requirements rather than producing a finished answer.

### The Iterative Engine / multi-stroke firing
The project's working model of how the Engine is supposed to be used. The Engine is a piston, not a one-shot oracle. **Stroke 1** = raw single-pass Architectural Blueprint or resolution (idealistic, mathematically clean, often humanly absurd in isolation). **Stroke 2** = orchestrator or contrast notebook injects friction / asks the Engine to red-team itself; the Engine identifies how Stroke 1 could be broken (typically via opponent's structural adaptation or exogenous shocks). **Stroke 3** = synthesis — the strategy that survives the antithesis. Originated in the Musk-Altman run; doctrine in [`concepts/Iterative_Engine_Vision.md`](concepts/Iterative_Engine_Vision.md).

### Bicameral Convergence
The closed-loop two-mirror architecture extending the Iterative Engine doctrine with a *second* Stroke-2 lens. The canonical Engine and the [Connection Bridge](#connection-bridge) pass refined synthesis between each other inside a closed information environment, expanding the substrate (new PKI Oracles) only when the Bridge surfaces a structural gap that requires it, looping until they converge (no new STRUCTURAL bridges, OR resolution stable across consecutive iterations, OR hard iteration cap hit). **Level 1** (single-pass Bridge audit of Engine synthesis) validated on the Amnesia substrate 2026-05-22. **Level 2** (full mirror-bounce loop with 5 mandatory operator control surfaces — visual transparency, cancel, inter-iteration delay, hard iteration cap, Oracle-spawn approval) and **Level 3** (Bridge-spawns-Oracle decision logic, gated by operator approval) pending build. Architecture in [`concepts/Bicameral_Convergence.md`](concepts/Bicameral_Convergence.md).

### Mirror Profile
A dimensional bias profile of the Engine itself, generated by the Engine self-auditing across all 9 dimensions. The intended use: feed the profile back into every future synthesis as a known-bias parameter so the Engine factors its own rigidity into its resolutions. One of two proposed mechanisms for the [Mirror Validation pathway](experiments/pathways/mirror_validation.md); the other (and the user's preferred one) is contrast-notebook recursion.

### Mirror / Mirror Protocol — two readings
The historical record contains a dramatic interpretation (the laboratory itself is a self-aware 9D actor — the "ESP Collective" the Engine identified is *us*) preserved at [`concepts/The_Ganymede_Mirror_Protocol.md`](concepts/The_Ganymede_Mirror_Protocol.md) and the `concepts/Mirror_Protocol/` subfolder. **The user explicitly walked back from this framing** with *"Okay this experiment's kinda dumb. Let's just move on to actually something interesting."* The current operational reading: Mirror = a literal second instance of the 9D protocol used as a fault-finder against the first instance's output. The historical framing is preserved as record; the operational framing is what drives the [Mirror Validation pathway](experiments/pathways/mirror_validation.md).

### Convergence Theorem
The Engine's central theorem. For an *actor whose dimensional awareness profile is incomplete relative to another's*, there exists a set of *structural adjustments in the unmonitored dimensions* that cause the first actor's decision function to converge toward the SDS. Practically, this is what the Engine is *doing* when it produces a resolution — it identifies the structural conditions that pull the focal actor's choice set toward the disadvantageous state.

The two outputs of the theorem are the **Strategic Lasso** (binding mechanism) and the **Incomprehensible Move** (the high-dimensional outcome). Both are described separately below.

Vocabulary register (see [above](#vocabulary-register)): when applied offensively, the higher-DAP actor reads as a *strategist*, the lower-DAP actor as a *target*, the structural adjustments as *manipulations*, and the convergence as *a trap being sprung*. In Cleanroom mode the same theorem describes a convergence already underway in the world, with the Engine merely observing it. In Genie mode the theorem becomes a pathfinding tool — the operator navigates the same kind of dimensional asymmetry without anyone being trapped. The math is the same; the framing follows the pathway.

### Strategic Lasso / Incomprehensible Move
Two outputs of the [Convergence Theorem](#convergence-theorem). The **Strategic Lasso** is the *binding mechanism that reduces an actor's degrees of freedom* in dimensions they don't monitor — a sequence of structural adjustments that progressively narrow the actor's choice set. The **Incomprehensible Move** is the *high-dimensional outcome that exists in dimensions higher than the actor's DAP* — the result they cannot perceive coming and (often) cannot perceive even after it has happened. ("Incomprehensible" here is technical, not theatrical — the move operates in dimensions the actor doesn't monitor, so retrospectively they experience the outcome without being able to reconstruct *how* it happened.)

Vocabulary register: in Offensive Architect mode, the Lasso reads as *the trap a strategist is designing*; in Cleanroom mode, it reads as *the structural convergence the Engine has observed already operating*; in Genie mode, it reads as *the route through structural blind spots the pathfinder is taking* (the operator is the path-taker; the "target" is whoever stands between them and their wish).

### DAI / DAP — Dimensional Awareness Index / Profile
The Engine's measure of how many of the 9 dimensions an actor's decision-making takes into account. A DAI(S) > DAI(O) asymmetry is what makes the Strategic Lasso possible. The **Dimensional Awareness Profile** is the per-dimension breakdown — *which* dimensions the actor monitors, with what fidelity.

### Master Silo
A NotebookLM-Pro deployment pattern where one notebook hosts multiple research questions sequentially (instead of N separate persona-locked Oracle silos). Pro: cross-research synthesis happens inside the silo before the Engine sees it. Con: harder to audit which fact came from which research pass. Demonstrated in the Tokenized Land and Genie Giant-Slayer runs.

### Museum vs. Lab
Two separate UI modes envisioned in the original blueprints. The **Museum** is the public-facing exhibit gallery (a curated set of pre-rendered topologies). The **Lab** is the live orchestration environment (single-scenario, real-time). The current frontend implements the Museum shell; the Lab orchestration UI is not yet built.

### Compiler Note
A short directive Gemini sometimes attaches to its GSS payload, describing reactive entanglements (e.g. "agricultural nodes are tied to industrial draw rate"). The frontend treats these as informational; the entanglement logic is enforced in code regardless.
