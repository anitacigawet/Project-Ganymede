# Open Methodology Questions

A standing log of methodology-level questions that affect multiple pathways and don't resolve into a single experiment. These are explicitly *open* — they are not roadmap items, they are unresolved tensions in the project's epistemics that we should remain honest about.

---

## Q1: The Structural-Waiver Pattern Attractor

**Observation.** Across multiple high-fidelity Cleanroom runs (Powell, Tokenized Land, Genie Giant-Slayer, the abstract Conglomerate offensive demo), the Engine reaches for the same structural-template resolution:

1. Target perceives a positional win or rebirth (the Bait).
2. The win contains a structural waiver of the target's prior-existing protections (the Lasso) — typically via a technical-legal vehicle (smart contract, designation revocation, royalty-free dissemination, ledger migration).
3. Resolution is **Functional Obsolescence**: target physically persists but operational/economic agency is captured.

The pattern was named differently each time (Shadow Fed, Ghost Ranger, Hollowing Out, Ideological Infrastructure capture) but the underlying mechanic is identical.

**The question.** Is this:
- (a) A real generalizable pattern in modern strategic landscapes — i.e. structural-waiver-via-technical-veil really *is* the dominant mode of contemporary strategic capture, and the Engine is correctly identifying it across domains?
- (b) Pattern-matching off the Engine's own previous outputs (or off the corpus that trained whatever the Engine sits on) — i.e. once the Engine produces this pattern once, it has a strong attractor toward producing it again, regardless of whether a given scenario actually fits?
- (c) Some combination of both?

**Why this matters.** If (a), the Engine is genuinely doing strategic-physics-grade work and the pattern is its discovery. If (b), the pattern is an artifact and the Engine's apparent fluency is partly memorization. The two have very different implications for trusting the Engine on novel scenarios.

**The user's framing of the deeper philosophical issue.** *"That would be a methodology question. I don't know how to approach that, though. I think that may be a philosophical question of actually trusting the NotebookLM to properly conduct the analysis compared to an AI that is actually fine-tuned for this model of the 9D thing. Although I don't even know how to really do that — the NotebookLM is my best approach for that."*

The unstated tension: **the Engine is a NotebookLM with a custom prompt**, not a model fine-tuned on the 9D framework. The 9D framework is the engine's *priming context*, not its weights. We are inferring strategic-physics-grade reasoning from in-context behavior. The same Engine could in principle be instantiated on a different base model and produce different results from the same prompt — we have no way to test whether the framework or the base model is doing the work.

**What might discriminate (a) from (b).** Scenarios where the structural-waiver template is *implausible* — pure information goods, pre-modern social conflicts, individual psychology, biological systems, scenarios with no contractual or legal substrate. If the Engine still reaches for "they perceive a win that contains a structural waiver of their immunity," that's evidence for (b). If it reaches for genuinely different structural templates that fit the new domain, that's evidence for (a).

**Status.** Logged and **explicitly pinned** by the user — not blocking any current work, and not actively being investigated yet. The pin is intentional: pursuing this question now (before the project has more validated runs) risks treating "the model is wrong" and "the substrate is wrong" as the same answer.

### The user's framing of the pin (preserved for when this is revisited)

> *"In the event that we do deduce that there is some pattern that it's attracted to by running that simulation in the notebook, the idea and the concept does not mean it's flawed. It simply means that using the notebook as the actual simulation for that is just not feasible and it will have to do some other closed home-brewed AI system built with the 9D Chess theory and all that to simulate it."*

There are at least three possible diagnoses for the pattern attractor, and they have very different implications:

1. **The substrate is the problem.** NotebookLM's behavior — its prompt-grounded RAG, its specific base model, its Studio-output bias — is what's producing the pattern attraction. The 9D framework itself is fine; we are running it on the wrong vehicle. *Fix: build a home-brewed runtime (fine-tuned model, custom orchestration, deterministic agent stack) that implements the 9D framework directly.*
2. **Our usage is the problem.** The Genie Prime / Dream State priming, the Surgical Middleman translation, the synthesis prompt — some part of the *operator's* methodology is leaking the attractor in. *Fix: re-run the same scenario with a substantially different invocation pattern and see if the attractor persists.*
3. **The framework itself has the bias.** The 9D framework as documented (in the upstream 9D-Chess repo) actually does converge on this template across the kinds of scenarios we've been running. *Fix: revisit the framework axioms with the upstream theoretical material, identify whether the convergence is principled or accidental.*

The user's stated preference: don't act on any of these until we have substantially more runs to argue from. **When this question is revisited, the next-action assumption is (1) — build a home-brewed runtime — pending an in-depth re-read of the 9D-Chess foundation documentation.**

The user has explicitly licensed Claude (the project manager going forward) to make this assessment when the time comes: *"You can actually analyze the documentation of it in depth and then make your own assessment so if you think maybe you could come up with your own home-brew solution or we could build an AI thing — I'm not sure."*

Cross-reference: the upstream theoretical project at [github.com/anitacigawet/9D-Chess](https://github.com/anitacigawet/9D-Chess) is where that re-read would start.

---

## Q2: Reproducibility without preserved notebook IDs

**Observation.** All Cleanroom runs to date were produced via NotebookLM Oracle notebooks that have either been deleted or whose state has drifted. The Truth Packets exist in run records as *text*, but the original Oracle notebooks (and the specific Deep Research source corpora they harvested) are no longer accessible.

**The implication.** A "reproducible run" in the current methodology is reproducible in terms of *prompts and intermediate outputs*, not in terms of *running the same computation again*. If somebody else tried to reproduce the Powell run using the prompts in `Powell_Cleanroom/`, they would re-run the Genie Prime against the same 9D Chess Engine notebook (still alive), but they would have to create *new* Oracle notebooks and run *new* Deep Research sessions — likely surfacing different sources and different exact citations, since web content and NotebookLM's research engine both drift over time.

**What this means for blind-validation claims.** It bounds them. Powell remains a strong validation because the Engine's output (Demotion via *Collins v. Yellen* / Shadow Fed) is preserved in text and the audit confirmation is preserved in text. But strict computational reproducibility is impossible — the Oracle stack is non-deterministic and ephemeral.

**Possible mitigations.**
- Snapshot raw Oracle outputs (with citations intact) to disk at extraction time.
- For high-stakes runs, archive the actual source documents the Oracles imported.
- Adopt pre-registration discipline so the *sequencing* (prediction first, validation second) is timestamp-verifiable even if the underlying computation isn't replayable.

**Status.** Logged. The pre-registration discipline mitigation is what the [Prediction Cleanroom pathway](pathways/prediction_cleanroom.md#open-methodology-problems) flags as the next-run requirement.

---

## Q3: The Engine's locus of intelligence

**Observation.** The 9D Chess Engine is one specific NotebookLM (`5967ce5d-f9eb-4f4e-b3e1-620f643d8390`) with one custom prompt the user authored offline. The custom prompt is *not* in this repo. We have no copy of it. We treat the Engine as a black box.

**The questions this raises.**
- If Google deletes that notebook, can the project be reconstituted? Currently: no, not without recovering the prompt.
- Is the framework portable? If we instantiated the same prompt on a different base model (Claude, GPT, etc.), would we get the same quality of output? We don't know.
- Is the Engine's apparent reasoning a property of (the prompt × the base model), or of the prompt alone? If we can't separate these, we can't make reliable claims about what the framework adds.

**Mitigations.**
- Export the Engine's custom prompt and commit it to the repo (or to a private-but-redundant location). The user authored it; the user has it.
- Optionally instantiate a mirror Engine on a different base model to compare outputs on the same Genie Prime + scenario. This is a controlled-experiment variant of the Mirror Validation pathway.

**Status.** Logged. Not blocking, but trivially fixable for the export-the-prompt step. The cross-base-model experiment is a longer-term ambition.

---

## Q4: What "module integration" looks like in practice

**Observation.** The project's stated north star (per [`../OVERVIEW.md`](../OVERVIEW.md#north-star-module-not-service)) is to plug into the user's other projects as a private analysis module. We have not yet defined what that integration *looks like* — what API the consuming projects call, what they pass in, what they get back.

**Open questions.**
- Synchronous (call → wait → resolution) or asynchronous (kick off → poll for status)? Most ULL runs take many minutes; sync probably doesn't fit.
- One scenario per call, or persistent session that supports Iterative Engine multi-stroke conversations?
- What is the consumer's natural input format? GSS-shaped JSON? Free-text scenarios? Structured (target, objective, constraints)?
- What does the consumer get back — full Resolution text, structured Lasso/IM extraction, or a callback when each stroke lands?

**Status.** Logged. Will need to be answered before any actual module integration can ship. Probably worth a small spike on one of the user's existing projects to see what the natural shape of the integration is, rather than guessing in the abstract.

---

## How to add to this log

Methodology questions go here when they:
- Affect multiple pathways or runs (not pathway-specific — those go in the pathway doc).
- Are not blocking immediate work but should remain visible.
- Have no clean resolution path the project is committed to.

When a question is closed (resolved or definitively shelved), move it from "Status: Logged" to a closed section with the resolution recorded. We don't delete questions — closed questions are part of the project's epistemic history.
