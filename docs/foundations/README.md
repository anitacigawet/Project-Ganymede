# Foundations

The upstream theoretical material that the [9D-Chess research project](https://github.com/anitacigawet/9D-Chess) produced — imported here as reference substrate for [[Project Ganymede]]. These docs are not Project Ganymede's own work; they are the *prior* theoretical apparatus this project operationalizes.

Distinct from [`../concepts/`](../concepts/) (Project Ganymede's own thinking artifacts) and [`../protocols/`](../protocols/) (Project Ganymede's operational discipline). Foundations is the **upstream substrate**.

## What's here

| File | What it is |
| --- | --- |
| `9D_Framework_Whitepaper.md` | The headline framing of the 9D Framework. Linguistic / mythological / strategic / philosophical layers; multidimensional emergence; contrast with binary-logic systems. The most accessible single doc. |
| `9D_Framework_Algorithmic_Implementation.md` | The most operational of the framework docs. How the 9D logic gets implemented as algorithm. |
| `9D_Framework_Simulation_Framework.md` | How to simulate scenarios in the 9D Framework. Closer to the Project Ganymede operational layer than the others. |
| `9D_Framework_Validation_Adaptations.md` | Methodology for validating outputs of 9D analysis. Pre-cursor to Project Ganymede's [[Mirror Validation]] work. |
| `9D_Framework_Metacognition_Mapping.md` | The 8 Pillars of Metacognition mapped onto the 9D framework. Explicit dimensional vocabulary. |
| `9D_Framework_Metacognition_Applications.md` | Applied metacognitive analysis using the framework. |
| `Comprehensive_Multidimensional_Analysis.md` | Worked-example analysis demonstrating the framework's full application. |
| `Mathematical_Formalization_9D_ROEM.md` | The formal mathematical layer underlying ROEM. Set-theoretic + measure-theoretic apparatus. |
| `ROEM_Formal_Model.md` | The Reverse Observer Effect Model in its formal articulation. Axioms, postulates, components. The canonical theoretical doc for ROEM. |
| `ROEM_9D_Metacognition_Integration.md` | How ROEM, the 9D framework, and the 8 Pillars of Metacognition fit together. |
| `reverse_observer_effect_analysis.md` | Applied analysis using ROEM. |
| `Vulnerabilities_of_Binary_Systems.md` | The argument for why limited-dimension systems are exploitable by 9D actors. The motivation for the framework's "conceptual zero-day" framing. |
| `Neuro-Linguistic Programming & VR via the 8 Pillars of Metacognition.pdf` | Long-form treatment of the 8 Pillars via NLP and VR. The deepest cut of the metacognitive layer. |

## A note on vocabulary

These foundations docs are upstream 9D-Chess content. The original project was built around a zero-sum two-player chess metaphor, so the vocabulary throughout is adversarial: *opponent*, *target*, *strategic manipulation*, *strike*, *funnel into disadvantageous states*.

Project Ganymede applies the same framework across four pathways, only one of which ([Offensive Architect](../experiments/pathways/offensive_architect.md)) is genuinely adversarial. The others — [Cleanroom](../experiments/pathways/prediction_cleanroom.md) (passive observation), [Genie](../experiments/pathways/genie_protocol.md) (pathfinding), [Mirror Validation](../experiments/pathways/mirror_validation.md) (self-audit) — use the *same math* with the *same primitives* but the chess vocabulary reads strangely. For the neutral framing of the same primitives, see the [Vocabulary register section](../GLOSSARY.md#vocabulary-register) of GLOSSARY.md.

Don't try to neutralise these source files. They are an upstream snapshot and a reproducibility artifact (see "Why these are committed to the repo" below). The reframing belongs at the project's authored-docs layer, not here — editing these would break the snapshot relationship with the [upstream 9D-Chess research project](https://github.com/anitacigawet/9D-Chess).

## How Project Ganymede uses these

The canonical [[9D Chess Engine]] notebook (`0a7d2672-...`) is grounded in this corpus. When the Engine produces a [[Strategic Lasso]] or names an [[Incomprehensible Move]], the vocabulary and reasoning are drawing from these docs.

The [[Engine Persona]] is intentionally terse (two sentences) precisely because the corpus does the heavy semantic lifting. The persona signals the role; the corpus supplies the substance.

## Why these are committed to the repo

Two reasons:

1. **Reproducibility.** The Engine notebook is a particular NotebookLM with a particular corpus. If that notebook is ever lost (account flagged, accidental deletion, NotebookLM service change), the corpus needs to be reconstructable. These files are how.
2. **Versioned theoretical reference.** As the upstream 9D-Chess project evolves, this folder is a snapshot — the version of the framework Project Ganymede operationalized at the time it was imported. Future divergence between Project Ganymede's apparatus and the upstream's is auditable against this snapshot.

## When to update this folder

When the upstream 9D-Chess project lands a substantive theoretical update *and* Project Ganymede decides to incorporate the update. Re-imports should land as their own commit with a note in [[Architecture History]] documenting what changed.

Don't update this folder casually. Each import is also a re-grounding of the [[9D Chess Engine]] notebook (or a new notebook with the new corpus), which is a real architectural decision.

## Reading order if you're new to the framework

1. **`9D_Framework_Whitepaper.md`** — start here for the framing.
2. **`Vulnerabilities_of_Binary_Systems.md`** — short and motivates *why* the framework matters.
3. **`ROEM_Formal_Model.md`** — the theoretical core. ROEM is what makes the [[Convergence Theorem]] operational.
4. **`9D_Framework_Algorithmic_Implementation.md`** — the operational layer. How the framework gets executed.
5. The metacognition / NLP / VR docs only if you want the deepest cut.

The rest are worked-example or applied docs that flesh out the framework once you have the foundations.
