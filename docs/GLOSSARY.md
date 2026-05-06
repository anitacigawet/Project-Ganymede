# Glossary

The vocabulary of the project, in one place. Several terms have been refined through brainstorming and carry a specific operational meaning here that doesn't always match the term's general usage.

---

### 9D Chess Engine (the Umpire)
A single, hard-coded NotebookLM with ID `5967ce5d-f9eb-4f4e-b3e1-620f643d8390`. Treated as the project's strategic logic core. Read-only. Pre-configured outside this codebase. Queried via `NotebookLMService.query_chess_engine`. Never modified.

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
A prompt-engineering technique for the Umpire: framing the query with a "you are in a dream" metaphor to bypass the engine's mathematical rigidity and elicit fluid synthesis. Documented in [`learnings/Iterative_Operational_Learnings.md`](learnings/Iterative_Operational_Learnings.md).

### The Mirror / ESP Collective
The recursive insight surfaced during the GPS-failure run: the Umpire's "Hive Mind" scenario was implicitly modeling the laboratory itself (user + orchestrator + oracle swarm). The lab is a 9D actor. Documented in [`concepts/The_Ganymede_Mirror_Protocol.md`](concepts/The_Ganymede_Mirror_Protocol.md) and the `concepts/Mirror_Protocol/` subfolder.

### Museum vs. Lab
Two separate UI modes envisioned in the original blueprints. The **Museum** is the public-facing exhibit gallery (a curated set of pre-rendered topologies). The **Lab** is the live orchestration environment (single-scenario, real-time). The current frontend implements the Museum shell; the Lab orchestration UI is not yet built.

### Compiler Note
A short directive Gemini sometimes attaches to its GSS payload, describing reactive entanglements (e.g. "agricultural nodes are tied to industrial draw rate"). The frontend treats these as informational; the entanglement logic is enforced in code regardless.
