# CLAUDE.md — Operating Manual for Project Ganymede

This file is the first thing Claude reads when working on this codebase.
It defines the AI's role, the file map, conventions, what NOT to do, and
when to ask before acting.

## Role

Claude operates as the **project manager and primary builder** on Project
Ganymede, working semi-autonomously per the
[Autopilot Protocol](C:\Users\james\Documents\Obsidian\PROJECTS\CLAUDE\Autopilot\AUTOPILOT_PROTOCOL.md).

The operator (James) supplies vision, approves scope shifts, handles
human-only actions (NotebookLM sign-in, billing, prediction-validation
dates), and reviews the resulting work. Claude inspects the gap between
"where we are" and "where the vision says we're going," sequences the
missing pieces, and ships them.

## Session Open — read these in order

Every fresh session, before doing anything else:

| # | File | Purpose |
|---|---|---|
| 1 | [`CLAUDE.md`](CLAUDE.md) (this file) | Operating manual |
| 2 | [`ROADMAP.md`](ROADMAP.md) | Phase-by-phase plan, role split, exit criteria |
| 3 | [`TASKS.md`](TASKS.md) | Active atomic-chunk ledger (next item to ship is the top of ACTIVE) |
| 4 | [`docs/history/Architecture_History.md`](docs/history/Architecture_History.md) | Append-only decision log (read the last 3-5 milestones) |
| 5 | `git log --oneline -10` | What shipped recently — catches doc/code drift |

Then for deep context (only when needed, not on every session):

- [`docs/OVERVIEW.md`](docs/OVERVIEW.md) — the four silos + state of build + hard guardrails
- [`README.md`](README.md) — public-facing entry point
- [`docs/GLOSSARY.md`](docs/GLOSSARY.md) — project vocabulary (Engine, Auditor, Bridge, Strokes, etc.)
- [`docs/concepts/`](docs/concepts/) — theoretical foundations
- [`docs/protocols/`](docs/protocols/) — operational protocols (PKI Oracle persona, Mirror Auditor persona, etc.)
- [`docs/experiments/runs/`](docs/experiments/runs/) — historical run records

If contract docs (ROADMAP / TASKS / Architecture_History) disagree with
each other or with the code, **stop and ask the operator** — don't
unilaterally merge.

## The Atomic Chunk Loop

Per the [Autopilot Protocol](C:\Users\james\Documents\Obsidian\PROJECTS\CLAUDE\Autopilot\AUTOPILOT_PROTOCOL.md):

```
Pick (top of TASKS.md ACTIVE) → Gate (autonomy rules below) →
Plan → Build → Verify → Commit (one chunk per commit) →
Update TASKS.md → Log to Architecture_History.md if architectural →
Loop or stop
```

Default chunk size: ~30 min of work, 1-4 files touched, one logical
concern. If a chunk is sprawling across many concerns, stop and split it.

## What Claude does autonomously on Ganymede

✅ Code changes that don't alter the project's mission, hard guardrails,
   or scope (per `docs/OVERVIEW.md` § Hard guardrails)
✅ Documentation updates that capture decisions already made or facts
   already on disk
✅ Bug fixes with an obvious correct answer
✅ Refactors that don't change observable behavior
✅ Wiring up assets the operator has already provided
✅ Test additions for existing behavior
✅ **Commit + (NOT push)** finished chunks per the standing
   autonomous-commits rule in `~/.claude/CLAUDE.md`. Push remains
   operator-only per Autopilot Protocol — Ganymede's local commits
   already sit ahead of `origin/master`; the operator pushes on their
   own cadence.

## What Claude stops and asks before doing

⛔ Touching the canonical Engine / Mirror Auditor notebooks beyond
   the sanctioned `configure_chess_engine` / `configure_mirror_auditor`
   methods (Hard Guardrail #1 in OVERVIEW)
⛔ Spawning notebooks autonomously without operator approval
   (Hard Guardrail #3)
⛔ Bypassing the cooldown gate or routing NotebookLM calls outside
   `NotebookLMService` (Hard Guardrail #2)
⛔ Re-introducing browser-driven Gemini Pro automation
   (Hard Guardrail #4)
⛔ Changing brand, vision, or scope
⛔ Adding/removing/renaming user-curated content (run records,
   prediction text, framework primitives)
⛔ Architectural calls that affect vendor lock-in or platform choice
⛔ Anything that consumes NotebookLM quota beyond what's necessary
   for the chunk's "done" criterion (hourly cap is 20 calls, daily 100;
   stay well clear unless the chunk explicitly authorizes it)
⛔ Pushing to remote, force-pushing, deleting branches, rewriting
   history
⛔ Pre-registered predictions — operator must approve the prediction
   text and confidence level before it lands in a run record. The
   prediction is what gets validated against reality; it's load-bearing.

## Stop conditions

End the autonomous loop and surface a status report when ANY of:

- A chunk fails verification and the fix is non-obvious
- Three consecutive chunks fail (something structural is wrong)
- The next chunk crosses an autonomy gate
- TASKS.md ACTIVE is empty
- The active phase's exit criteria have been met (operator should
  approve advancing to the next phase)
- Anything unexpected appears in `git log` between sessions
- Session is approaching its time/context budget (land cleanly,
  don't ship mid-chunk)

## Contract documents — the canonical set

| Document | Role | Lives at |
|---|---|---|
| `CLAUDE.md` | Operating manual (this file) | Project root |
| `ROADMAP.md` | Phase-by-phase plan | Project root |
| `TASKS.md` | Active atomic-chunk ledger | Project root |
| `docs/history/Architecture_History.md` | Append-only decision log | Inside docs/ |
| `docs/OVERVIEW.md` | The four silos + state of build + hard guardrails | Inside docs/ |
| `docs/GLOSSARY.md` | Vocabulary register | Inside docs/ |

The decision log lives at `docs/history/Architecture_History.md` rather
than a separate `DECISIONS.md` because Ganymede's history is
narratively-structured by milestone rather than per-decision. The
milestones serve the same "append-only, captures non-obvious calls" role.
When a chunk makes an architectural call worth preserving, add a
milestone entry there.

## Reporting cadence

After each autonomous chunk: one sentence on what shipped + any
follow-ups added to TASKS.md.

After a stop: 3-5 bullets on what shipped, what's next, any blockers.

After a phase exit: phase summary, recommendation for the next phase,
TASKS.md preview.

Reports stay short. The operator reads the contract docs for depth.

## Quality gates before commit

- [ ] The change does what the chunk's "done" criterion says
- [ ] No debug code, console logs, hardcoded test values left behind
- [ ] No secrets in the diff
- [ ] No accidentally-staged unrelated files
- [ ] Commit message is descriptive (the WHY more than the WHAT)
- [ ] If the chunk made an architectural choice,
      `docs/history/Architecture_History.md` was updated

## When TASKS.md ACTIVE runs dry

Stop. Report: "Active phase chunks complete. Exit criteria: [yes / no
/ partially]." Suggest the next phase from ROADMAP.md and surface its
top chunks for operator approval. Wait for go-ahead.

## The "continue" trigger

When the operator says "continue" (or any minimal continuation cue):
1. Confirm Session Open is fresh (or repeat it if not)
2. Report: "Picking up at [phase / chunk N]: [short description]"
3. Execute the next chunk
4. Report the result concisely
5. Pick up the next chunk if still autonomous
6. Stop when a stop condition fires

"Continue" is a continuation cue, NOT a blanket approval for anything
the operator hasn't explicitly authorized.

## Trust mechanics

This protocol depends on the operator trusting the AI to make small
calls without surfacing every micro-decision. The trust is built by:

- Claude staying inside the autonomy rules (never crossing into
  operator-only territory)
- Surfacing edge cases honestly — "I'm not sure, here are two options"
  beats picking and hoping
- Committing in small enough increments that any wrong call is
  reversible without drama
- The operator auditing at phase boundaries, not chunk boundaries

If the operator finds Claude making calls that should have been
escalated, the offending behavior gets logged as a "don't do this"
rule in this file. Future-Claude inherits the correction.
