---
title: "Framework Cleanup Hypothesis — Kernel vs. Scaffolding"
type: "concept"
status: "hypothesis"
tags: ["methodology", "framework-limits", "silo-3", "concepts"]
color_id: "5"
---

# Framework Cleanup Hypothesis — Kernel vs. Scaffolding

> **Status:** Hypothesis-tier concept doc. Captured 2026-05-25 during the first-live-Dispatcher-spin session, in response to the operator's direct question: *"do you think that the actual framework that we're utilizing is just simply wrong, or that that's what's poisoning everything else?"*
>
> Lives in [Methodology Silo 3](../experiments/methodology_questions.md). Operationalizes [Q1 diagnosis #3](../experiments/methodology_questions.md#q1-the-structural-waiver-pattern-attractor) — *"the framework itself has the bias"* — with a kernel-vs-scaffolding partition and a strip-down test plan. Not yet experimentally validated.

## The hypothesis

The 9D framework, as inherited from the upstream [9D-Chess research project](https://github.com/anitacigawet/9D-Chess), has two distinct components doing different work:

1. **A structural-reasoning kernel** — DAI/DAP asymmetry, Strategic Lasso, Incomprehensible Move, SDS, the multi-actor structural-funnel claim, the dimensional-asymmetry-creates-vulnerability theorem. This describes genuine patterns in strategic situations and **has been validated** on Powell, Tokenized Land, and Genie Giant-Slayer. It is doing real work.

2. **An aesthetic / theatrical scaffolding** — the 9 *named* dimensions (Egyptian mythology layer with Set/Horus, Chess/Go Western/Eastern strategy binary, narrative three-act structure, philosophical tensions, etc.). This is the rich vocabulary the Engine deploys. It is **not** load-bearing for the structural-reasoning kernel; it is ornamentation that the model is incentivized to apply systematically.

The hypothesis: **the scaffolding is what generates the systematic failure modes the Mirror Auditor catches.** Stripping the scaffolding while preserving the kernel would produce a leaner framework with fewer false-positive narratives and similar (or improved) true-positive identification.

## Evidence

### Empirical (from session observations 2026-05-25)

1. **The Mirror Auditor's four fault categories appear systematically, not randomly.** Pattern-Matching, Confidence-Evidence Gaps, Dimensional Greeds, Rigidity Errors (per [`../protocols/Mirror_Auditor_Persona.md`](../protocols/Mirror_Auditor_Persona.md)) triggered on both the [Amnesia validation](../experiments/runs/Mirror_Validation_Amnesia.md) and both [LMArena runs](../experiments/runs/06_LMArena_Anthropic_Cleanroom.md) in this session. These are not general LLM failure modes — they are predictable failure modes of a model deploying a rich aesthetic vocabulary across situations that don't all fit.

2. **Stroke 1 outputs lean hard on the mythological / strategy-binary layer.** Both LMArena Strokes 1 opened with Egyptian mythology (Set/Horus) and Chess/Go assignments. Both made aesthetically symmetrical narratives (Anthropic = Chess/Horus, Google = Set/Go) that the Auditor correctly flagged as false-binary in BOTH runs. The Auditor's exact catch in Run 2: *"selects an aesthetically symmetrical narrative over realistic corporate behavior, ignoring the fact that both multi-billion-dollar entities simultaneously utilize long-term resource accumulation and direct, tactical product releases."* This is the framework's STRUCTURE incentivizing the failure, not the model being lazy.

3. **ROEM is the most aesthetically-loaded primitive and the one that fails hardest outside strategic-game contexts.** It claims observation by an aware actor "collapses the observed actor's possibility space." Real in interactive strategic games. Category error when applied to passive market bettors observing a leaderboard (which both LMArena Strokes 1 did). The Engine is faithfully applying ROEM's definition — the definition is overgeneralized to non-interactive observation contexts.

4. **The [GLOSSARY "Vocabulary register" section](../GLOSSARY.md#vocabulary-register) exists precisely because of this mismatch.** The chess-origin primitives — opponent, target, manipulation, lasso — read awkwardly in Cleanroom / Genie / Mirror contexts. The operator has already done patching that acknowledges the framework's vocabulary wasn't designed for the pathways it's now used in. That patching is downstream of the original mismatch.

5. **NotebookLM's input-size cap (root-caused 2026-05-25) is exacerbated by Engine verbosity.** The Engine's Stroke 1 outputs run 4,500–5,500 chars, flirting with the ~5,100–6,000 char silent-rejection cap. A leaner framework producing shorter Stroke 1s would naturally avoid the cap. The infrastructure issue and the framework issue **compose** — cleanup helps both. See `project_notebooklm_input_cap` in memory + [Run 06's third-run diagnosis](../experiments/runs/06_LMArena_Anthropic_Cleanroom.md).

10. **The Engine processes dimensions statically rather than updating cross-dimension state — second empirical datapoint.** The [Powell Bridge Null Test (2026-05-31)](../experiments/runs/Powell_Bridge_Null_Test.md)'s Bridge 1 catch (DOJ probe explicitly documented as closed in Silo D8 while the Engine's Strategic Lasso treated it as ongoing) is the cleanest single-case instance of this pattern observed so far. The Bridge's own likely-reason hypothesis names it explicitly: *"The Engine pattern-matched the DOJ probe as a static structural vulnerability in one dimension, failing to update its temporal state based on the chronological event trigger located in another."* Reinforces the Mirror Auditor's "Rigidity Errors" category and the kernel-vs-scaffolding partition's central claim that the framework's dimensional structure produces predictable failure modes.

### Architectural

6. **The Mirror Auditor / Connection Bridge / Bicameral Convergence architecture exists as compensation for framework failures.** [`../concepts/Bicameral_Convergence.md`](Bicameral_Convergence.md) is a closed-loop two-mirror architecture whose purpose is to bound the framework's tendency to generate unfalsifiable narratives. That's a lot of architecture spent on QUALITY CONTROL for framework outputs. A tighter framework would reduce the cleanup needed; the architecture would shift from systematic-failure catching to edge-case catching, which is a better use of its cost.

7. **All persona-override attempts have failed when fighting the corpus.** Variant-1 (Nuance Prime), Variant-2 (Rule Zero), the [kami persona experiment](Persona_Expansion_Experiment.md) — all failed because NotebookLM's corpus dominance overwhelms persona text. The [Connection Bridge](../protocols/Connection_Bridge_Persona.md) succeeded because it leveraged the corpus rather than fighting it. Same lesson: **framework cleanup must happen at the corpus level**, not via persona text trying to override the corpus.

### Conserved (what the framework gets right)

8. **The Powell + Tokenized Land wins are not accidents.** DAI asymmetry, Strategic Lasso, Incomprehensible Move, SDS describe real patterns in multi-actor structural situations. Powell's *Collins v. Yellen* demotion pathway IS a Strategic Lasso. Tokenized Land's ERC-4337 + sovereign immunity carve-out IS an Incomprehensible Move. These primitives — the kernel — are doing real work and are explicitly the things to PRESERVE.

9. **The structural-reasoning shape generalizes to bounded domains beyond strategic games.** The [Palantir-for-Ganymede brainstorming doc](../brainstorming/Palantir_For_Ganymede.md) identifies non-sports domains where the framework's kernel shape would fit (single-company strategic dossier, legal/regulatory case prediction, corporate-event prediction). The shape works; the scaffolding mis-fires.

## Proposed approach

**Don't rewrite. Strip down.** Full rewrites risk losing the kernel that's been validated.

1. **Read [`../foundations/`](../foundations/) deeply** — the 13 imported documents that ARE the corpus the Engine grounds in. Identify each primitive: is it load-bearing for structural reasoning, or aesthetic scaffolding?

2. **Partition explicitly:**
   - **Kernel (KEEP):** DAI/DAP, Strategic Lasso, Incomprehensible Move, SDS, the multi-actor structural-funnel claim, the dimensional-asymmetry-creates-vulnerability theorem, ROEM **scoped to interactive strategic situations only**.
   - **Scaffolding (DROP or DE-EMPHASIZE):** the 9 *named* dimensions (especially the Egyptian mythology layer with Set/Horus), Chess/Go Western/Eastern strategy binary, narrative three-act structure, philosophical tensions, the more theatrical ROEM framings.

3. **Draft a leaner corpus** keeping the kernel and dropping or de-emphasizing the scaffolding. Critical constraint: leave enough that NotebookLM still has structural-reasoning material to ground in. Too sparse and the model loses the capability altogether — the kernel is what the model NEEDS, the scaffolding is what the model is INCENTIVIZED to deploy.

4. **Build a side-by-side notebook** — same canonical persona, leaner corpus. Run Powell, Tokenized Land, Amnesia, Genie Giant-Slayer, and LMArena on BOTH the current canonical Engine and the leaner one.

5. **Evaluation criteria:**
   - **PRESERVE:** Powell-class wins (does leaner version still identify *Collins v. Yellen*-class structural mechanisms?). Genie Giant-Slayer (does it still produce categorically different output than general-purpose LLMs?). Tokenized Land (does it still surface ERC-4337 + sovereign-immunity-class Incomprehensible Moves?).
   - **REDUCE:** Amnesia / LMArena-style dimensional-greed failures (does leaner version produce more empirically-grounded Stroke 1s? Fewer Egyptian-mythology category assignments? Less ROEM-on-passive-observers errors?).
   - **NEUTRAL:** Stroke 1 length should drop (resolving the NotebookLM input-size cap collisions as a free side effect).

6. **Ship the leaner notebook as a candidate canonical Engine** if it meets the criteria. Keep the current Engine alive as `LEGACY_KERNEL_PLUS_SCAFFOLDING_ENGINE_ID` for traceability against historical runs (mirrors the existing `LEGACY_ENGINE_ID` pattern).

## Risks

1. **Stripping too aggressively breaks the wins.** If we strip the scaffolding too hard, the Engine loses the structural-reasoning capability entirely. Side-by-side testing on validated runs is the mitigation.

2. **The scaffolding might be load-bearing in ways the outputs don't reveal.** Possible: the 9 named dimensions might function as a "scratchpad" the Engine uses to reach the right structural insights, even when the user-visible reasoning seems independent. The kernel might not survive without the scaffolding's reasoning aid. Empirical question.

3. **Domain fit may be the real issue, not framework substance.** It's possible the framework is fine when applied to multi-actor structural-funnel situations (Powell, Tokenized) and wrong when applied to others (Amnesia, LMArena). In that case, the right fix is a "domain applicability" gate at the orchestrator level — not framework cleanup. Worth ruling out empirically before committing to framework rewrite.

4. **Notebooks are stateful.** A leaner notebook needs the corpus re-uploaded; this is a substantial operational lift, not a quick experiment. The side-by-side test design needs careful planning.

5. **The "Mirror Auditor's job" might change.** If framework failures decrease, the Auditor needs less cleanup work. That's a good thing — but it changes what the Auditor is FOR. May need persona revision so it doesn't manufacture findings when the input is already clean.

## Relationship to other workstreams

| Workstream | Relationship |
| --- | --- |
| [Methodology Silo 3](../experiments/methodology_questions.md) | This IS Silo 3 work. Specifically, it operationalizes [Q1 diagnosis #3](../experiments/methodology_questions.md#q1-the-structural-waiver-pattern-attractor) ("the framework itself has the bias") with a concrete partition + test plan. |
| `project_notebooklm_input_cap` (memory) | A leaner framework producing shorter outputs would naturally avoid the cap. Workstreams compose — verbosity reduction at the source is the cleanest fix for both. |
| [Bicameral Convergence Levels 2-3](../concepts/Bicameral_Convergence.md) | Pending work that depends on the iterative loop functioning correctly. Framework cleanup may reduce the audit's workload but doesn't replace the architecture — it makes the architecture more efficient. |
| [Palantir-for-Ganymede brainstorm](../brainstorming/Palantir_For_Ganymede.md) | Aligned. A leaner framework would generalize more cleanly to bounded domains beyond strategic-game scenarios. |
| [Engine_Persona.md](../protocols/Engine_Persona.md) | Persona text changes are NOT the right lever — corpus dominance overwhelms persona. The cleanup has to happen at the corpus level. (Persona-text tightening for *brevity* and *CTA suppression* is a separate small fix that's been shipped 2026-05-25 to address the input-cap issue, not framework substance.) |

## Open questions

1. Is the kernel-vs-scaffolding partition genuinely clean, or are they tangled? Won't know until the deep read of `docs/foundations/`.
2. Does the Engine's reasoning quality depend on the scaffolding in ways the outputs don't reveal? (Risk #2 above — needs empirical answer.)
3. How would Genie Giant-Slayer fare on a leaner framework? It's the Genie-pathway win; the framework's domain there is different from Cleanroom's. Include in the side-by-side test.
4. Does the operator want to maintain TWO canonical Engines (current + leaner) indefinitely, or does the leaner one replace the current?
5. Does the cleanup change what the [Connection Bridge](../protocols/Connection_Bridge_Persona.md) catches? If the Bridge's missed-bridges are scaffolding-dependent, the Bridge's output discipline may need re-validation on the leaner corpus.

## Next concrete step

**Read `docs/foundations/` end-to-end** and produce an explicit kernel-vs-scaffolding partition document. Multi-hour focused-session work. Output: an annotated table of every primitive in the foundations corpus with KEEP / DROP / DE-EMPHASIZE marking + rationale. This is the prerequisite for any actual corpus rewrite work.

## Status

**Hypothesis-tier.** Captured 2026-05-25 in response to the operator's direct question during the first-live-Dispatcher session. The hypothesis's central claim (scaffolding generates the systematic Auditor catches) is grounded in observed Mirror Auditor patterns across the Amnesia + two LMArena runs, but the kernel-vs-scaffolding partition itself has not been done — the foundations corpus deep-read is the next step. Test plan and evaluation criteria specified above.

## Related

- [`../experiments/methodology_questions.md`](../experiments/methodology_questions.md) — Silo 3 index. Q1 specifically asks the question this doc operationalizes.
- [`../experiments/runs/06_LMArena_Anthropic_Cleanroom.md`](../experiments/runs/06_LMArena_Anthropic_Cleanroom.md) — the run that triggered this framing (Auditor's dimensional-greed catch on Stroke 1 + the size-cap diagnostic).
- [`../brainstorming/Palantir_For_Ganymede.md`](../brainstorming/Palantir_For_Ganymede.md) — sibling brainstorming doc proposing bounded-domain applications the cleanup would help.
- [`../concepts/Bicameral_Convergence.md`](Bicameral_Convergence.md) — the audit-architecture this critique is partly explaining (architecture as compensation for framework substance).
- [`../protocols/Mirror_Auditor_Persona.md`](../protocols/Mirror_Auditor_Persona.md) — the four-fault-category enumeration that grounds the empirical observation.
- [`../protocols/Engine_Persona.md`](../protocols/Engine_Persona.md) — current Engine persona (small; the corpus is the locus of behaviour, not the persona).
- [`../foundations/`](../foundations/) — the actual corpus this analysis is about. Deep-read pending.
- [`../concepts/Persona_Expansion_Experiment.md`](Persona_Expansion_Experiment.md) — the persona-design methodology lesson (output discipline beats vocabulary axioms) that informs why persona-text changes alone won't fix this; corpus-level cleanup is required.
