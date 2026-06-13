# TASKS — Active Atomic-Chunk Ledger

The next thing Claude ships is the top item of ACTIVE.

Last updated: 2026-06-13 (post-milestone 51 — Run 7's structural-attractor claim validated by federal Fable 5 pull within ~24 hours of the run ship. **Project's most consequential validation event to date.** Surface bet (LMArena #1 at 6/30) structurally voided because the model isn't on the board; structural claim (safety architecture funnels Anthropic into SDS_O) confirmed via stronger expression on a different specific lever. Three-layer milestone closeout discipline added (plumbing / surface bet / structural claim) as sibling to milestone 50's wiring/output distinction. **Every claude-autonomous chunk on the current scope remains done** — Pl2-03 still operator-driven; E1-06 operator-driven; M2 operator-gated but sharper urgency post-validation; P1-01 upstream notebooklm-py PR submission is operator action; P2 LMArena 6/30 calendar gate is now a non-event for tracking (no rank data to pull, both surface bets voided). Pl2-03 first live Z-SPAN session + Pl3 Operator Lens get higher leverage post-validation. Prior-state context: post-milestone 49, Dispatcher routes Cleanroom/Genie/Offensive on real-world entities to the Universal Logic Loop harvest path; DispatcherPanel WebSocket subscription mirrors RunnerPanel so the visualizer animates as Blueprint / Oracle / Stroke events fire.)

> **How this file works** — see
> [`CLAUDE.md`](CLAUDE.md) § "The Atomic Chunk Loop" and the
> [Autopilot Protocol](C:\Users\james\Documents\Obsidian\PROJECTS\CLAUDE\Autopilot\AUTOPILOT_PROTOCOL.md)
> § "The Active-Todo File Contract". Sections: ACTIVE (current work,
> ordered), NEXT UP (preview of upcoming phases, lower granularity),
> COMPLETED ARCHIVE (historical record).

---

## ACTIVE — Silo 4 Phase Pl2: Z-SPAN as first module consumer

Z-SPAN is the named first Pl2 consumer per milestone 43. Per the operator-locked sequence (P1-03b → P1-04 → Pl3 → Pl2 final), this is the last claude-autonomous phase before the project shifts to operator-driven validation events (E1-06 live run, 2026-06-30 LMArena resolution, M2 leaner-corpus test if approved).

### ~~Pl2-01 · Persistent session state~~ ✅ SHIPPED 2026-06-08 (milestone 46)

Shipped pieces:

- **`ganymede-backend/app/services/session_store.py`** — `SessionStore` class wrapping a single-file SQLite DB. Stdlib `sqlite3` + sync-in-executor; no new third-party dep. Schema: `sessions / strokes / events / translations` tables, foreign-keyed with `ON DELETE CASCADE`. Public API: `save_session`, `load_all`, `mark_orphan_running_as_error`, `list_summaries`, `count`, `search`, `delete`. `default_db_path()` resolves to `ganymede-backend/data/sessions.db`; env override via `GANYMEDE_SESSION_DB`.
- **`app/services/session.py` wiring** — `Session(store=...)` constructor kwarg + `_persist()` async helper called from inside the lock on every mutation (`record_stroke`, `record_translation`, `complete`, `fail`, `request_cancel`). `Session.from_persisted_state(data, store)` classmethod for rehydration (bypasses `__init__`'s SESSION_CREATED emit since the persisted events list already contains it). `SessionRegistry(store=...)` + `bind_store(store)` + `rehydrate()` + `store` accessor. `create()` passes the store + persists immediately; `discard()` deletes from store too.
- **`app/main.py` startup wiring** — opens the store + binds it + rehydrates before NotebookLM init so prior sessions are visible even when auth is broken. Failure modes degrade rather than block startup. `GANYMEDE_DISABLE_SESSION_PERSISTENCE=1` opts out.
- **`GET /api/v2/sessions`** in `app/v2_routes.py` — paginated list ordered newest-first. Filters: `status`, `pathway`, `q` (substring scenario_json + final_text), `limit` (1-200), `offset`. Returns `SessionSummary` rows with the full `Scenario` object + first-200-char `final_text_preview`.
- **`GET /api/v2/sessions/{id}/strokes`** — full strokes list + Pl3 translations keyed by `{stroke_number}:{register}` in the same payload.
- **`.gitignore`** updated to exclude `ganymede-backend/data/`.

Verified end-to-end via FastAPI TestClient lifecycle: create session via registry → record stroke → complete → list shows total 1 → simulated process death (`_sessions.clear()` + drop `_store`) → fresh boot → `rehydrate()` reports 1 prior session → GET / strokes / state all surface the rehydrated session with original `final_resolution` intact. Orphan-rescue path verified separately: a session left in `running` is flipped to `error` with a synthetic ERROR event appended so the events endpoint stays consistent.

### ~~Pl2-02 · Z-SPAN consumer-spec walkthrough doc~~ ✅ SHIPPED 2026-06-08 (rolled into milestone 47)

Shipped pieces:

- **`docs/integration/examples/zspan_consumer.md`** — full walkthrough doc following the prisonbreak_consumer template but adapted for Z-SPAN's session-as-consumer shape. Sections: model (session-as-consumer vs PrisonBreak's app integration), hook point (conceptual — which questions are Ganymede-shaped), what Z-SPAN naturally provides (operator-curated Truth Packets, not RAG-derived), what Z-SPAN wants back (Strategic Lasso / Incomprehensible Move / audience-facing translation), mapping to Ganymede API (pathway selection table, Truth Packet shape per type, iterative vs Bicameral Level 2 selection, Operator Lens register selection), concrete worked walkthrough (curl-by-curl for the Granicus positioning question), persistent-session pattern (GET /sessions + GET /strokes, the "build on prior strokes" manual workflow), courier-protocol usage cross-reference.
- **`docs/integration/examples/README.md`** — Z-SPAN row added to the consumer table.
- **`docs/integration/operator_courier_protocol.md`** § Related — link to zspan_consumer.md updated from "once written" to live cross-reference.
- **ROADMAP.md** § Pl2 deliverables — Z-SPAN integration spec line struck as shipped.

**Cross-cutting principle surfaced for the general API:** Z-SPAN's case validates that some consumers are sessions, not apps. The v2 API has to be ergonomic from both shapes. Pl2-01 persistent state + Pl3 Operator Lens + the closed-RAG-sphere discipline are what make the session-as-consumer shape viable for long-running strategic-planning work.

### ~~Pl2-02b · Canonical-API-doc parity for Pl2-01 endpoints~~ ✅ SHIPPED 2026-06-09 (milestone 47)

`docs/integration/consuming_the_v2_api.md` predated Pl2-01. Updated to:

- TL;DR now mentions persistence as first-class.
- § Session persistence rewritten from "(or lack of)" to the Pl2-01 reality (save-on-mutation, rehydrate-on-startup, orphan-rescue, opt-out env vars, schema overview).
- New § `GET /api/v2/sessions` reference entry with the full query-param table + response shape.
- New § `GET /api/v2/sessions/{id}/strokes` reference entry.

Future consumers reading the canonical reference now discover the Pl2-01 surface without having to read zspan_consumer.md.

### ~~Pl2-02c · BridgeNotebookRegistry persistence parity~~ ✅ SHIPPED 2026-06-09 (milestone 47)

Symmetric sister chunk to Pl2-01's SessionStore. The `BridgeNotebookRegistry` was in-memory-only; restart orphaned its metadata even though the actual notebooks persist in NotebookLM. Long-running Z-SPAN sessions span weeks → bridge notebooks live weeks → registry has to outlive the process.

Shipped:

- `BridgeNotebookRegistry(persistence_path=...)` + `bind_persistence(path)` + `load_from_disk()` + `_persist_locked()` atomic-write helper in `ganymede-backend/app/services/bridge_registry.py`.
- JSON-file backing (vs SQLite — small N, no querying beyond `list_all`, simpler).
- `default_persistence_path()` resolves to `ganymede-backend/data/bridge_registry.json` (env override: `GANYMEDE_BRIDGE_REGISTRY_DB`).
- `app/main.py` startup wiring alongside the SessionStore init.
- Corrupt-file handling: log warning + start empty; next mutation rewrites.

Verified across simulated restarts via TestClient lifecycle.

### Pl2-03 · First live Z-SPAN strategic-planning session (operator-driven)

Run a real Z-SPAN positioning question end-to-end through `POST /api/v2/managed-run`. Write up the run record.

**Done when:**
- Z-SPAN session produces a real strategic-planning question + 3-5 Truth Packets drafted with the operator.
- One `POST /api/v2/managed-run` call drives dispatch → create → iterate → translate → complete in one shot.
- Resolution returned to Z-SPAN; `session_id` captured into Z-SPAN's decision-log.
- Run record at `docs/experiments/runs/Z-SPAN_First_Strategic_Session.md` documenting scenario, strokes, observed wall time, dispatcher confidence + rationale, register used, and any operator observations.
- Architecture_History milestone 49 capturing the first live consumer-driven run (or rolled into milestone 48 if it happens in the same arc).

**Operator-gated.** Requires Z-SPAN's session to drive the question. James pastes the new `C:\Users\james\Desktop\Z-SPAN_Handoff_v2.md` as Z-SPAN's first message; Z-SPAN reads it and starts drafting the first question with James.

---

## DEFERRED — Silo 2 Phase E1: Bicameral Convergence Level 2 build

**Priority elevated by milestone 42 (2026-06-05) — Anthropic's real-world pause call confirmed the Bridge's mechanism-category catch from Run 7 but exposed the architectural gap: Levels 2/3 don't exist, so the Engine itself never made the specific prediction.** The gap is engineering, not research (architectural spec locked in [`docs/concepts/Bicameral_Convergence.md`](docs/concepts/Bicameral_Convergence.md)). Build the loop, and the next prediction of this shape produces the specific synthesis, not just the mechanism-category gesture.

**Status:** all 5 claude-shippable chunks (E1-01 through E1-05 + the E1-06 endpoint prep) landed 2026-06-06 (commits `392229c` through `1e0f00e`). Only E1-06 (first live run on a documented test scenario) remains and is operator-driven (requires live NotebookLM session + operator-approved scenario).

### ~~E1-01 · `POST /api/v2/sessions/{id}/cancel` endpoint + loop-checks-cancel-flag plumbing~~ ✅ SHIPPED 2026-06-06

Shipped pieces:
- `SessionEventType.SESSION_CANCELLED` added in `app/contracts.py` (E1-02 partial — the cancel event landed alongside).
- `Session.cancel_requested: bool` flag + `request_cancel(message)` async method on Session (`app/services/session.py`). Idempotent state transition to `"cancelled"` terminal status; emits `SESSION_CANCELLED` synchronously.
- New `SessionCancelledError(where, session_id)` exception class + `_check_cancelled(session, where)` method on `GanymedeOrchestrator` (`app/services/orchestrator.py`). Distinct from `asyncio.CancelledError` on purpose. Four check points wired into `run_iterative_engine`: `before-stroke-1`, `before-stroke-2`, `before-bridge-provision`, `before-stroke-2b-bridge`, `before-stroke-3`. The Bridge try/except now re-raises `SessionCancelledError` rather than swallowing it as a Bridge transient.
- New `POST /api/v2/sessions/{id}/cancel` endpoint in `app/v2_routes.py` returns `CancelResponse(cancelled, session_id, state)`. Idempotent — returns `cancelled=False` if already terminal (no 409 raised for the race). 404 for unknown session.
- `/iterate` endpoint catches `SessionCancelledError` and returns 200 with `session.strokes` (partial progress preserved).
- WS stream recognizes `SESSION_CANCELLED` as terminal alongside `SESSION_COMPLETE` and `ERROR`; drains + closes cleanly.

Smoke-test status: 4 modified Python files compile cleanly (`py_compile`). Live smoke-test (curl cancel mid-iterate, verify clean termination + WS event delivery) deferred to next session-with-backend-running.

### ~~E1-02 · New SessionEventType entries for the bicameral loop~~ ✅ SHIPPED 2026-06-06

Full set landed across E1-01 (SESSION_CANCELLED) and E1-02 (BICAMERAL_ITERATION_START, BICAMERAL_ITERATION_END, BICAMERAL_CONVERGED, BICAMERAL_HARD_CAP_REACHED) in `app/contracts.py`. Each event carries the payload fields the frontend needs for live rendering (iteration index, max_iterations, stroke numbers, new_bridges_surfaced, convergence criterion). WS stream recognizes all terminal events.

### ~~E1-03 · `run_bicameral_loop()` orchestrator method~~ ✅ SHIPPED 2026-06-06

Shipped in `app/services/orchestrator.py`:

- `run_bicameral_loop(session, truth_packets, *, max_iterations=5, min_inter_iteration_delay=5.0, bridge_notebook_id=None)` orchestrator method
- Closed-loop Engine ↔ Bridge mirror-bounce with iteration cap
- Bridge auto-provisioning on iteration 1, reuse across all subsequent iterations
- Cancel-flag checks at iteration boundaries (top + before Bridge + after delay)
- Bridge transient handling: terminate loop early with partial results (no Auditor fallback in Level 2 since the loop needs Bridge findings to continue)
- New `ITERATIVE_BICAMERAL_LOOP_TEMPLATE` for iteration-2+ re-synthesis (Bridge-only friction; no Auditor in the loop)
- Count-based convergence detection via `_count_bridges_in_audit(raw) -> int` (regex match on `Bridge N (STRUCTURAL|IMPLIED)`; SPECULATIVE excluded)
- Convergence-count regex verified against Powell (4), Amnesia (3), empty (0), SPECULATIVE-only (0), case-insensitive, no-bold-markers, mixed-tier cases — all pass
- Inter-iteration delay (operator-tunable 2-30s, default 5s) + cancel check after delay
- BICAMERAL_ITERATION_START emitted at top of each iteration; BICAMERAL_ITERATION_END at bottom with payload; BICAMERAL_CONVERGED on clean termination; BICAMERAL_HARD_CAP_REACHED on cap hit

Smoke-test status: syntax-check + AST inspection confirm all additions present + structurally correct. Live end-to-end smoke-test (a real run on a documented scenario) is E1-06's scope.

### ~~E1-04 · Convergence-criterion refinement~~ ✅ SHIPPED 2026-06-06

Shipped in `app/services/orchestrator.py`:

- **`_is_audit_substantive(raw) -> bool`** — fallback heuristic defending against false convergence on non-canonical Bridge output. Length threshold (300 chars) + bridge-flavored-token count (≥2 distinct tokens from "missed" / "connection" / "bridge" / "fails to" / "ignores" / "overlooks" / etc.). Returns True if Bridge produced substantive content even without canonical labels. Verified: LMArena Run 7 stream-of-consciousness output (734 chars, multiple flavor tokens) → True. Empty audit → False. Short non-content → False.
- **`_extract_final_resolution_section(raw) -> str`** — looks for canonical `FINAL RESOLUTION` / `FINAL 9D RESOLUTION` / `RESOLUTION` headers via regex; falls back to last 30% of text if no header found.
- **`_normalize_for_similarity(text) -> str`** — strips markdown, collapses whitespace, lowercases. For similarity comparison purity.
- **`_resolution_stable(prior, current, threshold=0.85) -> bool`** — extracts FINAL RESOLUTION from both syntheses, normalizes, computes `difflib.SequenceMatcher.ratio()`, compares against threshold. Verified: near-identical syntheses (0.887) → stable. Materially different (0.413) → not stable. Threshold env-tunable via `GANYMEDE_RESOLUTION_STABLE_THRESHOLD`.
- **Wired into `run_bicameral_loop`** convergence-detection block:
  - Criterion 1: `no_new_structural` — fires only if count==0 AND audit is NOT substantive (the fallback guard prevents false-converging on non-canonical output).
  - Criterion 2: `resolution_stable` — fires when count > 0 but the Engine's FINAL RESOLUTION is functionally unchanged across iterations (handles the case where Bridge keeps surfacing connections but Engine has stabilized).
  - Logs which criterion fired; `BICAMERAL_CONVERGED` payload's `criterion` field reports `"no_new_structural"` or `"resolution_stable"`.

Combined behavior verified: LMArena Run 7 Bridge output (which would have false-converged under E1-03's count-only logic) now correctly treats as ambiguous-no-convergence; loop continues to next iteration.

Defense layers vs. false convergence:
1. Pre-E1-04: count-only — false-converges on non-canonical Bridge output.
2. Post-E1-04: count-based AND substantiveness check together — won't false-converge even when Bridge persona produces stream-of-consciousness. Plus the resolution-stable backstop for "Engine has stabilized but Bridge hasn't" case.

### ~~E1-05 · Frontend live-progress UI~~ ✅ SHIPPED 2026-06-06

Shipped:

- **New `ganymede-ui/src/components/BicameralProgressIndicator.tsx`** — self-contained presentational component. Takes `BicameralProgressState` (running, currentIteration, maxIterations, currentSide, newBridgesSurfaced, convergenceCriterion, hardCapReached) + `onCancel` + `sessionId` props. Renders:
  - **Live progress**: iteration counter (`"Iteration N of M"`), animated side indicator (Engine synthesizing / Bridge auditing), last-iteration bridge count, **cancel button** wired to the parent's onCancel handler.
  - **Terminal CONVERGED**: emerald check-icon block with criterion label (`"No new structural bridges surfaced"` / `"Final resolution stabilized across iterations"`) + iteration count.
  - **Terminal HARD_CAP_REACHED**: amber alert block with "hit hard cap without converging" message + iteration count.
  - **Idle**: renders null (no DOM presence when not in a bicameral context).
- **`IDLE_BICAMERAL_STATE` constant exported** — convenient initial value for parents to seed their state hook.
- **`RunnerPanel.tsx` wired**:
  - SessionEvent type union extended: `session_cancelled`, `bicameral_iteration_start`, `bicameral_iteration_end`, `bicameral_converged`, `bicameral_hard_cap_reached`.
  - New `bicameralState` state hook seeded with `IDLE_BICAMERAL_STATE`.
  - `handleEvent` extended with 6 new event handlers (5 bicameral + 1 synthesis_complete-during-bicameral for the side flip from engine → bridge).
  - New `handleCancel` callback fires `POST /api/v2/sessions/{id}/cancel`; SESSION_CANCELLED arrives via WS and the existing terminal-event handler closes the WS + flips running to false.
  - `BicameralProgressIndicator` mounted directly above the strokes list.
  - `reset()` clears bicameralState back to IDLE.

Smoke-test status: `npx tsc --noEmit` against the project's tsconfig passes cleanly with no errors.

**DispatcherPanel deferred**: DispatcherPanel doesn't use WebSocket (it's fetch-based, blocking until /iterate returns). Wiring bicameral live-progress there requires adding a WS subscription during the /iterate call — separate work, lower priority. The RunnerPanel is the canonical operator-driven surface; Z-SPAN as Pl2 first consumer will use the v2 API directly, not the DispatcherPanel UI.

### E1-06 · First live run on a documented test scenario (operator-driven)

Run the new loop end-to-end on a scenario the operator approves; write up the run record.

**Pre-E1-06 prep landed:** the HTTP endpoint `POST /api/v2/sessions/{id}/bicameral-loop` wiring `BicameralLoopRequest` → `orch.run_bicameral_loop` is shipped in `app/v2_routes.py` (2026-06-06). `SessionCancelledError` caught and returns 200 with partial strokes per the same pattern as `/iterate`. Same response shape as `/iterate` (strokes + state).

**Done when:**
- Operator-approved test scenario selected (candidates per ROADMAP: a fresh Cleanroom-shape question similar to LMArena but different domain — non-political per standing rule).
- Backend running with a healthy NotebookLM session.
- `run_bicameral_loop` fires end-to-end via the new endpoint; converges or hits hard cap cleanly; cancel-test verified mid-loop (POST /cancel during iteration N+1 → SessionCancelledError → partial result returned, WS subscribers see SESSION_CANCELLED).
- Frontend live-progress UI verified: BicameralProgressIndicator renders iteration counter, side indicator, cancel button while running; terminal-state messaging (CONVERGED / HARD_CAP_REACHED) renders correctly.
- New run record at `docs/experiments/runs/Bicameral_Loop_First_Run.md` documenting scenario, iteration trace (per-iteration Engine + Bridge strokes), convergence outcome, observed wall time, and any persona-output observations.
- Architecture_History milestone 44 capturing what shipped + what the loop showed about the partial-validation gap from milestone 42.

**Files touched:** `docs/experiments/runs/<new-record>.md`, `docs/history/Architecture_History.md`.

**Estimated effort:** ~2-3 hours including write-up. NotebookLM call budget: ~14 for Bridge provisioning (iter 1) + 2 per iteration × ~3 iterations = ~20 calls. Plus cancel-test re-run if needed.

**Operator-gated.** Requires live NotebookLM session + operator-approved scenario. Not autonomous-territory; flag for next session where backend + auth + scenario approval are available.

---

## DEFERRED — Silo 1 Phase P1: Bridge robustness + operational hygiene

P1 has 2 of 3 exit criteria met (P1-02 Powell null test ✓, P1-03 CTA-leak quantification ✓). Remaining items deferred behind E1's elevated priority.

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

### ~~P1-03b · CTA-suppression post-processor~~ ✅ SHIPPED 2026-06-06

Shipped:
- **`_strip_trailing_cta(raw_response) -> tuple[str, Optional[str]]`** in `app/services/orchestrator.py`. Conservative trailing-paragraph strip: splits on `\n\n`, examines the last non-empty paragraph, strips leading markdown/whitespace, case-insensitive match against 13 curated CTA opener phrases ("Would you like me to", "Shall I", "Let me know", "If you'd like", "Feel free to", etc.). Refuses to strip if it would leave empty content (degenerate single-paragraph CTA case).
- **`cleaned_response` and `stripped_cta` optional fields** added to `StrokeResult` in `app/contracts.py`. `raw_response` is left untouched as source of truth; `cleaned_response` is populated only when a CTA was stripped. UI consumers display `cleaned_response ?? raw_response`.
- **Wired into all 3 StrokeResult construction sites** in `orchestrator.py`: synthesis stroke, Mirror Auditor stroke, Connection Bridge stroke. Logs at INFO when a strip happens (count of chars stripped) for ops visibility.

Verified against P1-03's 3 confirmed leak phrases + edge cases (9 test cases total):
- ✅ LMArena Run 3: *"Shall I initialize a Bayesian Network projection..."* — stripped
- ✅ LMArena Run 6: *"Would you like me to run a web search..."* — stripped
- ✅ Musk-Altman: *"Would you like me to elaborate..."* — stripped
- ✅ Powell substantive ending (no CTA shape) — NOT stripped
- ✅ Markdown-bold CTA `**Would you like me to**` — stripped (leading markdown normalizer handles it)
- ✅ Mid-paragraph CTA — NOT stripped (conservative; mid-paragraph CTAs often part of substantive content)
- ✅ Empty response — NOT stripped (no-op)
- ✅ Single-paragraph CTA-only — NOT stripped (refuse to leave empty)
- ✅ CTA after separator paragraph — stripped

Engine persona text left in place as defense-in-depth — both layers running per the P1-03 recommendation. Frontend updates to render `cleaned_response ?? raw_response` deferred as small polish chunk (the data is available on session state for forensic visibility today; UI just needs to opt-in).

---

### ~~P1-04 · Bridge notebook lifecycle decision~~ ✅ SHIPPED 2026-06-06 (milestone 44)

Operator chose **Option C — operator-managed with categorized delete-suggestions**. The system tracks auto-provisioned Bridge notebooks server-side, surfaces a categorized survey with per-row delete suggestions, and the operator handles the actual delete clicks. No auto-cleanup, no opt-in flag — explicit operator action via UI.

Shipped:
- **`ganymede-backend/app/services/bridge_registry.py`** — in-memory `BridgeNotebookRegistry` with categorization heuristic (session terminal + age + provision path → `likely_safe_to_delete` / `review` / `recently_used` + suggested action `delete` / `review` / `keep` + human-readable reason).
- **Orchestrator integration** — `provision_bridge_notebook` registers in the registry; `run_iterative_engine` + `run_bicameral_loop` + standalone `/bridge/provision` all tag with provision_path.
- **`GET /api/v2/bridge/notebooks`** survey endpoint with summary counts.
- **`DELETE /api/v2/notebooks/{id}` hook** — deregisters from registry on success.
- **`ganymede-ui/src/components/BridgeNotebookManager.tsx`** — self-contained UI panel with color-coded category badges, summary count chips, two-click confirm delete buttons, refresh button, help section.
- **`/bridge-notebooks` route** — page at `ganymede-ui/src/app/bridge-notebooks/page.tsx`.
- **`docs/history/Architecture_History.md` milestone 44** — full decision + implementation record.

Deferred follow-ups (not blocking):
- **Persistence across backend restarts.** Registry is in-memory; restart loses metadata. Actual notebooks persist in NotebookLM either way. File-backed persistence is a small follow-up candidate.
- **Operator-curated notebooks.** Notebooks created outside the orchestrator's auto-provision paths aren't tracked. Manual management via raw API calls remains the operator's responsibility there.

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

### ~~Silo 1 Phase P2: 2026-06-30 LMArena prediction validation~~ — structurally superseded 2026-06-13 (milestone 51)

Both Run 6 and Run 7 surface bets structurally voided by federal Fable 5 pull 2026-06-12. The 6/30 calendar gate becomes a non-event for tracking — Fable 5 isn't on the board, so neither "Anthropic holds #1" nor "Anthropic loses #1" resolves cleanly. The structural-claim validation already landed (see [milestone 51](docs/history/Architecture_History.md) + [`docs/experiments/runs/07_LMArena_Universal_Loop_Validation.md`](docs/experiments/runs/07_LMArena_Universal_Loop_Validation.md) § "Real-world outcome — 2026-06-12/13").

- ~~P2-01: Pull leaderboard rank + Polymarket resolution price~~ → no rank data to pull (surface bet voided).
- ~~P2-02: Update Run 06 record with outcome + classification~~ → Run 7 record carries the validation; Run 6 record optionally annotated with "structurally voided" note as low-priority cleanup chunk.

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
