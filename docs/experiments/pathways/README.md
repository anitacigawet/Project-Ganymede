---
title: "Active Research Pathways"
type: "cluster-head"
status: "active"
tags: ["pathway", "experiments", "cluster-head"]
color_id: "3"
---

# Active Research Pathways

Each pathway is a hypothesis + a method + a success criterion. Pathways are not products — they are research lines we are actively iterating on. A scenario run lives in `../runs/`; a pathway is the larger experimental program that scenario was sampling from.

Currently active:

| Pathway | What it tests | Status |
| --- | --- | --- |
| [`prediction_cleanroom.md`](prediction_cleanroom.md) | Can the Engine, in a Dream-State and fed only authenticated Truth Packets via no-Gemini-contamination, predict non-obvious strategic outcomes that real-world reality later confirms? | ✅ Two confirmed blind validations (Powell, Musk-Altman). Reproducibility methodology pending. |
| [`mirror_validation.md`](mirror_validation.md) | Can the Engine catch its own rigidity errors when a second instance reviews its output for faults? Does engine-self-modeling-as-parameter reduce the "correct math, infeasible reality" failure mode? | ✅ Validated end-to-end on the Amnesia case 2026-05-06 ([run record](../runs/Mirror_Validation_Amnesia.md)) — auditor caught all four documented failure modes without coaching. False-positive test (Powell-sound), Stroke-3 close-the-loop, and generalisation beyond Amnesia 🟡 pending. Companion architecture (Connection Bridge as orthogonal audit lens) shipped 2026-05-22 — see [`../../concepts/Bicameral_Convergence.md`](../../concepts/Bicameral_Convergence.md). |
| [`offensive_architect.md`](offensive_architect.md) | Stance shift — the Engine designs the funnel against a target scenario instead of auditing one. Can it productively find attack-surface in a target's strategic logic? | ✅ Concept demonstrated (Conglomerate / Power Play scenarios). Not yet applied to a real target. |
| [`genie_protocol.md`](genie_protocol.md) | Wish-fulfillment pathfinding — given (current state, wished-for state), can the Engine design the *Inadvertent Path* from one to the other? | ✅ One full demonstration (Zero-Budget Giant-Slayer → "release as ideological infrastructure"). Generalization pending. |

## The meta-methodology underlying all four

All four pathways operate inside the **Iterative Engine Vision**: the Engine is a piston, not a one-shot oracle. A single pass produces *idealistic / rigid* output that maps the laser path on one side of the box. The full engine fires in three strokes:

- **Stroke 1 — Thesis.** Raw single-pass output. Mathematically clean, often humanly absurd.
- **Stroke 2 — Antithesis.** Human/orchestrator injects friction or asks the Engine to red-team itself. The Engine identifies how its own Stroke-1 strategy could be broken — typically by the opponent's "structural adaptation" or by exogenous shocks.
- **Stroke 3 — Synthesis.** The Engine finds the move that survives the Antithesis. This is the strategy you actually take to the bank.

See [`../../concepts/Iterative_Engine_Vision.md`](../../concepts/Iterative_Engine_Vision.md) for the full philosophy.

## What "active" means here

These are pathways the project is actively iterating on. Other ideas surfaced during brainstorming (museum, SaaS, mediator, blind-spot auditor, etc.) are preserved in [`../../visions/`](../../visions/) and [`../../brainstorming/`](../../brainstorming/) as future possibilities. None of those are committed to.
