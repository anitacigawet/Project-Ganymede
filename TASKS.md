# TASKS — Active Atomic-Chunk Ledger

The next thing Claude ships is the top item of ACTIVE.

Last updated: 2026-06-01 (post-P1-03 — Stroke 1 CTA-leak rate quantified at ~43%; post-processor follow-up added as P1-03b).

> **How this file works** — see
> [`CLAUDE.md`](CLAUDE.md) § "The Atomic Chunk Loop" and the
> [Autopilot Protocol](C:\Users\james\Documents\Obsidian\PROJECTS\CLAUDE\Autopilot\AUTOPILOT_PROTOCOL.md)
> § "The Active-Todo File Contract". Sections: ACTIVE (current work,
> ordered), NEXT UP (preview of upcoming phases, lower granularity),
> COMPLETED ARCHIVE (historical record).

---

## ACTIVE — Silo 1 Phase P1: Bridge robustness + operational hygiene

The current chunk queue. Top item is the next thing to ship.

### ~~P1-01 · Upstream notebooklm-py PR for the `[["e",4,null,null,N]]` envelope~~ ✅ DRAFTED 2026-05-26 (awaiting submission)

**Status: drafted + tested locally. Awaiting operator submission to upstream.**

Worked out the fix on the upstream `teng-lin/notebooklm-py` repo
(cloned to sibling `../notebooklm-py-fork/`, branch
`fix/chat-e-error-frame`, commit `17c92270`). Per repo conventions, the
fix landed in `src/notebooklm/_chat_wire.py` (the code moved out of
`decoder.py` during a recent refactor — `decoder.py` handles non-chat
RPCs, `_chat_wire.py` handles the streamed chat parser). Added a
companion `_raise_chat_transport_error_frame` helper paralleling the
existing `_raise_chat_error_frame` (sibling fix to upstream PR #1219,
which closed the `"er"` frame silent-skip path).

Local verification:
- 3 new unit tests pass + 30 existing tests still pass in
  `tests/unit/test_streaming_chat_wire.py`
- 6,284 of 6,292 unit tests pass (8 Windows-symlink failures unrelated)
- `ruff format --check .` + `ruff check .` + `mypy` on the changed
  file all clean

Submission package at
`C:\Users\james\Desktop\GANYMEDE_FINAL\PROJECT_GANYMEDE\notebooklm-py-pr\`:
- `HOW_TO_SUBMIT.md` — step-by-step first-time-PR guide
- `PR_DESCRIPTION.md` — ready-to-paste PR body, matches upstream tone
- `0001-fix-chat-surface-e-transport-error-frames-as-ChatErr.patch` —
  portable backup of the commit

Operator submission steps: see `HOW_TO_SUBMIT.md`. Crosses the
"publishing public-facing" autonomy gate; held for explicit operator
action.

**Followup when the PR merges upstream:** Ganymede's
`app/services/notebooklm/client.py` raw-HTTP-body-on-empty-response
diagnostic logging becomes redundant (the SDK will raise `ChatError`
directly). Leave in place as defence-in-depth or clean up — small chunk
for after the merge.

---

### ~~P1-02 · Powell-sound Bridge null test~~ ✅ SHIPPED 2026-05-31

**Classification: "valid catches" — 4 missed bridges, 0 speculative.**

The Bridge passes its null-test discipline cleanly (no over-production)
AND surfaces real catches the canonical Powell run missed. Most severe:
the Engine's "Renovation-Cause Pincer" Strategic Lasso relied on a DOJ
probe that Silo D8 explicitly documented as already closed — a
temporal-state error the Bridge would have caught at the time.

Cross-scenario evidence for the orthogonal-lenses claim now spans three
substrates (Amnesia, LMArena, Powell) with zero Bridge↔Auditor overlap.

Run record: [`docs/experiments/runs/Powell_Bridge_Null_Test.md`](docs/experiments/runs/Powell_Bridge_Null_Test.md).
Driver: [`scripts/powell_bridge_null_test.py`](scripts/powell_bridge_null_test.py).
Artifacts: [`docs/experiments/runs/Powell_Bridge_Null_Test_Artifacts/`](docs/experiments/runs/Powell_Bridge_Null_Test_Artifacts/).

Updates: `docs/concepts/Bicameral_Convergence.md` "Powell-sound robustness"
pending item closed; `docs/concepts/Framework_Cleanup_Hypothesis.md`
gains a tenth empirical evidence entry referencing the DOJ-probe
temporal-state error.

---

### ~~P1-03 · Quantify Stroke 1 CTA-leak rate~~ ✅ SHIPPED 2026-06-01

Observed leak rate: 3 / 7 ≈ 43% (consistent with the operator's standing ~50% estimate). Stroke 1's tail-CTA persists *after* the 2026-05-25 persona-tightening — explicit persona-text prohibition is not overriding NotebookLM's substrate behavior. Documented in [`docs/learnings/Iterative_Operational_Learnings.md`](docs/learnings/Iterative_Operational_Learnings.md) § 4 "Persona CTA-suppression effectiveness" with sample table + methodology caveats + recommended mitigation.

**Recommended mitigation:** post-process strip (precision-targeted regex on canonical CTA shapes applied at orchestrator stroke-assembly boundary, after the last FINAL RESOLUTION capstone marker). Preserves raw response for forensics; cleans the operator-facing surface. Surfaces as P1-03b below.

**Key carryforward finding:** the CTA-leak persistence is empirical evidence that persona text changes are not the right lever for substrate-behavior shaping — same lesson as the Framework Cleanup Hypothesis's "corpus dominance overwhelms persona" finding.

### P1-03b · Implement CTA-suppression post-processor (follow-up to P1-03)

Implementation chunk for the mitigation recommended by P1-03.

**Done when:**
- New helper `_strip_trailing_cta(raw_response: str) -> tuple[str, str | None]` lives in `app/services/orchestrator.py` (or `app/services/notebooklm/client.py`). Match against canonical CTA-start patterns; if found in the final paragraph (after the last `### FINAL` / `**Final Resolution**` / equivalent capstone marker), slice it off.
- Wired into the synthesize-stroke return path so the UI receives the cleaned text and the session state preserves both `cleaned` and `stripped_cta` for forensic visibility.
- Verified against the three confirmed leak phrases from P1-03's table (the *"Would you like me to run a web search..."* / *"Shall I initialize a Bayesian Network projection..."* / *"Would you like me to elaborate..."* shapes) as test cases.
- Engine persona text left in place as defense-in-depth (don't fight one battle on two fronts).

**Files touched:** `app/services/orchestrator.py` or `app/services/notebooklm/client.py`; possibly `app/contracts.py` if a new field is added to StrokeResult for the stripped CTA.

**Estimated effort:** ~30 minutes. No NotebookLM calls.

---

### P1-04 · Bridge notebook lifecycle decision

Auto-provisioned Bridge notebooks aren't auto-deleted after the iterate
run. For long-lived ops, this accumulates clutter.

**Done when:**
- Survey current Bridge notebooks in the operator's account
  (`GET` against the NotebookLM dashboard or via a script). Quantify
  the clutter.
- Decide: auto-cleanup by default / opt-in via `cleanup_bridge_notebook`
  flag / operator-managed.
- If "opt-in flag": implement it in `IterateRequest` and
  `run_iterative_engine`.
- Log the decision in `docs/history/Architecture_History.md` as a
  milestone 39 entry.

**Files touched:** Possibly `app/v2_routes.py`, `app/services/orchestrator.py`,
`docs/history/Architecture_History.md`.

**Estimated effort:** ~1 hour including the survey.

**Operator-gated step:** the lifecycle decision itself. Claude proposes
a default; operator picks if they care.

---

### ~~P1-05 · Predictions bulletin board~~ ✅ SHIPPED 2026-05-26

Commit `581b5b6` + drive-by TS fixes in `90e70dc`.

- `ganymede-ui/src/data/predictions.ts` — typed ledger seeded with
  the LMArena prediction (audited + Bridge-extended, medium-high
  confidence, resolves 2026-06-30).
- `ganymede-ui/src/app/predictions/page.tsx` — bulletin board page
  with status pills, countdown subcomponent, falsification-triggers
  display, run-record link-out.
- `ganymede-ui/src/app/page.tsx` — top-right Predictions link with
  pending-count badge.
- Bonus: fixed two pre-existing TS errors that were blocking
  `next build` (GravityWell material type, LithographyView
  JSX.Element).

Verified: build produces three static routes (/, /predictions,
/_not-found) prerendered. Type-check clean.

---

## NEXT UP — preview of upcoming phases

After P1 exit criteria are met, surface these for operator approval
before promoting to ACTIVE.

### Silo 2 Phase E1: Bicameral Convergence Level 2 design

Build `run_bicameral_loop()` with the five mandatory operator control
surfaces. Architectural spec already locked in
`docs/concepts/Bicameral_Convergence.md`. Multi-chunk phase:

- E1-01: `POST /api/v2/sessions/{id}/cancel` endpoint + loop-checks-cancel-flag plumbing
- E1-02: New SessionEventType entries for the bicameral loop (per the spec)
- E1-03: `run_bicameral_loop()` orchestrator method, sequential mirror-bounce, hard iteration cap, inter-iteration delay
- E1-04: Convergence-criterion implementation (no-new-STRUCTURAL / resolution-stable-2x / iteration-cap)
- E1-05: Frontend live-progress UI (extends DispatcherPanel) — iteration counter, current side, cancel button visible
- E1-06: First live run on a documented test scenario; results into a new run record

### ~~Silo 3 Phase M1: Foundations corpus deep-read~~ ✅ SHIPPED 2026-06-01 (commit pending)

- M1a (foundations deep-read): all 14 files in `docs/foundations/` tagged with per-primitive KEEP/DROP/DE-EMPHASIZE in [`docs/scratch/2026-05-31-M1-foundations-deep-read.md`](docs/scratch/2026-05-31-M1-foundations-deep-read.md) (commit `221db90`).
- M1b (synthesis + recommendation): canonical partition doc shipped at [`docs/concepts/Framework_Kernel_vs_Scaffolding_Partition.md`](docs/concepts/Framework_Kernel_vs_Scaffolding_Partition.md). Recommendation: **PROCEED to M2 leaner-corpus side-by-side test.** Risk #1 (tangled partition) and Risk #2 (hidden load-bearing scaffolding) both trend LOW; Risk #3 (framework substance vs. domain fit) remains open and only M2's empirical test discriminates.

**Operator-gated next step.** Promoting M2 to ACTIVE depends on operator sign-off on the partition doc's PROCEED recommendation. The leaner-corpus build is a major scope shift (the canonical Engine's grounding moves), so this isn't autonomous-territory.

### Silo 3 Phase M2: Leaner-corpus side-by-side test (NEXT — operator-gated)

Awaiting operator approval of the M1 PROCEED recommendation. Per the partition doc's "Proposed M2 design":

- M2-01: Build a leaner sibling notebook of the canonical Engine (re-upload curated subset of `docs/foundations/` excluding Groups 7/8/9/12 of the partition; surgical replacement of Math_Formalization § 2.1 labeled 9-tuple with abstract metric subspaces; persona reused verbatim)
- M2-02: Run Powell, Tokenized Land, 60-Second Amnesia, Genie Giant-Slayer, and LMArena scenarios against BOTH the canonical Engine and the leaner sibling
- M2-03: Apply the evaluation criteria (PRESERVE Powell-class wins; REDUCE Amnesia/LMArena dimensional-greed failures; NEUTRAL Stroke 1 length drop)
- M2-04: Write the side-by-side test report; operator decides on promotion to canonical (operator-gated — major scope shift)

### Silo 1 Phase P2: 2026-06-30 LMArena prediction validation

Calendar-gated. Fires on or near 2026-06-30.

- P2-01: Pull leaderboard rank + Polymarket resolution price
- P2-02: Update Run 06 record with outcome + classification

---

## COMPLETED ARCHIVE

Historical record. Phases get moved here with a date when they close.
Atomic chunks within an active phase get struck-through inline above,
not moved here — only whole phases archive.

### Milestone 38 (2026-05-26) — Bicameral Convergence Level 1 wired into /iterate

Strictly speaking this was the protocol-adoption milestone's
predecessor and shipped before this file existed, but archiving here
for continuity:

- IterateRequest extended with include_bridge + bridge_notebook_id
- provision_bridge_notebook orchestrator method (extracted, DRY)
- run_iterative_engine branches on include_bridge; auto-provisions
  when no notebook ID supplied
- ITERATIVE_BICAMERAL_RESYNTHESIS_TEMPLATE with two audit blocks,
  budget-split 900/600 Auditor/Bridge
- audit_with_bridge fail_session_on_error flag for graceful fallback
- StrokeResult.audit_kind field for UI distinction
- DispatcherPanel + RunnerPanel: Bridge toggle, Stroke 2b rendering
- Backward-compat and Bicameral end-to-end both verified live

Commit: `97f9101`. Run record:
`docs/history/Architecture_History.md` § milestone 38.

### Milestone 40 (2026-05-31) — auto_relogin port + Powell Bridge null test

- **P1-06 auto_relogin ported from Z-SPAN** (commit `d809914`).
  Closes the recurring "cookies expired, re-auth manually" interruption
  for the steady-state case (Playwright profile still signed in to
  Google). Wired into backend startup auto-recovery + new
  `POST /api/v2/auth/auto-relogin` endpoint + reinitialize path.
  Smoke-tested live this session: cold-start with expired cookies
  recovered to `status=valid` + `client_initialized=true` in ~47s with
  zero manual interaction.
- **P1-02 Powell-sound Bridge null test** (commit pending).
  Classification: 4 missed bridges, 0 speculative. Bridge passes its
  null-test discipline AND surfaces real catches the canonical Powell
  run missed (notably: Engine's Strategic Lasso relied on a DOJ probe
  another packet documented as already closed). Closes
  Bicameral_Convergence.md's "Powell-sound robustness" pending item
  from milestone 33.

### Milestone 39 (2026-05-26) — Autopilot Protocol adopted + Predictions bulletin board

- Adopted the Autopilot Protocol (commit `2a458c2`). Three new
  contract docs at repo root: CLAUDE.md (operating manual),
  ROADMAP.md (phase-by-phase plan by silo), TASKS.md (atomic-chunk
  ledger — this file). docs/history/Architecture_History.md
  continues as the append-only decision log.
- P1-05 predictions bulletin board (commit `581b5b6`) — first
  autonomous chunk shipped under the protocol. New /predictions
  route in Next.js + typed predictions ledger + top-right link
  from main page. Seeded with the LMArena 2026-06-30 prediction.
- Drive-by TS fixes (commit `90e70dc`) — GravityWell.tsx material
  type cast + LithographyView.tsx JSX.Element removal. Both
  pre-existing, surfaced by running `next build` for the
  predictions chunk. Build now clean.

Run record: `docs/history/Architecture_History.md` § milestone 39.
