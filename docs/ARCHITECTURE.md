# Architecture

Project Ganymede is one source tree with two build-time editions.

## Full local edition

```text
Browser
  -> Next.js interface
  -> FastAPI session API
      -> Claude CLI dispatcher (no tools)
      -> Claude CLI triage (no tools, foundation corpus)
      -> Claude CLI research harvest (WebSearch only)
      -> source-linked Truth Packets
      -> Claude CLI synthesis (no tools, corpus + packets)
      -> Mirror Auditor (no tools)
      -> Connection Bridge (no tools)
      -> revised synthesis + translation
  <- WebSocket session events and HTTP results
```

The foundation corpus is assembled from `docs/foundations/*.md`. Outside facts enter analytical strokes only through explicit Truth Packets. Research and analysis are separate CLI invocations with different tool permissions.

Session state is stored in SQLite under `ganymede-backend/data/` by default. Prompt-cache files generated from the stable system prompts live under the same ignored data directory. No runtime state is committed.

## Deterministic showcase

The showcase uses the same React components but sets `GANYMEDE_EDITION=showcase` at build time. Next.js emits a static export. The dispatcher uses fixed fictional data, the advanced local runner is not navigable, and no fetch or WebSocket request is made during the scripted run.

## Claude CLI process boundary

`ClaudeCliRunner` uses `subprocess.Popen` inside `asyncio.to_thread`. This is intentional: it keeps FastAPI responsive and works under Windows Uvicorn execution where asyncio subprocess transports can fail. Each process has a timeout, a bounded retry count, no session persistence, strict empty MCP configuration, and an explicit tool list.

The WebSearch harvester tells Claude to treat webpages as untrusted evidence. URLs are preserved in the returned Truth Packet and surfaced to the analytical engine as source material.
