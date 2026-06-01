# M1 — Foundations corpus deep-read session notes

**Status:** M1a complete (2026-06-01) — all 14 files tagged. M1b synthesis pending.
**Started:** 2026-05-31
**M1a closed:** 2026-06-01
**Owner:** Claude (Autopilot Protocol, M1 chunk of TASKS.md)
**Resumption note:** if this file exists at session-open and the
"completed file checklist" below is partial, resume the deep-read from
the first unchecked file. Each per-file section is self-contained;
nothing depends on chronological reading order.

## M1a → M1b handoff — cross-file findings preview

Ten observations that span multiple files and will be load-bearing
when M1b drafts the canonical partition doc at
`docs/concepts/Framework_Kernel_vs_Scaffolding_Partition.md`:

1. **The kernel is concentrated in `Mathematical_Formalization_9D_ROEM.md`.**
   Its section 2.1 is the ONE scaffolding spot (the labeled 9-tuple) in an
   otherwise-kernel file. Surgical replacement of section 2.1 with abstract
   metric subspaces leaves every axiom, principle, theorem, and corollary
   intact.

2. **The 9D corpus is internally inconsistent on what the 9 dimensions ARE.**
   `Mathematical_Formalization` lists Cultural / Strategic-Game-Archetypes /
   Mythological / Temporal / Psychological / Linguistic / Economic / Social /
   Ethical. `Metacognition_Mapping` lists Linguistic / Set / Go / Chess /
   Horus / Narrative / Philosophical / Historical-Cultural / Meta-Analytical.
   Two different 9-tuples in the same corpus. If the labels were
   load-bearing, internal consistency would be enforced. They aren't.

3. **`Validation_Adaptations.md` section 3 IS the kernel-vs-scaffolding
   partition stated by the upstream itself.** Quote: *"While the core
   principles remain constant, the specific manifestation of dimensions,
   the nature of strategic interactions, and the characteristics of agents
   will vary significantly across fields such as finance, geopolitics, or
   social dynamics."* This makes the hypothesis a literal application of
   the upstream's prescribed methodology, not a deviation.

4. **The metacognition import is already a stripping decision made by the
   upstream.** The source PDF's full schema is 8 Pillars × 8 Layers of
   Consciousness × 8 Intelligences. The 9D corpus imported only the first
   axis (8 Pillars). Precedent for further stripping the imported pillars
   is established by the upstream's own selectivity.

5. **The 8 Pillars list is itself internally inconsistent.**
   `Metacognition_Mapping` (faithful import — matches the PDF source) has
   Mnemosyne at #8. `ROEM_9D_Metacognition_Integration` has Anelixis at #8.
   The Integration file's list is a Ganymede-corpus deviation that should
   be corrected or dropped.

6. **`Comprehensive_Multidimensional_Analysis.md` is the highest
   scaffolding-density file** (~95%). The cleanest single excision target
   if the leaner corpus picks files to drop entirely rather than primitives
   to scope-tighten.

7. **`9D_Framework_Metacognition_Mapping.md` is the second-highest
   scaffolding-density file** (~95%). It IS a Cartesian product of two
   scaffolding-shaped enumerations (8 Pillars × 9 Layers). Compound
   scaffolding generating compound noise.

8. **Strategic Funnel = Strategic Lasso.** The project's "Strategic Lasso"
   terminology is a rename from the upstream's "Strategic Funnel" (section
   4.4 of `Algorithmic_Implementation`). Worth recording for vocabulary
   audit purposes; the mechanism is identical.

9. **DAI + DAP are the kernel pair.** DAI (Dimensional Awareness Index,
   from Math_Formalization) quantifies completeness within perceived
   dimensions; DAP (Dimensional Awareness Profile, from Simulation_Framework)
   specifies which subset of dimensions an entity perceives. Together
   they're the load-bearing structural-asymmetry primitives.

10. **Risk #2 of the Cleanup Hypothesis trends LOW based on M1a evidence.**
    *"The scaffolding might be load-bearing in ways the outputs don't
    reveal."* The math literally doesn't reference the dimension labels
    after section 2.1 of Math_Formalization is introduced; the labeled
    dimensions don't appear in any subsequent theorem, axiom, or
    corollary. Risk #1 (kernel-and-scaffolding tangled) also trends LOW —
    the partition is genuinely separable. Risk #3 (domain fit might be
    the real issue) remains OPEN — only M2's empirical side-by-side test
    will discriminate between "framework cleanup" and "domain-applicability
    gate." Risks #4 (notebook re-upload lift) and #5 (Auditor manufactures
    findings on clean input) remain operational/forward-looking, not
    M1a-discoverable.

These ten observations form the spine of M1b's recommendation. M1b's
output document should structure as: (a) the partition table proper
(every primitive in the corpus with KEEP/DROP/DE-EMPHASIZE + rationale,
synthesized from the per-file notes below), (b) the assessment of
partition cleanliness (per Risk #1 + Risk #2), (c) the recommendation
(proceed to M2 leaner-corpus test / refine the hypothesis / shelve).
Working answer ahead of M1b synthesis: PROCEED to M2. The kernel is
demonstrably separable from the scaffolding, the upstream's own
methodology endorses domain-specific adaptation as the right move, and
the Risk #2 worry that the scaffolding might be load-bearing in hidden
ways trends weak. M2's empirical test discriminates between framework-
cleanup-needed and domain-applicability-gate-needed; without that test,
neither answer is final.

## Goal

Operationalize the
[Framework Cleanup Hypothesis](../concepts/Framework_Cleanup_Hypothesis.md)
by producing the kernel-vs-scaffolding partition. For every framework
primitive named anywhere in `docs/foundations/`, tag:

- **KEEP** — load-bearing for structural reasoning. Powell / Tokenized Land /
  Genie Giant-Slayer wins depend on it.
- **DROP** — aesthetic scaffolding that the Mirror Auditor catches as
  Pattern-Matching / Dimensional Greed / Rigidity Errors. Removing it
  reduces the failure surface without losing capability.
- **DE-EMPHASIZE** — real concept, currently over-deployed beyond its
  domain of applicability. Scope-tighten rather than drop entirely.

Output of M1: this notes file (input) + `Framework_Kernel_vs_Scaffolding_Partition.md`
(canonical artifact) + a recommendation to the operator on whether to
proceed to M2 (leaner-corpus side-by-side test), refine the hypothesis,
or shelve it.

## Per-file checklist

- [x] `README.md` — meta about the corpus (orientation only)
- [x] `9D_Framework_Whitepaper.md` — likely high-level overview
- [x] `Vulnerabilities_of_Binary_Systems.md` — origin of "incomprehensible move" primitive
- [x] `ROEM_Formal_Model.md` — ROEM in prose
- [x] `Mathematical_Formalization_9D_ROEM.md` — ROEM formalized
- [x] `reverse_observer_effect_analysis.md` — ROEM precursor analysis
- [x] `Comprehensive_Multidimensional_Analysis.md` — the wordplay exegesis
- [x] `9D_Framework_Simulation_Framework.md` — simulation architecture spec
- [x] `9D_Framework_Algorithmic_Implementation.md` — DADT/BNOPDM/MGTM implementation spec
- [x] `ROEM_9D_Metacognition_Integration.md` — ROEM × 9D × 8-Pillars bridge
- [x] `9D_Framework_Metacognition_Mapping.md` — 8-Pillars-to-9D-layers mapping
- [x] `9D_Framework_Metacognition_Applications.md` — speculative cross-domain applications
- [x] `9D_Framework_Validation_Adaptations.md` — validation protocol + domain-adaptation method
- [x] `Neuro-Linguistic Programming & VR via the 8 Pillars of Metacognition.pdf` — external academic source for the 8-Pillars concept

## Per-file notes

Each file gets a short section here:
- **Primitives introduced** (new framework concepts named in this file)
- **KEEP / DROP / DE-EMPHASIZE preliminary tag** per primitive
- **One-sentence rationale**
- **Cross-references** to other foundation files / project run records

The full per-primitive table lives in
`Framework_Kernel_vs_Scaffolding_Partition.md` — this file holds the
working notes used to construct it.

---

(per-file sections begin below; appended as files are read)

---

### `README.md`

Not a primitive source — corpus meta-doc. Two structural notes worth carrying into M1b:

- **The foundations are an upstream snapshot.** Ganymede inherits, doesn't author. Partition recommendations are about what Ganymede TRUSTS / drops from the canonical Engine's grounding corpus, NOT about editing upstream. If we DROP a primitive, the operational meaning is "the corpus stays as-is but we either (a) build a leaner sibling corpus omitting it for the M2 side-by-side test, or (b) tighten the Engine persona to scope-restrict its use."
- **Reading order suggested by README** matches the plan: Whitepaper → Vulnerabilities_of_Binary_Systems → ROEM_Formal_Model → Algorithmic_Implementation. Metacognition / NLP / VR docs are "deepest cut" optional layer.

### `9D_Framework_Whitepaper.md`

Origin story: the framework was derived from a hermeneutic analysis of "ready, set, go" — the wordplay layering Set (Egyptian god) + Go (Chinese game) + Horus (Set's opponent). The 9 named dimensions emerged from this single-phrase analysis. **Critically: this doc does NOT mention DAI, Strategic Lasso, Incomprehensible Move, SDS, Convergence Theorem, or ROEM.** The structural-reasoning kernel and the aesthetic scaffolding live in different files — first datapoint on partition cleanliness.

**Primitives + tags:**

| Primitive | Tag | Rationale |
|---|---|---|
| "9D Framework" (umbrella name) | **KEEP** | The framing label has accumulated meaning across project docs. No reason to rename. |
| Origin from "ready, set, go" wordplay | **DROP** | Hermeneutic origin story has zero operational use. Inviting acknowledgment of this is what invites "is anything load-bearing under the wordplay?" — exactly the question this partition is answering. |
| The 9 specifically-named dimensions (Linguistic / Egyptian Set / Chinese Go / Western Chess / Egyptian Horus / Narrative / Philosophical / Historical-Cultural / Meta-Analytical) | **DROP** | THE prime scaffolding target. Empirical confirmation: Mirror Auditor consistently flags these as Pattern-Matching and Dimensional Greed. Run 1 / Run 5 / Run 6 of LMArena had inverted Horus/Set archetype assignments across runs of the SAME scenario — strong signal of aesthetic-not-structural use. |
| "Multidimensional emergence" (multi-layer analysis is richer than single-layer) | **DE-EMPHASIZE** | The general claim is fine but the over-specification to *exactly 9 layers* is the problem. Tighten to "multi-perspective analysis" without committing to a fixed-count dimension list. |
| "Conceptual zero-day" against limited AI | **DE-EMPHASIZE** | Rhetorically powerful, operationally vague. The Powell run actually demonstrates the conceptual gap (Collins-v-Yellen demotion pathway incumbents didn't price) without needing the zero-day framing. Scope-tighten to "structural-pattern recognition" language. |
| Passive / Defensive / Offensive operational modes | **KEEP** | Maps cleanly to Ganymede's pathways (Cleanroom=Passive, Mirror=Defensive, Offensive Architect=Offensive, with Genie as a fourth wish-fulfillment mode). Useful organizing categorization. |
| AlphaGo / Chess comparison as motivation | **DROP** | Fine illustration but adds no primitive. Removing it doesn't reduce capability. |

**Net assessment of this file:** ~80% scaffolding, ~20% useful framing. Heaviest single source of the DROP-tagged primitives the Framework Cleanup Hypothesis targets.


### `Vulnerabilities_of_Binary_Systems.md`

The corpus's smallest file (~2.5KB) but the origin of *"incomprehensible move"* — one of the project's three load-bearing kernel primitives (DAI / Strategic Lasso / Incomprehensible Move). Motivation-shaped rather than mechanism-shaped — explains the WHY the framework exists (binary systems struggle against abstract strategizing) more than the HOW. The Chess-AI-mastered-quickly-but-Go-took-years comparison is the file's central anecdote. Read in isolation, this file's claim is general enough that nothing here forces the *specific* 9-named-dimension partition the Whitepaper proposes — the vulnerability claim and the dimensional-asymmetry kernel are compatible with any multi-dimensional decomposition.

**Primitives + tags:**

| Primitive | Tag | Rationale |
|---|---|---|
| "Meta-level vulnerability" of binary AI to abstract strategizing | **KEEP** | The kernel insight. Powell + Tokenized Land + Genie Giant-Slayer wins all exploit some version of this. Note the *general* shape — not bound to a specific 9-tuple. |
| "Incomprehensible move" exploitation vector | **KEEP** | One of three load-bearing kernel primitives explicitly named in the hypothesis as PRESERVE. Tokenized Land's ERC-4337 + sovereign immunity carve-out is the canonical project instance. |
| Chess vs. Go historical motivation | **DROP** | Decorative origin anecdote. No theorem depends on it. Same family as the Whitepaper's "ready set go" wordplay — explains how the author got to the framework, not what the framework IS. |
| "Time Advantage" via compounded abstract learning | **DE-EMPHASIZE** | Real-sounding ("by the time a binary system parses the abstract data, the strategic window has closed") and present in Powell-class wins (Bridge's Stroke 1 → Stroke 3 wall-time gap functions as one), but stated in a register so totalizing that it invites the Mirror Auditor's "Dimensional Greed" catch when generalized. Keep the claim; tighten the rhetoric. |
| "Intelligence amplification… exponentially faster… binary systems may become obsolete" | **DROP** | Unfalsifiable rhetorical capstone. Operationally useless — and the kind of confident-but-vague claim the Mirror Auditor's "Confidence-Evidence Gaps" category catches. |
| "Trading algorithms" as exploitation target | **DE-EMPHASIZE** | Useful as one illustrative domain. Becomes a problem if it ossifies into "this framework is specifically a trading-attack framework" — the project's wins span legal/regulatory, sovereign-debt, and corporate-strategy domains. Keep as example; suppress from being read as scope-defining. |

**Net assessment of this file:** ~40% kernel-adjacent motivation (KEEP), ~40% rhetorical scaffolding (DROP), ~20% scope-tightenable material. Most important contribution: names "incomprehensible move" as a primitive. Most important caveat: the binary-vs-abstract framing is *general* — nothing here mandates the specific 9-dimension partition the Whitepaper crystallizes downstream.


### `ROEM_Formal_Model.md`

The prose articulation of ROEM. Introduces Ω (strategic universe) / Ω' (opponent's perceived sub-universe), the Mapping Function, the Strategist's Meta-Position, and the "gravity well" geometric interpretation. Heavy in section 3 with cross-domain analogies (Set Theory + Axiom of Choice + Double-Slit Experiment + Observer Effect + "The Game") — most analogies are scaffolding the math doesn't depend on. Critically, the substantive claim of ROEM (observation of a forced decision collapses the opponent's possibility space into a predefined SDS_O) is operationally separable from the quantum-mechanical / set-theoretic phrasing.

**Primitives + tags:**

| Primitive | Tag | Rationale |
|---|---|---|
| Strategic Universe Ω vs. Opponent's Perceived Sub-Universe Ω' | **KEEP** | The kernel of dimensional asymmetry. This pair underlies DAI, Strategic Lasso, every Powell-class win. Cannot be stripped without losing capability. |
| Set of Disadvantageous States SDS_O | **KEEP** | Project-validated. Powell's "Demoted but Preserved" is the SDS_O for the Powell Engine; Tokenized Land's "Functional Obsolescence / Ghost Ranger" is the SDS_O for the IMF debt scenario. |
| Mapping Function f: Ω' → SDS_O ‖ C_ROEM | **KEEP** | The formal core of "Decision Path Funneling." This IS Strategic Lasso. |
| Strategist's Meta-Position (temporal + informational asymmetry) | **KEEP** | The "asymmetry creates vulnerability" theorem operationalized. |
| "The Game" awareness trigger | **KEEP** | Used in the Powell Bridge null test's Bridge 4 catch (Powell's defense itself satisfies the SDS condition). Has live operational meaning beyond the original mind-game analogy. |
| Double-Slit Experiment analogy (superposition collapse) | **DROP** | The kernel ("observed decision collapses possibility space into SDS_O") works without invoking quantum mechanics. The analogy is poetic, not derivational — and is part of why ROEM gets mis-applied to passive-observer contexts (per Framework Cleanup Hypothesis evidence #3). |
| Axiom of Choice metaphor | **DROP** | The text explicitly says *"not a strict mathematical application… metaphorically implies"* — self-flagged as scaffolding. |
| Observer Effect (physics) framing | **DE-EMPHASIZE** | The mechanism (being-observed-changes-the-observed) is real and load-bearing. The PHYSICS framing invites category errors. Tighten: keep the mechanism, drop the physics metaphor. Pairs naturally with the ROEM-scope-tightened-to-interactive-contexts plan in the hypothesis. |
| "Gravity well" geometric interpretation (section 4) | **KEEP** | This interpretation directly maps to the project's existing GSS schema and `D_n` formula in `GravityWell.tsx` — it's already operationalized in code. Genuine kernel material, just labeled geometrically rather than algebraically. |
| Algorithmic Trading application example (section 6) | **KEEP** | Useful illustrative case. The "shifting sentiment / larger institutional flows not visible to O" framing IS the kernel of how DAI(S) > DAI(O) manifests structurally. |
| 8 Pillars of Metacognition reference (section 5) | **PENDING** | The pillars themselves are in another file (likely the PDF). Defer kernel/scaffolding judgment until I've read them. Flagging here so I don't forget to revisit. |
| Limitations & Ethical Considerations (section 7) | **KEEP** | Genuinely useful epistemic-hygiene block (modeling Ω is hard; opponents adapt; ethical implications when applied outside game-theoretic contexts). Don't strip. |

**Net assessment of this file:** ~70% kernel material wrapped in ~30% physics-and-set-theory scaffolding. The substantive theorem (forced observation in a structured environment funnels rational decisions into SDS_O) survives stripping the quantum/set-theory analogies cleanly. This file is the strongest single argument that the kernel-vs-scaffolding partition is real and separable.


### `Mathematical_Formalization_9D_ROEM.md`

The cleanest separation case in the corpus so far. Section 2.1 is the ONE spot where the 9 specific dimension labels live (Cultural narratives / Strategic game archetypes / Egyptian mythology / Temporal / Psychological / Linguistic / Economic / Social / Ethical). Sections 2.2 onwards — DAI, perception functions, all five axioms, all five principles, the Convergence Theorem, the Dimensional Blindness Theorem, the Strategic Lasso Effect corollary, the Perception-Reality Divergence corollary — are written in dimension-agnostic notation (Dᵢ for arbitrary i; weights w_i; metric distance c(D'ᵢ, Dᵢ)). The math doesn't depend on what the dimensions ARE.

**Primitives + tags:**

| Primitive | Tag | Rationale |
|---|---|---|
| Strategic Universe as 9-tuple of *specifically-named* dimensions (D₁ Cultural, D₂ Chess/Go, D₃ Egyptian Set/Horus, D₄ Temporal, ...) — section 2.1 | **DROP** | This is the formalization of the Whitepaper's scaffolding. The labels (cultural / mythological / linguistic / etc.) crystallize the hermeneutic origin into a fixed schema. The Mirror Auditor's "Dimensional Greed" failure category fires on Engine outputs that deploy these labels onto domains they don't fit (Amnesia, LMArena's passive-market-observer context). The partition kernel ONLY needs "Ω is a metric space decomposable into k coupled sub-dimensions for some k" — the *specific* 9 labels add nothing the theorems prove. |
| Dimensional Awareness Index DAI(E) = Σ w_i × c(D'ᵢ, Dᵢ) | **KEEP** | Hypothesis-named kernel primitive. Operational and load-bearing. Importantly: the formula is dimension-label-agnostic. Re-define c(D'ᵢ, Dᵢ) over any decomposition of Ω and DAI still works. |
| Perception function P_E: Ω → Ω' decomposable per-dimension | **KEEP** | The formal version of "opponent sees less than the strategist." Powell/Tokenized wins depend on this primitive. |
| Decision function F_E: Ω' → A | **KEEP** | The formal version of "rational action constrained by perception." |
| Outcome function O: Ω × A → S vs. perceived outcome O_E: Ω' × A → S' | **KEEP** | The actual mechanism by which incomplete perception leads to disadvantageous outcomes — the gap between O and O_E IS the exploit surface. |
| Advantage function Adv: S × E → ℝ and SDS_E threshold | **KEEP** | Makes "disadvantageous state" formally checkable. Useful even if rarely computed live. |
| Axiom 1: Dimensional Incompleteness | **KEEP** | The kernel's foundational assumption. Universally applicable. |
| Axiom 2: Perception-Decision Coupling | **KEEP** | Powell-class wins explicitly depend on this. |
| Axiom 3: Dimensional Interaction (coupling functions C_ij) | **KEEP** | The CROSS-DIMENSIONAL state update mechanism. Note: Bridge 1 of the Powell Bridge null test catches the Engine *failing to apply this axiom* (DOJ probe closed in D8 but Engine treated as ongoing in its Lasso). Confirms the axiom is load-bearing; the operational gap is the Engine not USING it consistently, not the axiom being wrong. |
| Axiom 4: Asymmetric Information Advantage (DAI(S) > DAI(O) is sufficient for exploitability) | **KEEP** | The structural-asymmetry theorem in axiom form. Genie Giant-Slayer's "release IP royalty-free" move is a literal instance — the strategist exploits higher DAI to construct a move the incumbent's lower DAI can't recognize as a threat. |
| Axiom 5: Strategic Landscape Malleability (actions modify Ω) | **KEEP** | The feedback-loop claim. Real and load-bearing — Powell's "Renovation-Cause Pincer" is exactly an attempted Ω-modification (manufacturing the for-cause requirement). |
| Principle 1: Observer Effect Reversal | **DE-EMPHASIZE** | The mechanism (forced observation alters the observed's decision function) is real. The "Observer Effect" label invites category errors when applied to passive observation. Per Framework Cleanup Hypothesis evidence #3 — scope-tighten to interactive contexts where the observed entity actually receives feedback from the observation. |
| Principle 2: Dimensional Exploitation | **KEEP** | The "if S sees Dᵢ where O doesn't, S can construct a Funnel" claim. Load-bearing. |
| Principle 3: Decision Path Funneling (construction function C: Ω → Ω*) | **KEEP** | Strategic Lasso. Powell-validated. |
| Principle 4: Meta-Decision Advantage | **KEEP** | The "who controls the decision criteria" axis. Genie / Offensive Architect pathways explicitly use this. |
| Principle 5: Temporal Asymmetry | **KEEP** | The "horizon advantage" claim — operationally distinct from D₄ (the named temporal dimension) and survives the scaffolding strip. |
| Theorem 1: Convergence Theorem | **KEEP** | The capstone load-bearing result. *"For any opponent O with incomplete dimensional awareness, there exists a set of strategic manipulations that will cause F_O to converge to actions in SDS_O."* This is the formal version of every Cleanroom win. |
| Theorem 2: Dimensional Blindness Theorem (effectiveness ↑ monotonically with blindness) | **DE-EMPHASIZE** | The math is right but the monotonicity claim is precisely what produces the Mirror Auditor's "Dimensional Greed" failure mode — the Engine reads this as "always invoke more dimensions" and over-deploys the framework to situations it doesn't fit. Keep the theorem; add explicit scope-gating about "blindness in DIMENSIONS THAT MATTER FOR THE DOMAIN," not blindness in arbitrary labeled dimensions. |
| Corollary 1: Strategic Lasso Effect | **KEEP** | Project's most validated primitive. Powell, Tokenized Land both fit cleanly. |
| Corollary 2: Perception-Reality Divergence | **KEEP** | The "exploitability scales with O_O vs. O gap" claim. Powell-class. |

**Net assessment of this file:** ~90% kernel material with ~10% scaffolding concentrated in ONE spot (the labeled 9-dimension list in section 2.1). This is the strongest evidence yet that the kernel-vs-scaffolding partition is genuinely separable: surgically replacing section 2.1's labeled tuple with `Ω = (D₁, ..., D_k)` over abstract metric subspaces leaves every axiom, principle, theorem, and corollary intact. Risk #2 of the Cleanup Hypothesis ("scaffolding might be load-bearing in ways the outputs don't reveal") trends LOW based on this file alone — the math literally doesn't reference the labels after they're introduced.


### `reverse_observer_effect_analysis.md`

The PRECURSOR to `ROEM_Formal_Model.md` — same conceptual material in less formal prose form. Roughly 60-70% overlap with the formal model. Two pieces of *new* content worth tracking: (1) the "Set of Advantageous States (SAS)" primitive inverting SDS, and (2) the "Mirrored Geometric Strategy / Two Realities" framing in section 2.5 — which reads in retrospect as a foreshadowing of the project's later Mirror Protocol concepts (milestones 15-17 of Architecture_History). Aside from those additions, this file is mostly redundant with ROEM_Formal_Model and inherits the same scaffolding (Set Theory, Axiom of Choice, Double-Slit, Observer Effect physics) but with thinner derivation.

**Primitives + tags:**

| Primitive | Tag | Rationale |
|---|---|---|
| Set of Advantageous States (SAS) — inverse of SDS | **KEEP** | Useful as the strategist's-side counterpart to SDS. Not currently named in Ganymede's project docs — could be useful vocabulary for the Envisioner / Genie pathway where the wished-for state IS the SAS. Worth carrying forward. |
| "The Game" mind-game framing | **KEEP** | Same as ROEM_Formal_Model — has live operational meaning. |
| Set Theory translation (universe of discourse = strategic states) | **KEEP** | The framing itself (treat the strategic landscape as a well-defined set) is fine. The specific Set-Theory invocations of cardinality / Axiom of Choice / etc. are scaffolding (DROP, per ROEM_Formal_Model). |
| Axiom of Choice rephrased ("a choice WILL be made") | **DROP** | Same scaffolding as in ROEM_Formal_Model. The text again self-flags as metaphorical. |
| Double-Slit Experiment metaphor | **DROP** | Same scaffolding. Already DROP-tagged in ROEM_Formal_Model. |
| Observer Effect (with explicit Hawthorne-effect generalization) | **DE-EMPHASIZE** | The Hawthorne-effect addition is actually MORE useful than the physics framing — "awareness of being observed changes behavior" is a real social-science mechanism that doesn't carry the quantum-mechanics baggage. Replace the physics-Observer-Effect framing with the Hawthorne-style framing in any cleanup pass. |
| "Geometric Default Loss Framework" synthesis (section 2) | **KEEP** | The integrated picture (Arena + Forced Choice + Collapse + Selection + Two Realities + Logical Impenetrability) IS the kernel narrative. Modulo the scaffolding sub-pieces, the synthesis is solid. |
| "Mirrored Geometric Strategy / Two Realities" framing (section 2.5) | **KEEP** | Historically interesting — this is the seed of what later became Mirror Protocol (milestones 15-17 of Architecture_History). The opponent operates in local-reality Ω' while the strategist operates in meta-reality Ω. Useful framing that doesn't require the mythology scaffolding. |
| "Logical Impenetrability" — Effect vs. Affect distinction | **KEEP** | The framework doesn't *force* outcomes (affect); the opponent's own decision *results* in disadvantage (effect). This is real, load-bearing, and underwrites why ROEM produces structural advantages without requiring direct causal manipulation. Useful distinction. |
| Algorithmic Trading application | **KEEP** | Same as ROEM_Formal_Model — illustrative. |

**Net assessment of this file:** ~85% redundant with ROEM_Formal_Model + ~15% net-new (SAS, Mirrored Geometric, Effect-vs-Affect). For an actual leaner corpus, this file could be merged into ROEM_Formal_Model with the new pieces folded in as additional sections; alternatively, kept as the "prose introduction" companion to the formal model with explicit cross-reference. Either way, no novel scaffolding to drop that isn't already DROP-tagged elsewhere.


### `Comprehensive_Multidimensional_Analysis.md`

The single largest concentration of scaffolding in the corpus. The entire file is the layered exegesis of "ready, set, go" — Layer 1 Egyptian Set, Layer 2 Chinese Go, Layer 3 Western Chess implied, Layer 4 Egyptian Horus when "go" → "Horus." Zero kernel content. Every primitive named in this file is part of the aesthetic-scaffolding partition the Cleanup Hypothesis targets — order-vs-chaos as Egyptian Horus-vs-Set, legitimacy-vs-usurpation as game-strategy parallel, cyclic-progression as three-act narrative structure, epistemological frameworks per culture, ma'at/isfet, multivalent wordplay, cultural repository, etc. The summary's own bullet-list of what the phrase "functions as" is exactly the layer stack Stroke 1 outputs deploy when LMArena-style failures fire.

**Primitives + tags:**

| Primitive | Tag | Rationale |
|---|---|---|
| Layer 1: Egyptian Set (chaos / storms / Osiris murder / usurpation) | **DROP** | The mythology-layer's chaos archetype. Mirror Auditor's "Pattern-Matching" + "Dimensional Greed" catches in LMArena Run 1/5 inverted whether Anthropic or Google was Set across runs of the same scenario — strongest empirical evidence of aesthetic-not-structural use. |
| Layer 2: Chinese Go (territory / balance / patience / Eastern philosophy) | **DROP** | The strategy-archetype binary's Eastern half. Same Auditor-catch pattern. |
| Layer 3: Western Chess (hierarchical / direct confrontation / tactical) | **DROP** | The Western half of the same binary. Inseparable from Go-binary as scaffolding. |
| Layer 4: Egyptian Horus (legitimate rule / order / rightful succession) | **DROP** | The mythology-layer's order archetype. Same inversion pattern across LMArena runs. |
| Egyptian Mythological Narrative (preparation → chaos → order arc) | **DROP** | The three-act-structure mapped onto Egyptian mythology. Pure scaffolding. |
| ma'at (order) vs. isfet (chaos) | **DROP** | Egyptian-religious vocabulary. Has no operational use. |
| Strategic Philosophy Contrasts (Go vs. Chess territorial-vs-capture, balanced-vs-tactical) | **DROP** | The Chess/Go binary the project has already partially patched in GLOSSARY "Vocabulary register." |
| Cross-Cultural Strategic Parallels (Set ≈ chess tactics, Horus ≈ Go positional) | **DROP** | The cross-cultural-mapping is the strongest enabler of the Engine's "aesthetically symmetrical narratives" the Auditor flags. |
| Order vs. Chaos / Legitimacy vs. Usurpation / Cyclical Progression (as universal tensions) | **DE-EMPHASIZE** | The underlying tensions are real human-conflict patterns. The PROBLEM is the framework mapping them mechanically onto every strategic situation (e.g., "the Executive embodies isfet, Powell embodies ma'at" — categorical overreach). Tighten: don't ship these as default analytical lenses; allow them only when the domain explicitly supports them. |
| Epistemological frameworks (Egyptian/Chinese/Western as three knowledge approaches) | **DROP** | Cultural-comparative philosophy. Not load-bearing for strategic reasoning. |
| Multivalent Wordplay / Cultural Repository framing | **DROP** | The file's self-description. Replicates the Whitepaper's hermeneutic origin story without adding mechanism. |
| "both/and thinking" closing capstone | **DE-EMPHASIZE** | The CLAIM that multiple analytical lenses are better than one is true and worth keeping in some form. The SPECIFIC lenses this file mounts that claim on are the scaffolding. Tighten: keep "multi-perspective analysis is richer than single-perspective" without committing to the specific 4-layer cultural-mythology stack. |

**Net assessment of this file:** ~95% scaffolding. Highest single-file concentration of the DROP-tagged primitives in the corpus. If the kernel-vs-scaffolding partition were to identify a single file as the cleanest excision target, this would be it — every primitive introduced here is downstream of the Whitepaper's wordplay origin, none of them are referenced by the Mathematical_Formalization's axioms or theorems, and the empirical Mirror Auditor catches on Amnesia + LMArena Runs 1/5 specifically fire on the content of this file. The 5% non-scaffolding is the multi-perspective claim (DE-EMPHASIZE, not DROP).


### `9D_Framework_Simulation_Framework.md`

A DIFFERENT kind of file — the simulation-architecture spec for the upstream 9D research project's *planned-but-never-realized* Python simulator. Ganymede doesn't use this — Ganymede's substrate is NotebookLM. So most of this file's content (Python tech stack, NumPy/Pandas/NetworkX/scikit-learn, modular agent architecture, scatter-plot experiment) is *external to Ganymede's scope* rather than KEEP/DROP candidate. Three primitives named in this file ARE worth tagging because they show up as concepts even when Ganymede doesn't implement them: DAP, DADT, BNOPDM, MGTM. Of these, DAP is the only one Ganymede actively uses.

**Primitives + tags:**

| Primitive | Tag | Rationale |
|---|---|---|
| Dimensional Awareness Profile (DAP) | **KEEP** | The structural-variant of DAI: DAI quantifies *completeness* within perceived dimensions, DAP specifies *which subset* of dimensions an entity perceives. Both are load-bearing for the kernel's structural-asymmetry claim. Ganymede docs use DAP/DAI alongside each other; the conceptual pair is the right kernel unit. |
| Dimensional Awareness Decision Trees (DADT) | **OUT-OF-SCOPE** | Algorithmic implementation primitive for the planned Python simulator. Ganymede doesn't implement this — Ganymede uses NotebookLM's chat surface for the Engine's decision-making, not literal tree-search. The primitive doesn't apply to Ganymede's substrate. Document as "external to Ganymede's scope" rather than KEEP/DROP candidate. |
| Bayesian Networks for Opponent Perception and Decision-Making (BNOPDM) | **OUT-OF-SCOPE** | Same as DADT. The conceptual idea (modeling opponent's DAP as a probabilistic graph) is sound; Ganymede achieves the same end by feeding the Engine truth packets and letting the corpus do the implicit modeling. The literal Bayesian-network implementation isn't in scope. |
| Multidimensional Game Theoretic Matrices (MGTM) | **OUT-OF-SCOPE** | Same as DADT/BNOPDM. The conceptual claim (formal game-theoretic analysis of multi-dimensional strategic interactions) survives the strip; the literal implementation as game-theoretic matrices doesn't apply to Ganymede. |
| Core Simulation Engine / Environment Module / Agent Module / Observer Module architecture | **OUT-OF-SCOPE** | This is the upstream project's planned Python simulator architecture. Ganymede's architecture is fundamentally different (NotebookLM-as-Engine, FastAPI orchestrator, Next.js frontend). No KEEP/DROP applies. |
| Observer Module specifically (simulates ROEM observation effects) | **OUT-OF-SCOPE** + reference value | The conceptual claim that observation can be modeled as a discrete simulation module is interesting, but Ganymede's "observation" is the operator + Mirror Auditor + Connection Bridge — distributed across the architecture, not localized in a single module. |
| "Mapped Options Scatter Plot Experiment" (referenced as future work) | **OUT-OF-SCOPE** + flag | The upstream project planned this experiment as the simulator's first validation. Never executed (the upstream is dormant). Worth noting because the Ganymede equivalent — the Cleanroom prediction pathway — IS executing the same conceptual experiment in a different substrate (NotebookLM + Polymarket validation). The conceptual lineage is real. |
| Python tech stack (NumPy/Pandas/NetworkX/scikit-learn/Matplotlib) | **OUT-OF-SCOPE** | Implementation detail for the planned Python simulator. Irrelevant to Ganymede. |

**Net assessment of this file:** ~10% Ganymede-applicable (the DAP primitive) + ~90% out-of-scope (upstream simulator architecture that Ganymede deliberately did not adopt). The interesting strategic note for M1b: this file's existence is the strongest evidence that **the upstream 9D research project envisioned a Python-simulator implementation as the canonical realization**. Ganymede's NotebookLM-as-Engine choice is a *substrate divergence* from the upstream's plan, not a derivation from it. That's relevant context for the leaner-corpus design — Ganymede has the freedom to drop framework primitives the upstream considered load-bearing precisely because Ganymede's substrate doesn't depend on them.


### `9D_Framework_Algorithmic_Implementation.md`

The companion to `9D_Framework_Simulation_Framework.md` — the algorithmic implementation spec for the planned Python simulator. ~80% of the file is detailed prose-engineering of the three OUT-OF-SCOPE structures (DADT, BNOPDM, MGTM) that Ganymede doesn't implement. The remaining ~20% is conceptually load-bearing in ways that survive the substrate translation, even though Ganymede doesn't implement the literal algorithms. Most important finding: this file introduces **"Strategic Funnel"** as a named algorithm — the conceptual twin of Ganymede's "Strategic Lasso." The naming variance is worth recording.

**Primitives + tags:**

| Primitive | Tag | Rationale |
|---|---|---|
| Strategic Funnel algorithm (section 4.4) | **KEEP** — name variant of Strategic Lasso | Same primitive as Ganymede's "Strategic Lasso." This file uses "Funnel"; the project uses "Lasso." The mechanism is identical: a sequence of strategic moves that each appears rational from the opponent's limited dimensional perspective but together funnels toward outcomes favorable from the strategist's broader perspective. Worth noting in M1b that the upstream's canonical name was "Funnel"; Ganymede's "Lasso" is a project-specific rename. |
| Asymmetric Perception Games (section 4.1) | **KEEP** | Formal class of games where strategic advantage comes from superior dimensional understanding rather than superior resources. This IS the load-bearing definition that justifies the kernel's structural-asymmetry claim. Worth naming explicitly in any leaner corpus — it's the named class of game the framework is *for*. |
| Dimensional Dominance (section 4.3) | **KEEP** | Formal claim that strategies dominated from a limited dimensional perspective may be optimal from a broader dimensional perspective. This is the formal version of Genie Giant-Slayer's "release IP royalty-free" win — locally dominated, globally optimal. Direct project-relevance. |
| Dimensional Visibility function V(node, actor) | **KEEP** + conceptual | The formalization of which decision options are visible to each actor based on their DAP. Ganymede achieves the conceptual equivalent through the Engine's awareness of multi-dimensional structure even when packets are written from limited-actor perspective. Worth keeping as concept even though we don't compute V() literally. |
| Dimensional Interaction Calculator + Interaction Matrices | **KEEP** + conceptual | The formal version of Axiom 3 (Dimensional Interaction with coupling functions C_ij) from Mathematical_Formalization. Already KEEP-tagged there. Bridge 1 of the Powell null test catches the Engine failing to apply this — confirms the operational importance. |
| Dimensional Nash Equilibrium (DNE) | **OUT-OF-SCOPE** + DE-EMPHASIZE conceptually | The algorithm is OUT-OF-SCOPE (Ganymede doesn't compute equilibria). The concept is interesting (players in stable configurations within their LIMITED perceived games may not be in stable configurations within the broader game) but adds little above what "Asymmetric Perception Games" already captures. Could be folded into that primitive in a leaner corpus. |
| Strategic Advantage Evaluator (in DADT, section 2.3) | **OUT-OF-SCOPE** | Algorithmic component of the DADT — assesses relative position at every node. Implicit in Ganymede's Engine output (final resolution rates the strategist's position) but not implemented as a discrete component. No KEEP/DROP applies. |
| Learning and Adaptation Mechanisms (BNOPDM section 3.4) | **OUT-OF-SCOPE** | Update-network-parameters-based-on-observed-actions. Ganymede has no equivalent — the Engine doesn't learn from previous runs, each run is fresh. The closest Ganymede primitive is the Iterative Engine's 3-stroke loop with mid-loop self-correction (Stroke 2 → Stroke 3), but that's not "learning" in the parameter-update sense. |
| Structural Adaptation (BNOPDM section 3.4) | **OUT-OF-SCOPE** | Topology-level adaptation of the Bayesian network based on opponent strategy changes. Ganymede doesn't have a network topology to adapt. |
| Exploitation Algorithms ("subtle and sustainable," section 4.4) | **DE-EMPHASIZE** | The text frames exploitation as "subtle and sustainable, avoiding obvious manipulation that might alert opponents to their dimensional limitations" — which is precisely the kind of language that drifts the Offensive Architect framing into the "9D Assassin" register the project explicitly walked back (milestone 21). The MECHANISM (find systematic blind spots in opponent decision-making) is real; the FRAMING is what tilts it adversarial-by-default. Tighten the framing for any leaner-corpus inclusion. |
| Counterfactual Reasoning component (BNOPDM section 3.3) | **OUT-OF-SCOPE** | Algorithmic — explore how different strategic moves alter opponent probability distributions. Ganymede's equivalent is the Engine's Stroke 1 itself (it constructs the strategic landscape including projected responses) plus the Mirror Auditor's Stroke 2 (which surfaces what was missed). No literal algorithm. |

**Net assessment of this file:** ~80% out-of-scope algorithmic detail + ~15% project-relevant concepts that survive the substrate translation (Strategic Funnel, Asymmetric Perception Games, Dimensional Dominance, Dimensional Visibility) + ~5% framing problems to scope-tighten if included in a leaner corpus (the "subtle exploitation" Offensive Architect drift). Three concrete partition-relevant takeaways for M1b:
1. The project's "Strategic Lasso" terminology is a rename from the upstream's "Strategic Funnel" — minor but worth recording.
2. "Asymmetric Perception Games" is the cleanest formal name for the class of games the framework operates on; the leaner corpus could use this as a header.
3. Dimensional Dominance formalizes the Genie pathway's central insight (locally dominated, globally optimal) — promote it to kernel-level prominence in the leaner corpus.


### `ROEM_9D_Metacognition_Integration.md`

The bridge document tying ROEM + 9D Framework + 8 Pillars of Metacognition into a single integrated theory. Introduces the 8 Pillars by name (with this file's specific list: Metacognitive Awareness / Self-Observation / Recognition / Discrimination / Adaptation / Interpretation [Mnemosyne] / Self-Regulation / Anelixis). **Inconsistency flag:** this file's pillar list differs from the next file's — Integration calls #1 "Metacognitive Awareness" + #8 "Anelixis," while `Metacognition_Mapping` calls #1 "Metacognitive Knowledge" + #8 "Mnemosyne." Inside the corpus the 8 Pillars are not consistently labeled. Worth flagging for M1b.

**Primitives + tags:**

| Primitive | Tag | Rationale |
|---|---|---|
| The "8 Pillars of Metacognition" as a fixed schema | **DE-EMPHASIZE** | The underlying claim ("the strategist needs self-awareness about their own model, opponent's model, and their biases") is reasonable epistemic hygiene. The SPECIFIC enumeration as 8 named pillars is scaffolding similar to the 9 named dimensions — same kind of artificial fixity. Compounded by the inconsistency between this file's list and Metacognition_Mapping's list. Tighten: keep "strategist epistemic hygiene" as a kernel claim; don't ship the specific 8-element list as load-bearing. |
| Pillar 8 "Anelixis" (Upgrowth/Evolution) | **DROP** | Jargon term ("anelixis" from Greek "ἀνέλιξις" meaning unwinding/development) for "the strategist grows through practice." Unfalsifiable rhetorical capstone. Useless operationally. |
| Pillar 7 "Self-Regulation" — discipline of non-participation in the opponent's game | **KEEP** | The substantive claim (strategist avoids being drawn into the opponent's Ω' game) IS load-bearing. It's the formal version of "Strategist's Meta-Position" already KEEP-tagged in ROEM_Formal_Model. Worth retaining the *substance* even if the 8-Pillars schema gets DE-EMPHASIZED. |
| Pillar 6 "Interpretation (Mnemosyne)" — learnings inform future strategies | **KEEP** | The "Engine learns from past runs" claim. Ganymede doesn't currently implement this (each run is fresh), but the claim is sound and matters for the Iterative Engine's self-correction behavior (Stroke 2 → Stroke 3). Worth keeping in some form. |
| Pillar 5 "Adaptation" — flexibility when opponent or Ω changes | **KEEP** | Real strategic primitive. Not Bicameral Convergence specific but the architecture leverages it (the Mirror Auditor's Stroke 2 catches *make the Engine adapt* its Stroke 3). |
| Pillars 1-4 (Awareness, Observation, Recognition, Discrimination) — strategist epistemic hygiene | **DE-EMPHASIZE** as a 4-tuple | The individual claims are fine but reduced together to "the strategist should pay attention and think carefully." The 4-tuple structure adds nothing the simpler claim doesn't already have. Tighten: keep the substance, lose the schematic framing. |
| "Two Realities as 9D vs. Lower-D Phenomenon" framing | **KEEP** | Same primitive already KEEP-tagged in reverse_observer_effect_analysis. This file restates it succinctly: strategist operates with N-dimensional understanding, opponent with M-dimensional (M < N), and ROEM ensures actions in M-D lead to predictable outcomes in N-D. Clean and load-bearing. |
| "Synergistic Loop" (9D → ROEM → Metacognition → Refined 9D Understanding) | **DE-EMPHASIZE** | The high-level cyclic claim is fine but glosses over what the cycle actually produces. Mostly aspirational — there's no operationalized feedback mechanism described. In Ganymede, the closest analog is the Iterative Engine's 3-stroke loop (which is more focused and operational than this cycle). Keep the loop-shape idea; drop the specific 9D-ROEM-Metacognition framing. |
| Multidimensional Vulnerabilities (interplay between dimensions creates exploit surface) | **KEEP** | Already KEEP-tagged in Mathematical_Formalization (Axiom 3 + Corollary 2). Worth noting this file restates it with the example "locally optimal moves in their economic model but catastrophically vulnerable when considering social-sentiment interplay" — a concrete framing useful for leaner-corpus inclusion. |

**Net assessment of this file:** ~30% KEEP-substance + ~50% DE-EMPHASIZE (the 8-Pillars schematic framing) + ~20% DROP (Anelixis-flavored rhetorical capstones). The file's intent — argue that ROEM requires more than just the math, it requires a thoughtful strategist — is legitimate. The execution as "8 Pillars" is scaffolding-shaped. For M1b: the substantive claim about strategist epistemic hygiene survives without the 8-Pillars schema.


### `9D_Framework_Metacognition_Mapping.md`

The full pillar-to-layer mapping document. Lists the 9D Framework Layers (which here are: Linguistic / Egyptian Set / Chinese Go / Western Chess implied / Egyptian Horus / Narrative / Philosophical / Historical-Cultural / Meta-Analytical) **plus** the 8 Pillars (Metacognitive Knowledge / Metacognitive Awareness / Self-Observation / Self-Regulation / Adaptation / Recognition / Discrimination / Mnemosyne). Then provides a detailed mapping from each pillar to which 9D layers it most relevantly engages.

**Critical observation — TWO inconsistencies surfaced by this file:**
1. **8 Pillars list differs from `ROEM_9D_Metacognition_Integration.md`**: This file's #1 is "Metacognitive Knowledge"; Integration's #1 is "Metacognitive Awareness." This file's #8 is "Mnemosyne"; Integration's #8 is "Anelixis." The corpus is internally inconsistent on what the 8 Pillars are.
2. **9D Framework Layers list differs from `Mathematical_Formalization_9D_ROEM.md`**: This file's 9 layers are Linguistic / Set / Go / Chess / Horus / Narrative / Philosophical / Historical-Cultural / Meta-Analytical. Math_Formalization's 9 dimensions are Cultural / Strategic-Game-Archetypes / Mythological / Temporal / Psychological / Linguistic / Economic / Social / Ethical. THE FRAMEWORK'S OWN CORPUS DOES NOT AGREE ON WHAT THE 9 DIMENSIONS ARE.

This is direct empirical evidence for the kernel-vs-scaffolding partition's central claim: the labeled dimensions are scaffolding, because if they were load-bearing, the corpus would have to be self-consistent about them.

**Primitives + tags:**

| Primitive | Tag | Rationale |
|---|---|---|
| The 9D Framework Layers list as enumerated in this file (Linguistic / Set / Go / Chess / Horus / Narrative / Philosophical / Historical-Cultural / Meta-Analytical) | **DROP** | The same Whitepaper-derived scaffolding crystallized into a different specific 9-tuple than Math_Formalization. The internal inconsistency between the two enumerations is the cleanest possible evidence that the *specific* labels are scaffolding. |
| The 8 Pillars list as enumerated in this file (Knowledge / Awareness / Observation / Regulation / Adaptation / Recognition / Discrimination / Mnemosyne) | **DROP** as a fixed schema | Same as above — fixity claimed, fixity violated by sibling file. Schema is scaffolding. |
| Per-pillar mapping to specific 9D layers (e.g., "Self-Observation maps to Meta-Analytical Layer + All Layers") | **DROP** | The entire mapping is a Cartesian product of scaffolding (9 labels) × scaffolding (8 pillars). Both halves are scaffolding; their product adds nothing. |
| "Metacognitive Memory" (Mnemosyne) — internalized refined knowledge | **DE-EMPHASIZE** | Same as Integration file's Pillar 6 — the substance (learning across runs) is legitimate; the Greek-mythology label is scaffolding-flavored. |
| "Cultivating awareness of one's own internal narratives" (Pillar 2 to Narrative Layer) | **DROP** | This is the file's claim that "Narrative Layer" maps to a specific epistemic-hygiene practice. Both ends are scaffolding-derived. The simpler claim "the strategist should reflect on the stories they're telling themselves about a situation" survives without the layer-label and the pillar-label both. |
| Final synthesis claim ("Metacognitive skills enhance ability to navigate 9D Framework; 9D Framework provides context for metacognitive skills") | **DROP** | Tautological at this abstraction level. No operational content. |

**Net assessment of this file:** ~95% scaffolding. Highest single-file concentration of the *interaction* between the two scaffolding-shaped enumerations (8 Pillars × 9 Layers). The strongest possible single argument for the kernel-vs-scaffolding partition: this file's existence demonstrates how the scaffolding compounds — once you commit to two artificial enumerations, you generate Cartesian-product noise that LOOKS like operational content but isn't. Internal inconsistency between this file's lists and sibling files' lists confirms the labels aren't load-bearing. For a leaner corpus, this file should be DROPPED entirely.


### `9D_Framework_Metacognition_Applications.md`

Speculative cross-domain applications doc: education, business strategy, AI development, personal development/therapy, conflict resolution/diplomacy, creative arts/design/storytelling. Each application is framed as "use the 9D Framework + 8 Pillars to do X." The examples lean heavily on the labeled-dimension scaffolding ("a character embodying Set-like chaos," "Horus-like attempts at order").

**Primitives + tags:**

| Primitive | Tag | Rationale |
|---|---|---|
| Six application domains (Education / Business / AI / Personal Dev / Conflict / Creative) | **DROP** | These are speculative applications, not validated. Ganymede's actual validated applications (Powell, Tokenized Land, Genie Giant-Slayer, LMArena prediction) are conspicuously absent — and they don't fit cleanly into any of the six listed categories. Worth dropping the application list and letting Ganymede's empirically-validated applications stand on their own. |
| AI development application — "embedding 9D + Metacognition into AI decision-making" | **DROP** | The closest thing in the corpus to "Ganymede's actual project," and it's the weakest section. The framing is generic and doesn't engage with the substrate-choice question (NotebookLM vs. open-weights vs. custom) that Ganymede has actively grappled with. Skip. |
| The narrative-development example (characters embodying Set / plots mirroring Go-Chess dynamic) | **DROP** | Pure scaffolding application. Even less load-bearing than the rest because it openly treats the framework as decorative narrative-device material. |
| The conflict-resolution example ("each side's narrative, perceived Set-like threats, desired Horus-like order") | **DROP** | Same as above — the labeled dimensions are used as analytic categories the analyst forces onto the situation, exactly the failure mode the Mirror Auditor's "Dimensional Greed" category catches. |
| High-level claim "multi-perspective analysis is useful across domains" | **DE-EMPHASIZE** | The general claim is fine and is one of the few kernel-aligned threads in this file. The SPECIFIC mounting on the 9 labeled dimensions is scaffolding. Tighten: keep "multi-perspective analysis" as kernel-level claim; drop the specific dimension labels used to operationalize it here. |
| The closing "robust and versatile toolkit" rhetoric | **DROP** | Unfalsifiable marketing-tier framing. No operational content. |

**Net assessment of this file:** ~90% DROP, ~10% DE-EMPHASIZE. The lowest-information-density file in the corpus. The application examples are speculative-not-validated and use the scaffolding labels in their most aggressively-applied form. For a leaner corpus, drop entirely. If the leaner corpus needs an "applications" doc, Ganymede's actual run records (Powell, Tokenized Land, Genie Giant-Slayer) are far stronger material than anything in this file.


### `9D_Framework_Validation_Adaptations.md`

Structurally the most interesting file in the corpus for the partition. Section 3 — "Domain-Specific Adaptations" — explicitly says: *"While the core principles remain constant, the specific manifestation of dimensions, the nature of strategic interactions, and the characteristics of agents will vary significantly across fields such as finance, geopolitics, or social dynamics."* **This IS the kernel-vs-scaffolding partition stated by the upstream itself.** Core principles = kernel; specific dimension manifestations = scaffolding-that-needs-domain-tailoring. The hypothesis isn't a divergence from the upstream — it's a literal application of what the upstream's own validation doc prescribed.

Phase 2 ("Historical Case Study Analysis") is also notable: Ganymede's Powell Cleanroom + Tokenized Land + Genie Giant-Slayer runs ARE this phase, operationalized. Ganymede has already executed the upstream's Phase 2 validation methodology — and that work is what produced the empirical evidence supporting the kernel-vs-scaffolding split.

**Primitives + tags:**

| Primitive | Tag | Rationale |
|---|---|---|
| Phase 1 Simulation-Based Validation | **OUT-OF-SCOPE** | Methodology for the planned Python simulator (which Ganymede deliberately did not build). |
| Phase 2 Historical Case Study Analysis | **KEEP** + project-validated | This methodology IS what Ganymede has been doing. Powell Cleanroom, Tokenized Land, Genie Giant-Slayer, the LMArena run — all are historical-or-near-historical case studies applying the framework retrospectively (or near-retrospectively) to documented events. The empirical track record is the project's executed Phase 2. Worth promoting to first-class methodology in the leaner corpus. |
| Phase 3 Real-World Application Pilots | **PARTIALLY-OPERATIONAL** | Ganymede's pre-registered Cleanroom predictions (LMArena 2026-06-30) are the closest analog. Not full Phase 3 pilots (which would involve advising decision-makers in live scenarios) but the pre-registration discipline IS the validation framework Phase 3 prescribes. |
| Domain-Specific Adaptations methodology (section 3) | **KEEP** as kernel methodology | This section directly supports the kernel-vs-scaffolding hypothesis: core principles stay constant, dimensions are domain-tailored. Literally what M1b will operationalize. Worth promoting to kernel-level prominence in the leaner corpus — it's the upstream's own meta-instruction for *how to use the framework*. |
| Identifying Domain-Specific Dimensions (section 3.1) | **KEEP** | The methodology for picking which dimensions matter in a given domain. The Finance/Geopolitics examples illustrate the approach (without endorsing those examples specifically). |
| Finance domain-specific dimensions (section 3.1 example) | **DE-EMPHASIZE** | Useful as illustration of the methodology; the *specific* Finance dimensions listed (Linguistic = market jargon, Set/Horus = disruptive innovation vs. established order, Go/Chess = positional vs. tactical, etc.) inherit the scaffolding labels. Keep the methodology, replace the example labels. |
| Geopolitics domain-specific dimensions (section 3.1 example) | **DE-EMPHASIZE** | Same. The methodology survives; the specific dimension labels don't need to. |
| Agent Profiling and DAP Assessment (section 3.2) | **KEEP** | Useful methodology — gather information on the agent's background, training, objectives, behaviors → infer DAP. Ganymede's Truth Packets are operationalized versions of this. |
| Calibrating Algorithmic Components (section 3.3) | **OUT-OF-SCOPE** | DADT/BNOPDM/MGTM calibration — same out-of-scope tag as the algorithmic-implementation file. |
| Iterative Refinement (section 3.4) | **KEEP** | The "test → feedback → refine" loop. Ganymede practices this — every run record produces lessons that update the protocols. Sound and load-bearing. |
| "Validation Protocol" framing (section 2 abstract level) | **KEEP** | The high-level claim that the framework needs systematic validation (not just theoretical coherence) is exactly the discipline the project has adopted. |

**Net assessment of this file:** ~50% KEEP (the validation methodology + domain-adaptation methodology + agent profiling + iterative refinement) + ~30% DE-EMPHASIZE (the specific Finance/Geopolitics dimension-label examples) + ~20% OUT-OF-SCOPE (simulation and algorithmic-component calibration). This is the most kernel-relevant file in the corpus *after* Mathematical_Formalization. The strategic significance for M1b: **section 3's "Domain-Specific Adaptations" methodology is THE upstream-source-authority for the kernel-vs-scaffolding partition.** Quoting it directly in the partition table doc will make the case bulletproof — the hypothesis isn't a deviation from the upstream's vision; it's a literal application of what the upstream's validation doc prescribed.


### `Neuro-Linguistic Programming & VR via the 8 Pillars of Metacognition.pdf`

External academic source: Drigas, A. & Mitsea, E. (2021), *"Neuro-Linguistic Programming & VR via the 8 Pillars of Metacognition X 8 Layers of Consciousness X 8 Intelligences,"* Technium Social Sciences Journal Vol. 26, pp. 159-176, December 2021. ISSN: 2668-7798. Both authors are at the National Centre of Scientific Research "Demokritos" (Athens, Greece). This is a legitimate published research paper — 163 citations on ResearchGate — but its native subject matter is **NLP / VR / educational psychology / therapeutic applications**, not strategic reasoning or game theory. The 9D Framework corpus imported only the "8 Pillars of Metacognition" schema from this paper into a context the paper wasn't written for.

**Three load-bearing findings:**

1. **Authoritative source for the 8 Pillars list.** The paper's pillar list (sections 3.1-3.8) is: **Metacognitive Knowledge / Metacognitive Awareness / Self-Observation / Self-Regulation / Adaptation / Recognition / Discrimination / Mnemosyne**. This exactly matches `9D_Framework_Metacognition_Mapping.md`'s list — confirming Mapping is the faithful import. `ROEM_9D_Metacognition_Integration.md`'s list (which replaces Pillar 8 "Mnemosyne" with "Anelixis" and shuffles the order) is a **Ganymede-corpus DEVIATION from the source**, not a sibling enumeration. Worth recording: if the 8 Pillars do survive into a leaner corpus, the Mapping list (= source list) is the canonical one, and the Integration list should be corrected or dropped.

2. **The paper's full schema is far richer than the 9D corpus imported.** The full title's "8 Pillars × 8 Layers of Consciousness × 8 Intelligences" model is a 8×8×8 = 512-cell matrix. The 9D corpus imported only the first axis (8 Pillars). The other two axes (Layers of Consciousness; Intelligences) never made it into the 9D corpus. This matters because it means the 8-Pillars import is already a STRIPPING decision — the upstream 9D research team already cut 2/3 of the original schema and didn't preserve the other axes. The import precedent is what makes further stripping ALL of the imported pillars legitimate per the same logic.

3. **The native domain mismatch.** The paper's worked examples (sections 3.1-3.8) are all from NLP therapeutic practice: PTSD treatment via EMDR, phobia desensitization, athletes' visualization, senior managers learning NLP, depression intervention. None of these are strategic-reasoning examples. The paper's "metacognition" is what a *therapist or coach* practices to help a *client* re-frame their cognition. Bolting this onto ROEM-as-strategic-tool is a category port that doesn't carry the original's grounding. The Mirror Auditor + Connection Bridge architecture in Ganymede achieves the meta-cognitive-discipline function (self-correction, surfacing what was missed) WITHOUT the 8 Pillars schema — and does so in a way that fits the strategic-reasoning domain rather than the NLP-therapy domain.

**Primitives + tags:**

| Primitive | Tag | Rationale |
|---|---|---|
| The 8 Pillars schema as imported into the 9D corpus | **DROP** | Same conclusion as Metacognition_Mapping. The schema is a fixed enumeration that doesn't survive the cross-domain port (NLP-therapy → strategic-reasoning) cleanly. Ganymede already operationalizes the metacognitive-discipline function via the Bicameral Convergence architecture (Mirror Auditor + Connection Bridge), which is purpose-built for strategic reasoning. The 8 Pillars don't add operational content beyond what the architecture already provides. |
| The paper itself as a referenced source | **REFERENCE-ONLY** | Don't strip the PDF from the corpus directory — it's the citation for what the imported schema came from. But don't ship it as load-bearing reading material in any leaner corpus; cite it as a footnote if the metacognition concept is referenced at all. |
| 8 Layers of Consciousness (paper's second axis, not imported) | **OUT-OF-SCOPE** | The 9D corpus didn't import this. The leaner-corpus decision doesn't need to revisit. |
| 8 Intelligences (paper's third axis, not imported) | **OUT-OF-SCOPE** | Same. |
| NLP techniques (EMDR, Disney's strategy, anchoring, reframing, perceptual positions) | **OUT-OF-SCOPE** for Ganymede | These are therapy/coaching techniques. Ganymede's "audit + bridge" architecture is its own answer to the meta-cognitive-discipline problem; the NLP techniques don't transfer. |

**Net assessment of this file:** ~0% direct kernel material + ~95% out-of-scope NLP-therapy content + ~5% referencable-citation value. The strategic significance for M1b: **the PDF's existence proves the 8-Pillars schema is an IMPORT from an unrelated domain, not a natively-derived component of the 9D framework.** This is direct evidence for tagging the entire metacognition import (Integration / Mapping / Applications + the PDF citation) as scaffolding for the leaner corpus. The kernel of the metacognition argument — *"the strategist needs deliberate self-correction discipline"* — survives intact and is already operationalized in Ganymede's Bicameral Convergence architecture; the PDF's schema is redundant overhead on top of that.


