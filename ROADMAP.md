# ROADMAP — Project Ganymede

Phase-by-phase plan from current state to vision-complete. Organized
by the four silos defined in [`docs/OVERVIEW.md`](docs/OVERVIEW.md#the-four-silos-canonical-project-organization).

> **How this file works.** Each silo has its own phase sequence. Phases
> are sequential within a silo but can run concurrently *across* silos
> (e.g., a Methodology deep-read can happen alongside a Predictor
> calendar wait). The active phase for each silo is marked. The atomic
> chunks for whatever phase Claude is currently working live in
> [`TASKS.md`](TASKS.md).

---

## Status at a glance (2026-06-06)

| Silo | Last shipped | Active phase | Next phase |
|---|---|---|---|
| **1. Predictor** | LMArena Cleanroom partially validated 2026-06-05 (milestone 42) — Bridge's mechanism-category catch landed in reality as Anthropic's pause call, 10 days early | **P1: Bridge robustness** (2 of 3 exit criteria met) | P2: 2026-06-30 leaderboard-rank resolution (secondary, mechanism-category already validated) |
| **2. Envisioner** | Bicameral Convergence Level 1 wired into /iterate (milestone 38) | **E1: Bicameral Level 2 build** (priority elevated by milestone 42 validation — architectural gap to specific predictions is now empirically named) | E2: Bicameral Level 3 |
| **3. Methodology** | Framework Kernel vs. Scaffolding partition shipped (milestone 41) | (M1 complete) — **M2 operator-gated, deprioritized vs. E1 in light of milestone 42** | M2: Side-by-side leaner-corpus test |
| **4. Pluggable** | Z-SPAN pattern-recognition validation 2026-06-06 (milestone 43) — framework correctly identified Z-SPAN's structural position from a generic prompt | **Pl1: Operational hygiene** | **Pl2: Z-SPAN as first consumer** (changed from PrisonBreak per milestone 43) → **Pl3: Operator Lens (translation stroke for operator-facing output)** |

---

## Silo 1 — Predictor

> **Mission:** Use the Engine as a closed-loop forecaster. Given a
> falsifiable scenario, identify non-obvious strategic outcomes that
> reality later confirms.

### P1 — Bridge robustness (ACTIVE)

**Goal:** Make Bicameral Convergence Level 1 trustworthy enough that
the audited+Bridge-extended prediction is the load-bearing one for
all future Cleanroom runs.

**Deliverables:**
- Powell-sound Bridge null test — does Bridge produce "0 missed
  bridges" on known-sound Engine output? (Diagnostic for whether
  Bridge over-produces SPECULATIVE bridges on sound input.)
- Persona CTA-suppression diagnostic — Stroke 1 still leaks "Would
  you like me to…" CTAs in ~50% of runs. Quantify and decide on
  mitigation.
- Bridge notebook lifecycle decision — auto-cleanup vs operator-managed.

**Exit criteria:**
- Powell-sound test produces "0 missed bridges" OR a documented
  understanding of when Bridge over-produces and what to do about it.
- Stroke 1 CTA-leak rate documented; mitigation decided.
- Bridge notebook cleanup approach decided (probably operator-managed
  with optional `cleanup_bridge_notebook: bool` flag).

**Role split:**
- Claude builds the test scripts, runs them, drafts findings.
- Operator picks the Powell-class baseline (or accepts Claude's
  default pick — `Powell_Cleanroom/`).

### P2 — 2026-06-30 LMArena prediction validation (NEXT)

**Goal:** Validate the audited+Bridge-extended LMArena prediction
against reality. Document the result with the same discipline as
the Powell run.

**Deliverables:**
- Pull LMArena leaderboard rank at end of June 2026.
- Pull Polymarket resolution price for the "Which company has best
  AI model end of June?" market.
- Update `docs/experiments/runs/06_LMArena_Anthropic_Cleanroom.md`
  with the actual outcome.
- Classify: validated / falsified / partial / inconclusive.

**Exit criteria:** Run record updated with outcome and classification.

**Role split:**
- Operator triggers the validation on 2026-06-30 (or near it).
- Claude does the data-pull and write-up.

### P3 — Next pre-registered prediction (FUTURE)

After P2 lands, pick the next Cleanroom-shape question. Candidate
domains per `docs/brainstorming/Palantir_For_Ganymede.md` —
single-company strategic dossier, legal/regulatory case prediction,
corporate-event prediction. Politics excluded per operator standing rule.

---

## Silo 2 — Envisioner

> **Mission:** Use the Engine to design strategy given a wished-for
> state. Mirror Validation and Bridge audit operate against the
> Envisioner's output.

### E1 — Bicameral Convergence Level 2 design (ACTIVE)

**Goal:** Build `run_bicameral_loop()` — the closed-loop mirror-bounce
between Engine and Bridge until convergence — with the five mandatory
operator control surfaces.

**Deliverables (per `docs/concepts/Bicameral_Convergence.md` §
"Operator control surfaces"):**
1. Visual transparency — WS events at each iteration boundary
2. Cancel endpoint — `POST /api/v2/sessions/{id}/cancel`
3. Minimum inter-iteration delay (default 5s, configurable 2-30s)
4. Hard iteration cap (default 5, configurable 1-10)
5. Operator approval gate for new Oracle spawn (Level 3 only,
   stubbed for Level 2)

**Exit criteria:**
- `run_bicameral_loop()` orchestrator method shipped + tested
  on at least one scenario.
- All five control surfaces wired through to the API + frontend.
- Cancel works mid-loop with clean orphan cleanup.
- WS subscribers see iteration progress live.

**Role split:**
- Architectural spec is already locked in
  `docs/concepts/Bicameral_Convergence.md` — Claude builds against
  the spec autonomously.
- Operator approves test scenario for first live run.

### E2 — Bicameral Convergence Level 3 (NEXT)

**Goal:** Bridge-triggers-new-Oracle-spawn decision logic, gated
by operator approval. The substrate-expansion mechanism.

**Deliverables:**
- When Bridge surfaces a STRUCTURAL bridge requiring information
  neither instance has, the loop emits `ORACLE_SPAWN_REQUESTED`
  and pauses for operator approve/reject.
- `POST /api/v2/sessions/{id}/oracle-spawn-decision` endpoint.
- Frontend UI for the approval dialog.

**Exit criteria:** A live run where the operator approves a
Bridge-triggered Oracle spawn and the loop continues with the
expanded substrate.

**Role split:**
- Claude builds the decision logic + API surface + UI dialog.
- Operator participates in the approve/reject flow live.

---

## Silo 3 — Methodology

> **Mission:** The deep look at what the framework actually IS,
> including conflicts and limits.

### M1 — Foundations corpus deep-read (ACTIVE)

**Goal:** Operationalize the
[Framework Cleanup Hypothesis](docs/concepts/Framework_Cleanup_Hypothesis.md)
by producing the kernel-vs-scaffolding partition.

**Deliverables:**
- End-to-end read of `docs/foundations/` (13 imported 9D theoretical
  docs from the upstream 9D-Chess project).
- An annotated table of every primitive in the corpus with
  KEEP / DROP / DE-EMPHASIZE marking + rationale.
- A written assessment of the kernel-vs-scaffolding partition's
  cleanliness (per Risk #1 in the hypothesis: "stripping too
  aggressively breaks the wins").
- Recommendation: proceed to side-by-side test, refine the hypothesis,
  or shelve it.

**Exit criteria:** Partition table + assessment exist as a doc in
`docs/concepts/`; operator has read it and signed off on the
recommendation.

**Role split:**
- Claude does the deep-read and produces the partition table.
- Operator reviews and signs off on the recommendation before
  committing to M2.

### M2 — Leaner-corpus side-by-side test (NEXT)

**Goal:** Empirically test whether the kernel-vs-scaffolding partition
produces a leaner Engine that preserves Powell-class wins while
reducing Amnesia/LMArena-style dimensional-greed failures.

**Deliverables (per Framework_Cleanup_Hypothesis §
"Proposed approach"):**
- Build a side-by-side Engine notebook with the leaner corpus.
- Run Powell, Tokenized Land, Amnesia, Genie Giant-Slayer,
  and LMArena scenarios against BOTH the canonical Engine and the
  leaner one.
- Apply the evaluation criteria (PRESERVE: Powell-class wins;
  REDUCE: Amnesia/LMArena failures; NEUTRAL: Stroke 1 length drop).

**Exit criteria:** Side-by-side test report with empirical findings;
operator decides whether to promote the leaner notebook to canonical.

**Role split:**
- Claude runs the tests, writes the report.
- Operator decides on promotion. This is a major scope shift (the
  canonical Engine moves) — operator-gated.

### M3 — Framework decision (FUTURE)

After M2, operator decides on the framework's future:
- Keep the current corpus (M2 falsified the hypothesis)
- Promote the leaner corpus (M2 confirmed the hypothesis)
- Pursue a home-brewed runtime (M2 showed NotebookLM is the wrong
  substrate entirely)

Final decision lives in `docs/history/Architecture_History.md` as
a milestone.

---

## Silo 4 — Pluggable

> **Mission:** The integration layer. Ganymede as a private analysis
> module other projects can call.

### Pl1 — Operational hygiene (ACTIVE)

**Goal:** Shore up the v2 API surface for first external consumers.

**Deliverables:**
- Upstream `notebooklm-py` PR for the `[["e",4,null,null,N]]`
  error envelope (SDK should recognize as `ChatError`).
- Documentation pass on `docs/integration/consuming_the_v2_api.md`
  — confirm it reflects the post-milestone-38 surface.
- Predictions bulletin board (optional small ship) — `/predictions`
  route in the UI showing pre-registered predictions with countdown +
  resolution outcome.

**Exit criteria:**
- Upstream PR submitted (or punted with reason).
- v2 API doc accurate.
- Bulletin board shipped (if operator opts in).

**Role split:**
- Claude does the upstream PR, doc pass, and (if approved) bulletin
  board.
- Operator opts in/out on the bulletin board.

### Pl2 — First module consumer: Z-SPAN (NEXT — primary)

**Goal:** Wire Z-SPAN as the first concrete consumer of the v2 API, with
Z-SPAN using Ganymede as a long-term strategic-planning module for
positioning against legacy GovTech competitors (Granicus etc.).

**Why Z-SPAN replaces PrisonBreak as primary** (per milestone 43,
2026-06-06): the 2026-06-06 NotebookLM transcript demonstrated that the
framework's strategic-reasoning maps cleanly to Z-SPAN's competitive
situation (open-source civic-data platform vs. closed-source legacy
GovTech). Z-SPAN has live strategic decisions to make over the next
weeks/months (terminology lock-in, competitive response, audience-facing
narrative). The framework is exercised on real decisions, not
hypotheticals. PrisonBreak is preserved as the planned second consumer.

**Deliverables:**
- **Persistent session state** — current sessions are ephemeral; long-term
  Z-SPAN strategic planning wants sessions that persist over weeks,
  build on prior strokes, and surface a history of strategic
  decisions. Backend persistence (Session + StrokeResult into SQLite or
  similar) + API endpoints to resume / list / search prior sessions.
- **Z-SPAN-side integration spec** — `docs/integration/examples/zspan_consumer.md`
  describing how Z-SPAN calls Ganymede for strategic positioning,
  competitive-response planning, terminology validation, etc.
- **First live Z-SPAN strategic session** — a real Z-SPAN positioning
  question processed end-to-end through the Dispatcher → iterative
  loop → operator-facing output.
- **Run record** documenting the first end-to-end Z-SPAN consumer run.

**Exit criteria:** Z-SPAN's operator surface produces a Ganymede-driven
strategic resolution end-to-end on at least one real positioning
decision, and the operator can come back to the session a week later
and continue with full prior-stroke context preserved.

**Role split:**
- Cross-project work — touches Z-SPAN's repo. Operator decides which
  side gets which work; Ganymede side handles persistence + integration
  spec.

### Pl3 — Operator Lens (translation stroke for operator-facing output)

**Goal:** Build a downstream translation stroke that re-expresses the
final stroke's output in legible operator-facing language while
preserving the kernel's logic 1:1. Solves the "framework output is
correct but jargon-heavy" UX problem without contaminating upstream
reasoning.

**Origin:** surfaced in the 2026-06-06 NotebookLM transcript session
(milestone 43). When James prompted the framework with the Cube of
Space as an aesthetic frame, the framework produced strategically
identical reasoning but in more visceral/legible vocabulary
(*"actualizes the concept instead of avoiding it"*, *"central
intersection"*, *"gravity well"*, *"North face / South face"*). The
insight: the kernel doesn't need to change; a translation layer
downstream of the analytical strokes can re-express the output for
human consumption. Architecturally analogous to a post-process render
layer, not a persona change.

**Why this architectural shape:**
- Persona text changes contaminate upstream reasoning (corpus-dominance
  lesson from M1 and earlier persona experiments). NOT the right lever.
- Adding aesthetic frameworks to the grounding corpus compounds
  scaffolding (M1 Cleanup Hypothesis evidence). NOT the right lever.
- A downstream translation stroke is purely additive, reversible, and
  preserves both the technical and translated versions for audit +
  display.

**Deliverables:**
- **Translation Persona** sibling to Engine / Mirror Auditor / Connection
  Bridge personas. Spec: receive a final-stroke raw_response + a
  vocabulary-register target (e.g., "Cube-of-Space register",
  "plain-English register", "executive-brief register"); re-express
  in the target register while preserving the analytical claims 1:1.
  Must NOT add new claims, soften strength, or introduce hedging the
  original didn't carry.
- **`run_translation()` orchestrator method** that fires the translation
  stroke against a final synthesis (Stroke 3 in iterative runs;
  Bicameral converged output in Level 2 runs).
- **Session state** preserves both the technical final synthesis and
  the translated version. API exposes both fields.
- **Frontend toggle** between technical view and translated view in
  DispatcherPanel + RunnerPanel; default to translated for operator-
  facing display.
- **Verbosity / register selector** — operator picks the translation
  register per run. Default register: plain-English; alternative
  registers selectable.
- **First live run + comparison** — Cube-of-Space register applied to
  a recent Stroke 3 (e.g., the Run 6 audited Anthropic synthesis).
  Validate that the translated version preserves the analytical claims.

**Exit criteria:** A live run produces both technical and translated
outputs; operator can compare side-by-side; the translated version
preserves the kernel's claims without altering them.

**Role split:**
- Claude builds the Translation Persona spec + orchestrator method +
  API extension + frontend toggle.
- Operator decides on the register library — which named registers to
  ship (Cube-of-Space, plain-English, executive-brief, etc.).

---

## Cross-cutting concerns

These don't belong to a single silo but should stay on the radar:

- **GOOGLE_API_KEY rotation** — operator action, sanctioned-skipped
  earlier this month per the original handoff note.
- **Bridge notebook lifecycle policy** — once Bridge runs become
  routine, the question of when to auto-delete bridge notebooks
  becomes real. See P1 for the decision step.
- **Cookie lifetime** — NotebookLM cookies ~5hr lifetime. The auth
  pill works; future-Claude should expect re-auth requests every
  session pause >5hr.

---

## How phases get added or modified

- **Adding a phase:** when a chunk surfaces work that doesn't fit
  any existing phase, propose a new phase in `TASKS.md` under
  "NEXT UP" and surface it in the next stop-report. Operator
  confirms before the phase becomes ACTIVE.
- **Modifying a phase:** if a phase's exit criteria turn out to be
  wrong, log it in `docs/history/Architecture_History.md` and
  update this file.
- **Closing a phase:** once exit criteria are met, mark the phase
  COMPLETED and move the next phase to ACTIVE. Surface in the
  next stop-report.

## How this file gets kept fresh

Every time a phase transition happens (chunks deplete a phase,
operator approves the next phase, an unexpected gap emerges),
this file gets updated alongside `TASKS.md`. The two stay in sync.

If you find this file disagreeing with `TASKS.md` or with reality,
that's a stop condition — ask the operator.
