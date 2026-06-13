# HANDOFF

*Bootstrap prompt for resuming Project Ganymede work in a fresh Claude Code session after a local-folder reset. Clone this repo, open Claude Code in the cloned directory, and paste the contents of the code block below as your first chat message.*

---

## Copy-paste this into a fresh Claude Code chat

```
This is a continuation of long-running work on Project Ganymede — a strategic-physics reasoning engine grounded in a 9D theoretical framework, running as an open primitive consumed via the v2 HTTP API. Module-not-service north star. Operating under the Autopilot Protocol.

Project root: <path you cloned into>\Project Ganymede

Please ingest in this exact order before responding:
  1. CLAUDE.md (operating manual)
  2. ROADMAP.md (status table updated 2026-06-13 reflecting milestone 51 + paused experimental tracks)
  3. TASKS.md (current ACTIVE: Pl2-03 paused; experimental architecture tracks all paused — see PAUSED section)
  4. docs/history/Architecture_History.md — read the last 4 milestones carefully: 48 (/managed-run + dispatcher-as-canonical-entry-point), 49 (dispatcher routes Cleanroom on real-world entities to Universal Logic Loop), 50 (PKI Oracle harvest path unblocked end-to-end — IMPORT_RESEARCH timeout + synthesis input-cap + dispatcher multi-provider routing), 51 (Polymarket-rooted reality test — Run 7's structural-attractor claim confirmed by federal Fable 5 pull within ~24 hours)
  5. docs/experiments/runs/07_LMArena_Universal_Loop_Validation.md — the milestone-50 / milestone-51 validation run, with the 2026-06-12/13 outcome section
  6. docs/experiments/runs/06_LMArena_Anthropic_Cleanroom.md § "Real-world outcome — 2026-06-12/13" — sibling Run 6 record's surface-bet-voided annotation
  7. HANDOFF.md (this file — the bootstrap that brought you here)

Memory at ~/.claude/projects/<encoded-project-path>/memory/ auto-loads via MEMORY.md once the new session writes its first memory file (it'll auto-create on first save). The full prior-state memory is archived under .claude-archive/memory/ in the repo. You can either let auto-memory rebuild organically as you work, or restore the archive to ~/.claude/projects/<encoded-project-path>/memory/ before starting if you want full continuity. Especially load-bearing if restored:
  - project_structural_attractor_validation (milestone 51's vision-level finding)
  - project_lmarena_prediction (both surface bets voided; structural claim validated)
  - project_connection_bridge_validated (E1-06 status: PAUSED)
  - project_pl2_zspan_first_consumer (Pl2-03 status: PAUSED while Z-SPAN's cycle is busy)
  - feedback_validate_output_not_wiring (sibling methodology rule)
  - feedback_autonomous_push (Ganymede only — push after autonomous commits is not gated)

== State at handoff (2026-06-13) ==

**Project is feature-complete and validated through milestone 51.** Run 7's vector-agnostic structural claim ("safety architecture funnels Anthropic into SDS_O") was confirmed by federal Fable 5 pull within ~24 hours of Run 7 ship, via a stronger expression on a different specific lever than the framework hypothesized. Project's most consequential validation event to date.

**Experimental architecture tracks PAUSED 2026-06-13 (pause-not-delete):** M2 leaner-corpus side-by-side test, E1-06 first live Bicameral Level 2 run, Bridge audit on Universal Logic Loop output. All specs / builds / partition docs retained intact. Revisit only if the validated path starts producing failures the current discipline doesn't catch.

**Pl2-03 first live Z-SPAN strategic-planning session is PAUSED** while Z-SPAN's own development cycle is busy. Ganymede side has nothing left to build; pickup is gated on Z-SPAN's availability.

**2026-06-30 LMArena calendar gate is structurally voided** — Fable 5 isn't on the board so neither Run 6 nor Run 7 surface bet resolves cleanly.

**Backend / frontend state:** not running at handoff time. When work resumes: backend on :8000 with PYTHONIOENCODING=utf-8 + venv_312; frontend on :3007 with PORT=3007 npm run dev. `.env` contains DeepSeek key (gitignored, won't survive the clone — re-paste DEEPSEEK_API_KEY when needed).

== What's likely to bring James back ==

There's no "next chunk to ship" at handoff. Future sessions are likely only when one of these fires:

- Z-SPAN's session produces feedback or drives Pl2-03 — courier protocol at `docs/integration/operator_courier_protocol.md` covers cross-session communication
- James decides to revisit a paused architectural track (M2, E1-06, or Bridge-on-Universal-Logic-Loop)
- James decides to do P3 (next pre-registered prediction) to test whether milestone 51's structural-attractor capability generalizes
- An operational issue surfaces (NotebookLM cookies expiring, upstream notebooklm-py PR landing, etc.)

Confirm you've ingested the docs and then ask James what's brought him back. Don't assume there's a chunk waiting to be shipped.
```

---

## How to resume

1. Clone the repo: `git clone https://github.com/anitacigawet/Project-Ganymede.git`
2. `cd Project-Ganymede`
3. Open Claude Code in that directory
4. Open this `HANDOFF.md`, copy the code block above (everything between the triple-backticks), paste it as your first message in the new Claude Code chat
5. *Optional*: if you want full prior-state memory continuity, restore `.claude-archive/memory/*` to your Claude Code project memory directory before the new session writes its first memory file (see `.claude-archive/README.md` for the exact path encoding). Skipping this is fine — auto-memory will rebuild organically.
6. The new session ingests the project's docs in the right order and is ready to continue

You don't need anything else preserved locally. The repo is the source of truth.

## How this file came to exist

The operator paused this project for long-term storage and wanted to move the local working directory into a cloud-backed folder while preserving everything needed to resume from a fresh `git clone` if the local copy is ever lost or moved. Rather than keep the bootstrap prompt in personal notes or clipboard, it's committed to the repo so the act of cloning automatically yields the resume instructions.

The `/complete-handoff` skill produced this file. The companion `.claude-archive/` directory holds the local Claude Code session infrastructure that lived outside the repo at pause time — session transcripts and auto-memory files.
