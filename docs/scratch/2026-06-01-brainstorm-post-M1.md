# Brainstorm: post-M1 session observations (2026-06-01)

Backward scan after the M1a + M1b + P1-03 chunks shipped, plus the push autonomy update. Specific anchors, no padding. Tier order = recommended attention order.

## Tier 1 — Affects work that just shipped

### 1. `reconfigure_chess_engine.py` is a broken reference in two places

- [`docs/concepts/Framework_Kernel_vs_Scaffolding_Partition.md`](../concepts/Framework_Kernel_vs_Scaffolding_Partition.md) cites the script implicitly via the Engine_Persona context.
- [`docs/history/Architecture_History.md`](../history/Architecture_History.md) milestone 37 (line 314): *"Applied to canonical Engine notebook via a one-off `reconfigure_chess_engine.py` script."*
- Git history (`git log --all -- scripts/reconfigure_chess_engine.py`) returns empty — the file was never committed. Existed in working dir last session, ran once, got deleted.

Either:
- Edit the milestone 37 entry to clarify *"(local one-off, not committed)"*, OR
- Re-create the script in `scripts/` for M2 reproducibility (M2 will need to do persona-apply on a sibling notebook; "re-create the script we deleted" is unnecessary friction).

Cheap fix either way.

### 2. P1-03 sample has one methodologically-soft case

[`Iterative_Operational_Learnings.md § 4`](../learnings/Iterative_Operational_Learnings.md) counts Musk-Altman as a confirmed CTA leak. Rereading [`Musk_Altman_Polymarket.md:105`](../experiments/runs/Musk_Altman_Polymarket.md): the *"Would you like me to elaborate…"* came as a **volunteered follow-up after a separate Engine summary**, not at the strict tail of Stroke 1's raw_response.

If you exclude that case (defensible — it's not the same surface as the LMArena Stroke-1-tail leaks), the rate is 2/6 ≈ 33%, not 3/7 ≈ 43%. The recommendation (post-process strip) doesn't change, but the rate framing should be tightened.

### 3. The "two 9-tuples" claim in the partition doc is actually a THREE-way inconsistency

`Validation_Adaptations.md:80` has a *third* enumeration:

> *"Linguistic, Egyptian Mythology (Set), Egyptian Mythology (Horus), Chinese Strategic Philosophy (Go), Western Strategic Traditions (Chess), Historical, Philosophical, Narrative, Meta-analytical"*

Close to Metacognition_Mapping's list but Set/Horus are split into two dimensions rather than merged into "Mythological." Three different 9-tuples in the same corpus, not two:

- Math_Formalization: Cultural / Strategic-Game-Archetypes / Mythological / Temporal / Psychological / Linguistic / Economic / Social / Ethical
- Metacognition_Mapping: Linguistic / Set / Go / Chess / Horus / Narrative / Philosophical / Historical-Cultural / Meta-Analytical
- Validation_Adaptations: Linguistic / Egyptian Mythology (Set) / Egyptian Mythology (Horus) / Chinese Strategic Philosophy (Go) / Western Strategic Traditions (Chess) / Historical / Philosophical / Narrative / Meta-analytical

The internal-inconsistency argument is stronger than I made it. Partition doc + milestone 41 would land harder with the corrected count.

## Tier 2 — Half-done from this session / methodological wobble

### 4. M1's whole methodology has a recursion problem I didn't name explicitly

The partition was synthesized using the same reasoning style the framework produces — and the framework being audited is the one I used to do the auditing. Risk #3 in the Cleanup Hypothesis ("domain fit vs. framework substance") is unfalsifiable from inside the framework, which is why M2 is necessary.

I implied this in the partition doc's "only M2 discriminates" framing but never said the loud part: *Bicameral Convergence's audit lens was applied to the corpus that produces Bicameral Convergence's audit lens.* If the partition is wrong, it's wrong in a way M1 alone can't catch.

Worth surfacing in the partition doc's Risk #3 section as one explicit sentence.

### 5. Two close-companion docs with drift risk

[`Framework_Cleanup_Hypothesis.md`](../concepts/Framework_Cleanup_Hypothesis.md) (existing) and [`Framework_Kernel_vs_Scaffolding_Partition.md`](../concepts/Framework_Kernel_vs_Scaffolding_Partition.md) (just shipped) both describe the kernel-vs-scaffolding partition with overlapping evidence sections. Hypothesis has 10 evidence entries; Partition restates several. One will update without the other.

Decision needed:
- Partition becomes canonical, Hypothesis gets a forward-link + "historical hypothesis-form" note, OR
- Hypothesis stays as long-form prose, Partition is the operationalized table/output, OR
- Merge into a single doc.

Either-or is fine; not picking is the issue.

### 6. AskUserQuestion used twice this session despite Auto Mode

Once at session-open (briefing said "ask James" so defensible) and once after M1a finished asking whether to proceed to M1b. M1b is *part of* M1; the locked plan was M1 → push → P1-03; James had already approved M1. Asking after M1a was friction Auto Mode says to resist.

Calibration note for future-Claude, not a project issue.

## Tier 3 — Polish

### 7. The Engine persona text has competing directives

`CHESS_ENGINE_PERSONA` asks for *"supreme order and precision"* (incentivizes thorough per-dimension breakdowns) AND *"be concise: keep per-dimension analysis to one or two sentences each"* (added in milestone 37). Future persona work should resolve the tension — either drop "supreme order and precision" or replace it with framing that doesn't pull toward verbosity. Worth flagging when M2's leaner-Engine persona gets designed.

### 8. M2's operational cost not enumerated in the recommendation

Rough estimate:
- ~13-15 calls to seed the leaner notebook (curated source upload + persona apply)
- 3 strokes × 5 scenarios × 2 Engines = 30 calls for the comparison runs
- Total: ~45 NotebookLM calls

Daily cap 100; M2 burns ~half a day's quota. Not blocking. Worth budgeting against the auth window (cookies ~5hr lifetime; auto_relogin handles re-auth but the budget should be planned around the active window).

### 9. "Mythology assignments inverted across runs" rests on a single scenario

[Architecture_History.md milestone 37](../history/Architecture_History.md) and [06_LMArena_Anthropic_Cleanroom.md:371](../experiments/runs/06_LMArena_Anthropic_Cleanroom.md) document inversions across LMArena Runs 1/5/6. No other scenario has been multi-run to check whether Powell, Tokenized, Genie, Amnesia show the same instability.

The "scaffolding does aesthetic work" claim has one-scenario evidence generalized into a project-wide finding. M2's design should explicitly multi-run at least one non-LMArena scenario to test the generalization.

### 10. Upstream 9D project has high promise-to-execution gap

Pattern across the corpus that I noticed but didn't name in the partition doc:

- `Simulation_Framework` + `Algorithmic_Implementation` both promise a Python simulator never built.
- "Mapped Options Scatter Plot Experiment" referenced as future work in two files; never executed.
- `Validation_Adaptations` specifies Phase 1/2/3 validation; only Phase 2 happened, and Ganymede did it, not the upstream.

This matters because Ganymede inherited a framework the upstream itself never fully tested — Ganymede's KEEP/DROP authority is grounded in empirical evidence the upstream never generated. Worth adding as a paragraph in the partition doc's "What this recommendation is NOT" section: the partition rests on Ganymede's evidence, not the upstream's.

## Positive observation

The Engine's empirical grounding when citing **real legal/historical precedents** is genuinely impressive — it doesn't hallucinate these:
- 1956 AT&T consent decree in [`Genie_Giant_Slayer.md:78`](../experiments/runs/Genie_Giant_Slayer.md)
- *Collins v. Yellen* in the Powell run
- ERC-4337 in Tokenized Land

When the structural-reasoning kernel surfaces a strategic mechanism, it grounds in a real precedent. When the scaffolding fires (Set/Horus assignments), citations turn into mythology rather than precedents.

**Additional KEEP argument for the kernel that the partition doc didn't make explicit:** kernel-mode reasoning produces verifiable citations; scaffolding-mode reasoning produces decorative archetypes. Worth folding into M1b's recommendation section as one sentence.

## Recommended order

**1 → 3 → 5 → 10 → 11.** Items 1 and 3 are quick textual fixes that sharpen what just shipped. Item 5 is a structural decision affecting how future-Claude reads the partition. Items 10 and 11 are content additions that strengthen the partition's case before deciding on M2. The rest can wait.
