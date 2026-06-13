---
name: project-autopilot-protocol
description: "Ganymede operates under James's Autopilot Protocol since 2026-05-26 (milestone 39). Contract docs at repo root: CLAUDE.md / ROADMAP.md / TASKS.md. Decision log lives at docs/history/Architecture_History.md (numbered milestones)."
metadata: 
  node_type: memory
  type: project
  originSessionId: b1fabc43-1fa7-4ec9-b300-429b7b733143
---

Ganymede adopted James's [[Autopilot Protocol]] (`~/Documents/Obsidian/PROJECTS/CLAUDE/Autopilot/AUTOPILOT_PROTOCOL.md`) on 2026-05-26 as its operating mode. Future sessions MUST follow the session-open routine before acting.

**Why:** James's instruction (2026-05-26): *"We should just use this protocol to do everything as much as you can, unless you need my input for major things and such."* The protocol formalizes how Claude operates semi-autonomously on vision-driven projects with a clear vision + roadmap. Atomic-chunk loop, autonomy rules, stop conditions, per-chunk commits, contract documents kept fresh.

**How to apply — session-open routine (always do this before any work):**

1. Read `CLAUDE.md` at the project root (operating manual)
2. Read `ROADMAP.md` (phase-by-phase plan organized by silo)
3. Read `TASKS.md` (atomic-chunk ledger — top of ACTIVE = next chunk)
4. Read the last 3-5 milestones in `docs/history/Architecture_History.md` (append-only decision log; no separate DECISIONS.md)
5. `git log --oneline -10` (catches doc/code drift)

If contract docs disagree with each other or with the code, **stop and ask** — don't unilaterally merge.

**Key autonomy posture for Ganymede specifically:**
- Commit-and-push to local origin is autonomous (per James's standing rule in `~/.claude/CLAUDE.md` § "Autonomous commits"). Pushing to remote also sanctioned for this early-stage personal repo.
- Spawning NotebookLM Oracle notebooks requires explicit operator approval (Hard Guardrail #3 in `docs/OVERVIEW.md`).
- Canonical Engine + Mirror Auditor notebooks are read-only beyond the sanctioned `configure_*` methods (Hard Guardrail #1).
- Anything that crosses "publishing public-facing" needs operator action (e.g., upstream PRs).

**Cross-references:**
- The protocol document itself: `~/Documents/Obsidian/PROJECTS/CLAUDE/Autopilot/AUTOPILOT_PROTOCOL.md`
- Ganymede's adoption: milestone 39 in `docs/history/Architecture_History.md`
- Z-SPAN is the project the protocol was first written against; structurally-similar conventions apply (see [[feedback-zspan-reference-first]] for the workflow heuristic).
