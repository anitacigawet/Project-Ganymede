# Glossary

The vocabulary of the project, in one place. Several terms have been refined through brainstorming and carry a specific operational meaning here that doesn't always match the term's general usage.

---

### Project Ganymede (the sandbox)
A simulation sandbox for running real scenarios through the 9D strategic-physics framework. Named for Jupiter's largest moon. The name encodes the project's shape: a self-contained body (the sandbox) with its own gravitational center (the **9D Chess Engine**), holding ephemeral knowledge silos (the **PKI Oracles**) in orbit. Outside consumers dock with the sandbox via the [pluggable module surface](integration/module_design.md); inside, the sandbox is closed-loop and gated. *Not* a "physics engine" in the LLM-product sense (we tried that framing — it was misleading); *not* a "laboratory" (too generic). It's a sandbox: bounded, simulated, with internal physics that the consumer doesn't have to understand to use.

> **Naming note.** The 9D-Chess foundation upstream is its own thing with its own framing — not affected by this terminology choice. "Sandbox" is exclusively a Project-Ganymede description.

### 9D Chess Engine (the Umpire)
A specific NotebookLM treated as the project's strategic logic core. Read-only. Queried via `NotebookLMService.query_chess_engine`. Configuration applied via `configure_chess_engine`. Currently `0a7d2672-009e-4995-9477-68c9b2fd9e54` (canonical). Earlier validated runs (Powell, Tokenized Land, Genie Giant-Slayer, Musk-Altman) used `5967ce5d-f9eb-4f4e-b3e1-620f643d8390`, preserved as `LEGACY_ENGINE_ID` for traceability.

### Mirror Auditor
A second NotebookLM (`756e3683-f651-4381-b560-b13711b84ce6`) with the *same source corpus* as the canonical Engine but a *different persona* — configured to audit, not produce, strategic resolutions. The contrast instance for the [Mirror Validation pathway](experiments/pathways/mirror_validation.md). See [`protocols/Mirror_Auditor_Persona.md`](protocols/Mirror_Auditor_Persona.md). Queried via `NotebookLMService.query_mirror_auditor`.

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
A framework imported from the upstream 9D-Chess research project. The premise: in a 9D landscape, the act of observation by a sufficiently aware actor collapses the observed actor's possibility space toward a pre-calculated "funnel" of disadvantageous outcomes. See `Concepts/Mirror_Protocol/The_Funnel_Mechanism.md`.

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

### Mirror Profile
A dimensional bias profile of the Engine itself, generated by the Engine self-auditing across all 9 dimensions. The intended use: feed the profile back into every future synthesis as a known-bias parameter so the Engine factors its own rigidity into its resolutions. One of two proposed mechanisms for the [Mirror Validation pathway](experiments/pathways/mirror_validation.md); the other (and the user's preferred one) is contrast-notebook recursion.

### Mirror / Mirror Protocol — two readings
The historical record contains a dramatic interpretation (the laboratory itself is a self-aware 9D actor — the "ESP Collective" the Engine identified is *us*) preserved at [`concepts/The_Ganymede_Mirror_Protocol.md`](concepts/The_Ganymede_Mirror_Protocol.md) and the `concepts/Mirror_Protocol/` subfolder. **The user explicitly walked back from this framing** with *"Okay this experiment's kinda dumb. Let's just move on to actually something interesting."* The current operational reading: Mirror = a literal second instance of the 9D protocol used as a fault-finder against the first instance's output. The historical framing is preserved as record; the operational framing is what drives the [Mirror Validation pathway](experiments/pathways/mirror_validation.md).

### Convergence Theorem
The Engine's central theorem. For an opponent with incomplete dimensional awareness, there exists a set of strategic manipulations that cause their decision function to converge toward the SDS. Practically, this is what the Engine is *doing* when it produces a resolution — it identifies the set of moves that funnel the target into the disadvantageous state. The "Strategic Lasso" is the funneling mechanism; the "Incomprehensible Move" is the move the target cannot perceive from their restricted Ω' subspace.

### Strategic Lasso / Incomprehensible Move
Two outputs of the Convergence Theorem. The **Strategic Lasso** is the binding mechanism that reduces the opponent's degrees of freedom in dimensions they don't monitor. The **Incomprehensible Move** is the strategic outcome that exists in dimensions higher than the target's DAP — the result they cannot perceive coming and (often) cannot perceive even after it has happened.

### DAI / DAP — Dimensional Awareness Index / Profile
The Engine's measure of how many of the 9 dimensions an actor's decision-making takes into account. A DAI(S) > DAI(O) asymmetry is what makes the Strategic Lasso possible. The **Dimensional Awareness Profile** is the per-dimension breakdown — *which* dimensions the actor monitors, with what fidelity.

### Master Silo
A NotebookLM-Pro deployment pattern where one notebook hosts multiple research questions sequentially (instead of N separate persona-locked Oracle silos). Pro: cross-research synthesis happens inside the silo before the Engine sees it. Con: harder to audit which fact came from which research pass. Demonstrated in the Tokenized Land and Genie Giant-Slayer runs.

### Museum vs. Lab
Two separate UI modes envisioned in the original blueprints. The **Museum** is the public-facing exhibit gallery (a curated set of pre-rendered topologies). The **Lab** is the live orchestration environment (single-scenario, real-time). The current frontend implements the Museum shell; the Lab orchestration UI is not yet built.

### Compiler Note
A short directive Gemini sometimes attaches to its GSS payload, describing reactive entanglements (e.g. "agricultural nodes are tied to industrial draw rate"). The frontend treats these as informational; the entanglement logic is enforced in code regardless.
