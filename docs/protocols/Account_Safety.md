---
title: "Account Safety — NotebookLM Cooldown Discipline"
type: "protocol"
status: "active"
tags: ["protocols", "operational"]
color_id: "6"
---

# Account Safety — NotebookLM Cooldown Discipline

## Why this exists

NotebookLM has no official API. The `notebooklm-py` package this project depends on reverse-engineers the web app's session cookies to make calls. Google's anti-automation systems are not documented; the Z-SPAN bridge that pioneered this access pattern explicitly notes that *"the unofficial API has invisible safety triggers we don't want to find."*

A flagged or locked Google account would lose:
- The canonical 9D Chess Engine notebook
- The Mirror Auditor notebook
- All source documents loaded in either
- Future ability to run any experiment on this stack
- Probably cascade to other Google services tied to the same account

The mitigation is a **cooldown gate** at the lowest layer of the codebase that enforces minimum spacing between any two NotebookLM API calls, plus advisory soft caps on cumulative call volume.

## What the gate enforces

Implemented as `_CooldownGate` in `ganymede-backend/app/services/notebooklm/cooldown.py`, with a single module-global instance (`_GATE`) shared by all `NotebookLMService` instances in the process. Re-exported from the package root for legacy callers.

| Setting | Default | Env var | Behavior |
| --- | --- | --- | --- |
| Per-call cooldown | 8 seconds | `GANYMEDE_NOTEBOOKLM_COOLDOWN` | **Hard floor.** Every NotebookLM API call blocks until 8s have passed since the previous one. |
| Inter-session cooldown | 60 seconds | `GANYMEDE_NOTEBOOKLM_SESSION_COOLDOWN` | **Advisory.** Callers running distinct experimental runs (Powell run vs. Tokenized Land run, etc.) call `mark_session_boundary()` between them; the next API call then waits the full 60s. |
| Hourly soft cap | 20 calls | `GANYMEDE_NOTEBOOKLM_HOURLY_CAP` | Logs a warning. Does not block. Human operator decides whether to stop. |
| Daily soft cap | 100 calls | `GANYMEDE_NOTEBOOKLM_DAILY_CAP` | Logs a stronger warning. Does not block. |

The 8s and 60s defaults match the values Z-SPAN's bridge documents as operationally validated. The 20/hour and 100/day caps are conservative project-specific additions.

## What's covered by the gate

Every method in `NotebookLMService` that invokes `self.client.X` has `await _GATE.acquire()` before the call. Methods covered:

Core (in `notebooklm/client.py`):
- `create_notebook`
- `upload_document` / `upload_url` / `upload_file`
- `query_notebook` (and through it, `query_chess_engine`, `query_mirror_auditor`)
- `configure_persona` (and through it, `configure_pki_oracle`, `configure_chess_engine`, `configure_mirror_auditor`)

Studio (in `notebooklm/studio.py`):
- `generate_audio_overview`, `generate_video_overview`, `generate_infographic` — each Studio create call, each retry attempt, and each download poll iteration acquires the gate.

Research (in `notebooklm/research.py`):
- `start_research`, `poll_research`, `import_research_sources` — and the `run_deep_research` convenience method, which acquires once per upstream call.

`initialize` and `close` are not gated — they're once-per-process and don't generate Engine traffic. The `auth_check` module's `_probe` is also not gated; it loads cookies without making a billable API call.

## What's NOT covered

- **Direct calls to `self.client.X` from anywhere outside `NotebookLMService`.** Don't do this. Always go through the service methods.
- **External tools talking to NotebookLM independently** (e.g. user using the web UI, the `notebooklm` CLI, the browser subagent). Out of scope by definition.
- **Other Google services on the same account.** The gate only governs NotebookLM. Don't slam Gmail, Drive, etc. from the same automation that's also driving NotebookLM.

## Operator practices that complement the gate

- **One experiment per session.** Don't chain a Cleanroom run + a Mirror Validation run + a Genie run in the same automation pass. Run one, mark a session boundary, take a break, then the next.
- **Pre-flight cooldown stats before a multi-stroke run.** `NotebookLMService.cooldown_stats()` returns current call counts; if the hourly cap is already at 15+ and the upcoming run will need 5+ calls, defer.
- **Don't loop without explicit limits.** Any code that calls NotebookLM in a loop must have a hard cap on iterations, set conservatively. The cooldown gate makes infinite loops slow, not safe.
- **If something fails or hangs, stop.** Don't retry automatically against NotebookLM. Stop, investigate, then re-run manually.

## What to do if the account gets flagged

If you start seeing 429s, 403s, "session expired" errors that don't go away after re-login, or behavior changes in the notebooks (notebooks disappearing, custom prompts being reset):

1. **Stop all automation immediately.** Kill any running Ganymede backend process.
2. **Don't retry.** Whatever caused the flag will only get worse with more requests.
3. **Inspect the gate stats** (`NotebookLMService.cooldown_stats()`) to see what hourly/daily volume you've been at. Save those numbers — they're a data point for whether the configured caps are too loose.
4. **Refresh login manually** (`notebooklm.exe login` from `ganymede-backend/venv_312/Scripts/`) and check whether the notebooks are still there via the web UI before doing anything else from code.
5. **If notebooks are gone** — the project's notebook IDs in `notebooklm/client.py` (`CHESS_ENGINE_ID`, `MIRROR_AUDITOR_ID`) will need to be updated to whatever new notebooks the user creates. The persona text is preserved at `docs/protocols/Engine_Persona.md` and `docs/protocols/Mirror_Auditor_Persona.md` so the new notebooks can be re-configured to match.
6. **If notebooks are intact** — re-tighten the cooldown caps in `.env` (lower the hourly/daily limits, increase the per-call cooldown) and resume cautiously.

## Historical compliance note

This gate was added on 2026-05-06, after a session that did 3 NotebookLM API calls in <60 seconds with no cooldowns (the Mirror Validation Amnesia run — `configure_chess_engine` + `configure_mirror_auditor` + `query_mirror_auditor`). Nothing went wrong, but it was a violation of the Z-SPAN-recommended discipline and would have left the project exposed if Google's safety triggers had reacted. The gate was added before any further NotebookLM work was done, so all post-2026-05-06 calls go through it.

## How to test the gate without touching NotebookLM

```python
import asyncio, time
from app.services.notebooklm import NotebookLMService, _GATE

async def main():
    svc = NotebookLMService()
    print(svc.cooldown_stats())
    t0 = time.monotonic()
    await _GATE.acquire()
    await _GATE.acquire()  # should wait ~8s
    print(f"Two acquires took {time.monotonic() - t0:.1f}s")

asyncio.run(main())
```

This was the smoke test run when the gate landed; it correctly enforced 8.02s between two rapid acquires.
