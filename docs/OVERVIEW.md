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

## The four silos (canonical project organization)

The project's actual structure, per the user's framing, is four research silos. Pathways and runs and brainstorming all live *inside* these silos — they are techniques, not silos themselves.

| # | Silo | What it does | Active technique(s) | Status |
| --- | --- | --- | --- | --- |
| 1 | **Predictor** | Use the Engine as a closed-loop forecaster. Given a falsifiable scenario, it identifies non-obvious strategic outcomes that reality later confirms. *The user's standing description: "the boring one."* | [Prediction Cleanroom](experiments/pathways/prediction_cleanroom.md) | ✅ Two confirmed blind validations (Powell, Musk-Altman partial). |
| 2 | **Envisioner** | Use the Engine to design strategy given a wish-shape (current state → wished-for state). Mirror Validation operates as the auditor instance against the Envisioner's output. *The user's description: "the more interesting one but requires more priming with the mere thing in the secondary notebook as an auditor and all that."* | [Genie Protocol](experiments/pathways/genie_protocol.md) (with [Offensive Architect](experiments/pathways/offensive_architect.md) as a stance variant) + [Mirror Validation](experiments/pathways/mirror_validation.md) | ✅ Genie demonstrated (Giant-Slayer). ✅ **Mirror Validation methodology validated end-to-end on the Amnesia case** ([run](experiments/runs/Mirror_Validation_Amnesia.md)) — auditor caught all four documented failure modes without coaching. |
| 3 | **Methodology** | The deep look at what the framework actually is, including conflicts and limits. Pattern attractor question, locus-of-intelligence question, reproducibility question. *Could yield a home-brewed runtime if NotebookLM turns out to be the wrong substrate.* | [`experiments/methodology_questions.md`](experiments/methodology_questions.md) | 🟡 Logged, pinned, not actively pursued. |
| 4 | **Pluggable** | The integration layer. Ganymede as a private analysis module other projects can call. *PrisonBreak is the first concrete validation case.* | [`integration/`](integration/) | 🟡 Design proposed; not yet built. |

The meta-methodology underlying silos 1 and 2 is the **Iterative Engine Vision** ([`concepts/Iterative_Engine_Vision.md`](concepts/Iterative_Engine_Vision.md)): the Engine is a piston, not a one-shot oracle. Single-pass output is idealistic; multi-stroke firing with human or contrast-notebook friction injection between strokes is what produces strategy that survives reality.

> Note on terminology: "pathway" and "silo" are not synonyms. A *silo* is one of these four research areas. A *pathway* is one technique used inside a silo. The Genie Protocol pathway lives inside the Envisioner silo; the Mirror Validation pathway also lives there as the auditor. Brainstorming items (autonomous-scouting Genie, "9D Assassin" scenarios, etc.) are sub-items inside whichever silo they belong to, never their own silo.

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
- **Mirror Validation, end-to-end** — the contrast notebook (`756e3683-f651-4381-b560-b13711b84ce6`) **now exists** with the same source corpus as the canonical Engine. Persona refresh + first audit run on the Amnesia known-wrong output is the pending work. See [`protocols/Mirror_Auditor_Persona.md`](protocols/Mirror_Auditor_Persona.md).
- **Pre-registered prediction methodology** — the Cleanroom pathway has demonstrated the technique but not yet locked in pre-registration discipline (timestamped predictions before validation runs).
- **Module integration surface** — design proposed in [`integration/`](integration/), including a concrete validation case for the user's PrisonBreak project. Adds session abstraction, WebSocket event stream, multi-stroke Iterative Engine, and pre-harvested Truth Packet ingestion to the existing orchestrator. Not yet built.
- **Genie autonomous-scouting variant** — preserved as a brainstorming-tier thought experiment in [`experiments/pathways/genie_protocol.md`](experiments/pathways/genie_protocol.md#variant-autonomous-scouting-brainstorming-tier-not-committed-work), not committed work.

## Hard guardrails

These are non-negotiable rules baked into the project. Every contributor — human or agent — must respect them.

1. **The 9D Chess Engine and Mirror Auditor are read-only.** Canonical Engine: `0a7d2672-009e-4995-9477-68c9b2fd9e54`. Mirror Auditor: `756e3683-f651-4381-b560-b13711b84ce6`. Both hard-coded in `notebooklm_service.py`. Only the named query methods (`query_chess_engine`, `query_mirror_auditor`) and the persona-config methods (`configure_chess_engine`, `configure_mirror_auditor`, applying known-good persona templates from `docs/protocols/`) may touch them. Never create, rename, or delete. The earlier validated runs were performed against legacy Engine `5967ce5d-f9eb-4f4e-b3e1-620f643d8390`, kept in code as `LEGACY_ENGINE_ID` for traceability.
2. **All NotebookLM API calls cooldown-gated.** Hard floor 8s between calls (Z-SPAN-recommended default), soft caps 20/hour and 100/day. Implemented in `_CooldownGate` in `notebooklm_service.py`. Don't bypass with direct `self.client.X` calls — always route through `NotebookLMService` methods. Full rationale and operator practices in [`protocols/Account_Safety.md`](protocols/Account_Safety.md).
3. **Manual approval before spawning notebooks.** PKI Oracles are created on demand, but never autonomously. The human approves each new oracle. This protects the Google account from ban risk and keeps the swarm curated. Enforced in code via the per-call shape of `create_oracle`.
4. **No browser-driven Gemini-Pro automation.** A previous experiment burned Pro queries by mis-firing keyboard events. The Cortex Clipboard exists specifically to keep the Gemini-Pro step a deliberate human paste action. *(Caveat: Gemini Pro is also explicitly excluded from the Prediction Cleanroom loop entirely — its only legitimate role is the post-hoc independent-research auditor.)*
5. **Surgical plain-language prompts to Oracles.** The Engine's internal jargon (DAI, ROEM, Horus Trap, etc.) does not survive contact with a research bot. The orchestrator translates jargon → plain English losslessly before any Oracle is invoked. Editorial summarization is forbidden — the orchestrator is a transparent pipe between Engine and Oracle, not an editor.
6. **Zero-degradation synthesis.** When Truth Packets come back from the Oracles, paste the *exact unmodified text* into the synthesis prompt. No summarization. No reordering. No cleanup. The Engine's resolution quality depends on the source-citation chain remaining intact.
7. **Holistic synthesis at the Engine.** Don't pre-frame Truth Packets with "find SDS only" or any goal-shaped instruction. Hand the Engine the authenticated facts and the original scenario, and let it run.

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
