# TASKS — Active Atomic-Chunk Ledger

The next thing Claude ships is the top item of ACTIVE.

Last updated: 2026-05-26 (post-milestone 38 commit).

> **How this file works** — see
> [`CLAUDE.md`](CLAUDE.md) § "The Atomic Chunk Loop" and the
> [Autopilot Protocol](C:\Users\james\Documents\Obsidian\PROJECTS\CLAUDE\Autopilot\AUTOPILOT_PROTOCOL.md)
> § "The Active-Todo File Contract". Sections: ACTIVE (current work,
> ordered), NEXT UP (preview of upcoming phases, lower granularity),
> COMPLETED ARCHIVE (historical record).

---

## ACTIVE — Silo 1 Phase P1: Bridge robustness + operational hygiene

The current chunk queue. Top item is the next thing to ship.

### P1-01 · Upstream notebooklm-py PR for the `[["e",4,null,null,N]]` envelope

The SDK's `decode_response` falls through to "no answer extracted" on
this Google-internal RPC error structure, masking real failures as
empty strings. The post-milestone-37 work added always-on raw-HTTP-body
logging so the project sees the envelope, but the SDK still doesn't.

**Done when:**
- Pulled the upstream `notebooklm-py` repo as a worktree or sibling clone.
- Patched `notebooklm/rpc/decoder.py` to recognize the envelope and
  raise `ChatError` with a structured message.
- Local test: feed a known-bad-prompt response through `decode_response`
  and confirm `ChatError` is raised.
- PR drafted (not necessarily submitted — operator decides on submit).

**Files touched:** `notebooklm/rpc/decoder.py` (upstream),
`notebooklm/exceptions.py` (upstream — if a new error class is needed).

**Estimated effort:** 1-2 hours including upstream repo orientation.

---

### P1-02 · Powell-sound Bridge null test

Does Bridge produce "0 missed bridges" on known-sound Engine output, or
does it over-produce SPECULATIVE bridges on sound input? Either result
is informative.

**Done when:**
- Pick a Powell-class Stroke 1 as the input. **Default pick:** the
  Powell Cleanroom canonical Stroke 1 (preserved in
  `docs/experiments/runs/Powell_Cleanroom/`). Alternative if operator
  prefers: Tokenized Land or Genie Giant-Slayer.
- Provision a Bridge notebook with the Powell substrate.
- Fire `/sessions/{id}/bridge-audit` with that Stroke 1 as
  `target_text`.
- Document the Bridge's output. Classify: "0 missed bridges" / "missed
  bridges with valid catches" / "over-produced speculative bridges".
- Write a short run record at
  `docs/experiments/runs/Powell_Bridge_Null_Test.md`.

**Files touched:** new run record; possibly `docs/protocols/Connection_Bridge_Persona.md` if the test surfaces persona tuning.

**Estimated effort:** ~30 min wall time for the test + write-up
(15 min for Bridge provision + 1 min audit + write-up).

**NotebookLM call budget:** ~15 calls.

---

### P1-03 · Quantify Stroke 1 CTA-leak rate

Stroke 1 still leaks "Would you like me to…" CTAs in ~50% of runs
despite the persona's explicit prohibition. Quantify first; mitigate
second.

**Done when:**
- Inspect Stroke 1 raw_response from the last ~10 runs (in
  `backend.log` or stored session state if available).
- Count how many end with a CTA-shaped sentence.
- Document the rate in
  `docs/learnings/Iterative_Operational_Learnings.md` under a new
  "Persona CTA-suppression effectiveness" section.
- Recommend a mitigation: stronger persona phrasing / post-process strip
  / `response_length=SHORTER` / accept-and-document.

**Files touched:** `docs/learnings/Iterative_Operational_Learnings.md`.

**Estimated effort:** 30 min. No NotebookLM calls (uses logged data).

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

### P1-05 · Predictions bulletin board (operator opt-in)

A `/predictions` route in the UI showing pre-registered predictions as
cards with claim / mechanism / resolution-date countdown / status.
Currently we only have one (LMArena 2026-06-30), but the surface scales.

**Done when:**
- Operator approves the build (small ship; opt-in).
- New page at `ganymede-ui/src/app/predictions/page.tsx` (or wherever
  Next.js 16 wants it — check `node_modules/next/dist/docs/` first).
- Parses predictions from a static JSON at
  `ganymede-ui/src/data/predictions.ts` OR a new
  `GET /api/v2/predictions` endpoint that scans run records.
- Cards show: scenario one-liner, claim, mechanism, resolution date,
  countdown, status (pending / validated / falsified / inconclusive).
- LMArena prediction populated as the first card.

**Files touched:** new page file, new data file or new API endpoint,
possibly `app/v2_routes.py`.

**Estimated effort:** 1-2 hours.

**Operator-gated:** yes — opt-in. Skip if operator doesn't approve.

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

### Silo 3 Phase M1: Foundations corpus deep-read

Multi-hour focused work. Best done as a single big chunk rather than
many small ones, since the value is in the cross-foundation synthesis.

- M1-01: Read all 13 foundation files end-to-end; take notes per file
- M1-02: Build the kernel-vs-scaffolding partition table
- M1-03: Write the assessment doc; recommend proceed/refine/shelve

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
