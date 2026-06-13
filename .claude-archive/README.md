# .claude-archive

Archival snapshot of the local Claude Code auto-memory corpus at the time of `/complete-handoff` (2026-06-13). Lives in the repo so a future `git clone` can restore the project's memory state if desired.

This directory is archival-only. Future Claude Code sessions can ignore it — auto-memory will rebuild organically from the canonical project docs and the operator's interactions.

## What's here

- `memory/` — the 13 auto-memory `.md` files plus the `MEMORY.md` index, copied verbatim from the operator's local Claude Code project directory at handoff time.

## What's intentionally NOT here

**Session transcripts (`*.jsonl`).** Three of the prior session transcripts contained API keys in plaintext (a `GOOGLE_API_KEY` value and a `sk-...` DeepSeek-style value). Rather than scrub them and risk missing patterns, the operator chose to skip transcript archiving entirely for this handoff. The `HANDOFF.md` bootstrap plus the in-repo docs (`CLAUDE.md`, `ROADMAP.md`, `TASKS.md`, `docs/history/Architecture_History.md`, run records) cover the load-bearing context without the transcripts.

Operator follow-up flagged at handoff: rotate the `GOOGLE_API_KEY` — it's been deferred for weeks and sat in plaintext across multiple surfaces. That's an operator action in Google AI Studio.

## How to restore memory into a fresh Claude Code session

If you clone fresh and want full memory continuity (so the new session inherits the auto-memory corpus instead of rebuilding from scratch):

**Windows:**

```powershell
# Replace <user> with your Windows username; the encoded path mirrors the project root
$target = "C:\Users\<user>\.claude\projects\C--Users-<user>-Desktop-GANYMEDE-FINAL-PROJECT-GANYMEDE\memory"
New-Item -ItemType Directory -Force $target
Copy-Item .claude-archive\memory\*.md $target
```

**macOS / Linux:**

```bash
# Adapt the encoded path to your clone location
target="$HOME/.claude/projects/-Users-<user>-Desktop-GANYMEDE-FINAL-PROJECT-GANYMEDE/memory"
mkdir -p "$target"
cp .claude-archive/memory/*.md "$target/"
```

The encoded path is the absolute project path with `\` / `/` and `:` replaced by `-`. Claude Code auto-creates the directory on first memory write if you skip the restore — the new session will start fresh and accumulate memory organically from the canonical docs.

Skipping the restore is fine. Memory is a convenience layer; the canonical docs are the source of truth.

## How this directory came to exist

The operator paused Project Ganymede for long-term cloud-backed storage and ran `/complete-handoff` to commit all resume-from-clone infrastructure to the repo. The skill produced `HANDOFF.md` at the repo root (bootstrap for fresh sessions) and this `.claude-archive/` directory (Claude Code project artifacts that lived outside the repo at pause time).
