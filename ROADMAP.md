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
| **4. Pluggable** | v2 API + Bicameral /iterate + Dispatcher all production | **Pl1: Operational hygiene** | Pl2: First module consumer |

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

### Pl2 — First module consumer (NEXT)

**Goal:** Wire PrisonBreak as the first concrete consumer of the
v2 API, per `docs/integration/examples/prisonbreak_consumer.md`.

**Deliverables:**
- PrisonBreak's `SimulatePanel.tsx` calls Ganymede's `/api/v2/sessions`
  + `/iterate` with errors-as-truth-packets.
- Validation that the Genie pathway produces useful output for
  PrisonBreak's "digital public defender" use case.
- Run record documenting the first end-to-end consumer run.

**Exit criteria:** PrisonBreak's SimulatePanel produces a Ganymede-driven
strategic resolution end-to-end on at least one case.

**Role split:**
- This is cross-project work — touches PrisonBreak's repo. Operator
  may want to do this manually or have Claude handle both repos.
  Decision pending operator availability.

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
