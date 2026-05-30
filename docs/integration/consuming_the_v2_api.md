---
title: "Consuming the Ganymede v2 API"
type: "architecture-component"
status: "active"
tags: ["integration", "api"]
color_id: "2"
---

# Consuming the Ganymede v2 API

This is the doc to read first if you're building a consumer that wants to use Ganymede's strategic-analysis engine. It assumes no prior knowledge of the project's research framework — concepts are introduced inline. After reading, you should be able to write a working consumer in any language that can speak HTTP and JSON.

If you're new to the project itself (rather than just the API), [`OVERVIEW.md`](../OVERVIEW.md) explains the broader research goal first; this doc is strictly the integration surface.

## TL;DR

- Ganymede runs as an HTTP service (FastAPI). Default URL: `http://127.0.0.1:8000`.
- The API is **session-based**: you create a session, drive one or more "strokes" against it, and finalize.
- A *stroke* is one Engine invocation. Single-pass = one stroke; iterative = three strokes (synthesis → audit → re-synthesis).
- Inputs: a *Scenario* (what to reason about) + *Truth Packets* (your already-harvested research findings, source-cited).
- Outputs: structured *StrokeResults* with the canonical strategic shapes (Strategic Lasso, Incomprehensible Move, Final Resolution).
- Real-time progress is available over WebSocket; polling also works.
- Cooldown discipline is built in. You don't manage rate limits — the backend does.

```
Consumer                                Ganymede
   │                                       │
   │  POST /api/v2/sessions                │
   │     (scenario, pathway, iterative?)   │
   │ ────────────────────────────────────► │
   │                                       │
   │ ◄──────── { session_id, state } ───── │
   │                                       │
   │  POST /api/v2/sessions/{id}/iterate   │
   │     (truth_packets[])                 │
   │ ────────────────────────────────────► │
   │  WS  /api/v2/sessions/{id}/events     │
   │ ────────────────────────────────────► │
   │ ◄──── stroke_started, stroke_started, │
   │       synthesis_complete, ...         │
   │                                       │
   │ ◄──────── { strokes[], state } ────── │
   │                                       │
   │  POST /api/v2/sessions/{id}/complete  │
   │ ────────────────────────────────────► │
   │ ◄──── { final_resolution } ────────── │
```

## Concepts

### What Ganymede is, mechanically

Two things, glued together:

1. **A persona-locked NotebookLM** (the "9D Chess Engine") — a notebook configured with a fixed strategic-physics persona and a curated source corpus. Querying it returns reasoning expressed in the project's strategic vocabulary (Strategic Lasso, Incomprehensible Move, etc).
2. **A second persona-locked NotebookLM** (the "Mirror Auditor") — same source corpus, but configured for fault-finding rather than synthesis. It enumerates rigidity errors, pattern-matching, confidence-evidence gaps, and dimensional greeds in a piece of analysis.

Ganymede's API is a session-based HTTP wrapper around these two notebooks. It manages cooldowns, threading, multi-stroke orchestration, and event emission so consumers don't have to.

You don't talk to NotebookLM directly. You hand Ganymede a Scenario + Truth Packets and Ganymede drives the notebook calls.

### Pathways

Every session picks one *pathway* at creation time. The pathway determines which prompt template wraps your scenario before it hits the Engine.

| Pathway | Use when | Scenario fields | Engine output shape |
| --- | --- | --- | --- |
| `cleanroom` | You have a falsifiable question with a known resolution date ("will X happen by Y") | `question` | Probability + reasoning, with Strategic Lasso and Incomprehensible Move |
| `genie` | You have a current state and a wished-for state, and you want a path between them | `current_state`, `wished_for_state` | Inadvertent Path: a strategic move sequence with Lasso + Incomprehensible Move |
| `offensive` | Architect-stance variant of Genie. You're designing a strategic funnel against a target | `target`, `objective_state` | Same shape as Genie, with the framing flipped |
| `mirror_audit` | You have a piece of analysis (typically Stroke 1 from another session) and want it stress-tested for faults | `prior_resolution` | Audit findings: rigidity / pattern-matching / confidence-evidence-gaps / dimensional-greeds |

Most consumers want `cleanroom` or `genie`. `mirror_audit` is normally driven internally by the Iterative Engine (Stroke 2) rather than called directly.

The four pathways share the same code path under the hood — only the prompt framing differs. There's no engine-level distinction; pathway choice is a prompt selector.

### Truth Packets

A *Truth Packet* is a research finding the consumer wants the Engine to reason over. It has three fields:

```json
{
  "subject": "Eyewitness Misidentification (severity 4)",
  "content": "Witness identification varies between police statement and trial testimony. Trial transcript p.42 line 11 vs. police report 2024-03-12 §3. Brady v. Maryland may apply.",
  "source_label": "PrisonBreak case 7c91a3, error #14"
}
```

- **`subject`** — short label. Rendered as a header in the synthesis prompt.
- **`content`** — the body of the finding. The orchestrator never modifies this text (Zero-Degradation rule). Hash-citing facts in your content is encouraged but not enforced — the Engine's reasoning quality scales with the source-grounding of your packets.
- **`source_label`** — human-readable provenance. Not sent to the Engine; for your own audit trail.

Truth Packets are the consumer's job. Ganymede does **not** harvest them for you in v1 — see ["What's not in v1"](#whats-not-in-v1) below for why and what's planned. If your project has a closed-RAG layer (NotebookLM, vector search, document-grounded chat, anything that produces source-cited findings), use it to produce the packets and ship them to Ganymede.

### Sessions and strokes

A *session* is one in-progress experimental run. It holds:

- The scenario you're reasoning about
- The chosen pathway
- A sequential list of *strokes* (one per Engine invocation)
- An event timeline (creation, stroke starts/completes, terminal events)
- Subscriber queues for live event streaming
- A final resolution once completed

A *stroke* is one Engine call. Most consumer flows are either:

- **Single-pass** — one synthesis stroke. Fast (minutes, mostly cooldown). Cheaper. Good for "first look."
- **Iterative** — three strokes:
  - Stroke 1: synthesis on your truth packets
  - Stroke 2: Mirror Auditor critique of Stroke 1
  - Stroke 3: re-synthesis with the audit findings injected as friction
  - Slower (3× the cooldowns + 3× the Engine response time), but produces decision-grade output. The Stroke 1 result is plausible-sounding but operationally fragile; Stroke 3 is what survived a stress test.

Once a session is created with `iterative: true, max_strokes: 3`, you drive the loop with one call to `/iterate` and Ganymede orchestrates all three strokes. You don't have to call audit and re-synthesize separately (though you can — the API exposes those primitives too).

### Final Resolution

When you `POST /complete` on a session, Ganymede returns a `FinalResolution`:

```json
{
  "session_id": "...",
  "pathway": "genie",
  "iterative": true,
  "strokes": [ /* StrokeResult[] — ordered Stroke 1, 2, 3 */ ],
  "final_text": "<the canonical answer text>",
  "started_at": "2026-05-06T18:00:00Z",
  "completed_at": "2026-05-06T18:14:32Z",
  "total_engine_calls": 3
}
```

`final_text` is a convenience: for iterative runs it's the Stroke 3 final resolution; for single-pass runs it's the only stroke's resolution. `strokes` carries the full per-stroke history including audit findings if Stroke 2 ran.

`/complete` is idempotent. You can call it multiple times and get the same FinalResolution.

## Lifecycle of a typical run

```
1. CREATE     POST /api/v2/sessions
              Body: { scenario, pathway, iterative, max_strokes }
              → 201 { session_id, state }

2. SUBSCRIBE  WS /api/v2/sessions/{id}/events/stream
              (optional — for live progress; you can also poll /events)
              ← session_created event replayed immediately, then live events

3. DRIVE      POST /api/v2/sessions/{id}/synthesize     (single-pass)
              OR
              POST /api/v2/sessions/{id}/iterate         (iterative)
              Body: { truth_packets, [framing] }
              → 200 { stroke } | { strokes }
              (blocks for the duration of the engine call(s);
               WS subscribers see stroke events as they fire)

4. FINALIZE   POST /api/v2/sessions/{id}/complete
              → 200 { final_resolution, state }

5. (optional) GET /api/v2/sessions/{id}/events
              → all events ever emitted on the session, chronological
```

The HTTP calls are blocking — `/iterate` returns when all three strokes are done. For UI-style consumers that want stroke-by-stroke progress as it happens, run `/iterate` in a background task while a separate task forwards events from the WebSocket to your frontend.

## API reference

All endpoints are under `/api/v2/`. Default base URL: `http://127.0.0.1:8000`.

### `GET /api/v2/health`

Liveness check + cooldown stats + active session count. Hit this before kicking off a multi-stroke run to confirm the gate isn't already saturated.

```json
{
  "status": "healthy",
  "cooldown": {
    "calls_last_hour": 4,
    "calls_last_24h": 17,
    "hourly_cap": 20,
    "daily_cap": 100,
    "api_cooldown_sec": 8.0,
    "session_cooldown_sec": 60.0
  },
  "active_sessions": 1
}
```

### `POST /api/v2/sessions`

Create a session. Returns 201 on success.

Request:
```json
{
  "scenario": {
    "current_state": "...",
    "wished_for_state": "...",
    "dream_state": true,
    "extra_context": null
  },
  "pathway": "genie",
  "iterative": true,
  "max_strokes": 3
}
```

Response:
```json
{
  "session_id": "8194413e-...",
  "state": {
    "session_id": "8194413e-...",
    "status": "running",
    "pathway": "genie",
    "iterative": true,
    "max_strokes": 3,
    "strokes_so_far": 0,
    "error_message": null,
    "has_final_resolution": false
  }
}
```

Errors:
- `422` — scenario doesn't satisfy the chosen pathway's contract (e.g. genie pathway with no `current_state`/`wished_for_state`).
- `422` — `iterative=true` with `max_strokes < 2`.

### `GET /api/v2/sessions/{id}`

Get the session's current state. Returns 404 if not found.

### `POST /api/v2/sessions/{id}/synthesize`

Run one synthesis stroke. The session's strokes list grows by 1.

Request:
```json
{
  "truth_packets": [ /* TruthPacket[] — at least 1 required */ ],
  "framing": null
}
```

`framing` is an optional string that fully replaces the synthesis prompt template for this call. Most consumers leave it null and use the pathway's default. Only override if you've reviewed `app/services/orchestrator.py:SYNTHESIS_TEMPLATE` and have a specific reason.

Response:
```json
{
  "stroke": { /* StrokeResult */ },
  "state": { /* updated SessionStateResponse */ }
}
```

Errors:
- `404` — session not found
- `409` — session is not in `running` state (already completed or errored)
- `422` — pathway/contract mismatch, e.g. trying to synthesize on a `mirror_audit` pathway session
- `500` — orchestrator failure (session is also transitioned to `error` state internally)

### `POST /api/v2/sessions/{id}/iterate`

Drive the full Iterative Engine multi-stroke loop in one HTTP call. Convenience over making N separate `/synthesize` and `/audit` calls. The session must have been created with `iterative: true`.

Request:
```json
{
  "truth_packets": [ /* TruthPacket[] */ ],
  "max_strokes": null,
  "include_bridge": true,
  "bridge_notebook_id": null
}
```

`max_strokes` defaults to the session's own max_strokes. With Bridge enabled the loop has 4 stroke slots (S1, Auditor, Bridge, re-synth); without Bridge it has the historic 3 (S1, Auditor, re-synth). Pass a smaller value to stop earlier.

`include_bridge` (default `true`) controls whether the Connection Bridge runs as Stroke 2b — Bicameral Convergence Level 1 — alongside the Mirror Auditor. The Bridge enumerates *missed connections* between Truth Packets that the Engine's synthesis didn't draw; this is an orthogonal lens to the Auditor's fault-mode catches. When enabled, Stroke 3's re-synthesis prompt includes BOTH audit blocks (Auditor 900 chars + Bridge 600 chars within the existing 1500-char audit budget).

`bridge_notebook_id` (optional) lets the caller supply a pre-provisioned Bridge notebook to skip the ~3-min provisioning step. When `include_bridge=true` and `bridge_notebook_id=null`, the orchestrator auto-provisions a fresh Bridge notebook inline via `provision_bridge_notebook` (14 cooldown-gated calls: 1 create + 13 foundations + N truth packets + 1 persona apply). For one-shot runs this is fine; for repeated runs on the same substrate, pass a notebook ID to amortise.

**Bridge failures fall back to historic 3-stroke gracefully** — if provisioning or the Bridge audit query errors, the run continues with Auditor-only friction for Stroke 3. The session is NOT marked failed.

Response:
```json
{
  "strokes": [ /* StrokeResult[] — ordered, length = max_strokes; with Bridge enabled, Stroke 2 has audit_kind="mirror_auditor" and Stroke 3 has audit_kind="bridge" */ ],
  "state": { /* updated SessionStateResponse */ }
}
```

Each `StrokeResult` now carries an `audit_kind` field (`"mirror_auditor"` | `"bridge"` | `null`) so consumers can render Auditor and Bridge strokes distinctly without inspecting event payloads.

The HTTP call blocks for the full loop duration. With Bridge auto-provisioning, expect ~5-7 minutes total wall time (vs ~2 min historic 3-stroke). Stroke events fire on the session as each stroke completes — WS subscribers see them in real time.

Errors:
- `404` — session not found
- `409` — session not running
- `422` — non-iterative session, or `max_strokes` out of range

### `POST /api/v2/sessions/{id}/bridge-audit`

Run one Connection Bridge audit stroke against a Stroke 1 (or arbitrary target) text — Bicameral Convergence Level 1. The Bridge enumerates *missed connections* between Truth Packets that the Engine's synthesis didn't draw, an orthogonal lens to the Mirror Auditor's fault-mode catches.

Unlike `/iterate` (which fires the Mirror Auditor inline on a canonical notebook), the Bridge has no canonical notebook ID — its persona is applied per-call to a caller-supplied non-canonical notebook. The caller is responsible for creating + provisioning that notebook before this endpoint can be invoked.

Request:
```json
{
  "bridge_notebook_id": "<notebook-uuid>",
  "target_text": null,
  "scenario_context": null
}
```

- `bridge_notebook_id` (required): a non-canonical notebook with the foundations corpus + the scenario's Truth Packets pre-loaded. Passing a canonical ID (Engine / Mirror Auditor / Legacy) returns 422.
- `target_text` (optional): the analysis text to audit. Defaults to the most recent stroke's `raw_response`.
- `scenario_context` (optional): override for the scenario framing. Defaults to derived from the session's scenario.

Response:
```json
{
  "stroke": { /* StrokeResult — pathway=mirror_audit, audit_findings=null */ },
  "state": { /* updated SessionStateResponse */ }
}
```

The returned stroke is recorded as `pathway: "mirror_audit"` (structurally an audit stroke, same shape as a Mirror Auditor stroke). Distinguishable from Mirror Auditor strokes by inspection of `raw_response` — Bridge enumerates connections, Auditor enumerates fault categories. `audit_findings` is intentionally `null` (the four-category parser doesn't apply to Bridge output).

**Typical caller flow (with the provision helper — recommended):**

```
1. POST /api/v2/sessions                                  # create session
2. POST /api/v2/sessions/{id}/synthesize                  # Stroke 1
3. POST /api/v2/bridge/provision                          # ← helper (returns task_id)
4. GET  /api/v2/tasks/{task_id}  (poll until completed)   # task.result.notebook_id is the Bridge ID
5. POST /api/v2/sessions/{id}/bridge-audit                # ← this endpoint, pass that notebook_id
6. DELETE /api/v2/notebooks/{bridge_nb}                   # cleanup (optional, but recommended if single-use)
```

Step 3 (`/bridge/provision`) bundles foundations upload + Truth Packet upload + Bridge persona apply into one background task — ~3-5 min wall time for ~14 NotebookLM calls.

**Manual flow (if you want full control over what gets uploaded):**

```
1. POST /api/v2/sessions                                  # create session
2. POST /api/v2/sessions/{id}/synthesize                  # Stroke 1
3. POST /api/v2/notebooks                                 # create Bridge notebook
4. POST /api/v2/notebooks/{nb}/sources/file  (×N)         # foundations corpus
5. POST /api/v2/notebooks/{nb}/sources/file  (×M)         # scenario Truth Packets
6. POST /api/v2/notebooks/{nb}/configure-persona          # apply Bridge persona
7. POST /api/v2/sessions/{id}/bridge-audit                # ← this endpoint
8. DELETE /api/v2/notebooks/{nb}                          # cleanup (optional)
```

Steps 3-6 in the manual flow are ~15+ NotebookLM calls; this endpoint itself is 1 call. For ad-hoc single audits, prefer the helper. For long-lived scenarios where the same Bridge notebook is reused across many audits, either flow works since the setup amortises.

Errors:
- `404` — session not found
- `409` — session not running
- `422` — `bridge_notebook_id` is a canonical ID, or no prior stroke and no `target_text` supplied
- `500` — orchestrator failure (session transitions to error state)

### `POST /api/v2/bridge/provision`

Provision a Bridge notebook in one background-task call. Bundles four steps that otherwise require ~15 separate HTTP requests:

1. Create a new (non-canonical) NotebookLM notebook.
2. Upload the foundations corpus (`docs/foundations/` — every `.md` / `.pdf` / `.txt` file except `README.md`; 13 files in the current corpus).
3. Upload the supplied Truth Packets (each written to a temp `.md` file with the packet's subject as title + source_label as attribution).
4. Apply the Connection Bridge persona via `configure_connection_bridge`.

Returns 202 + `task_id` immediately. The actual work runs as a background task — caller polls `GET /api/v2/tasks/{task_id}` until completion.

Request:
```json
{
  "title": null,
  "truth_packets": [
    { "subject": "Scenario", "content": "Will Anthropic still be ranked #1...", "source_label": "Operator-supplied" }
  ],
  "include_foundations": true
}
```

- `title` (optional): notebook title. Defaults to `"Bridge — <first truth_packet subject>"`. Truncated to 200 chars.
- `truth_packets` (required): list of Truth Packets to upload. Should match the substrate the Engine reasoned over for the scenario being audited.
- `include_foundations` (optional, default true): whether to also upload `docs/foundations/` corpus. Set false only for testing or if foundations are pre-loaded elsewhere.

Response (202):
```json
{
  "task_id": "...",
  "kind": "bridge_provision",
  "notebook_id": null,
  "status": "running",
  "poll_url": "/api/v2/tasks/..."
}
```

`notebook_id` is `null` at submit time (the notebook hasn't been created yet). Once `task.status == "completed"`, `task.result.notebook_id` is the Bridge notebook ID — pass that to `/api/v2/sessions/{id}/bridge-audit`.

On completion, `task.result`:
```json
{
  "notebook_id": "<uuid>",
  "title": "Bridge — Scenario",
  "foundations_uploaded": 13,
  "truth_packets_uploaded": 1,
  "sources_total": 14,
  "bridge_persona_applied": true
}
```

Operational cost: ~14 NotebookLM calls (one create + one per foundation file + one per Truth Packet + one persona apply). With the 8s cooldown floor, typically 3-5 minutes wall time.

Notes:
- The foundations directory defaults to `docs/foundations/` relative to the project root. Override via the `GANYMEDE_FOUNDATIONS_DIR` env var if your deployment lays out files differently.
- On task error (any upload or create failure), the partial notebook is **not** auto-deleted — caller can clean up via `DELETE /api/v2/notebooks/{id}` or keep it for debugging.

### `POST /api/v2/sessions/{id}/complete`

Finalize the session. Returns the FinalResolution. Idempotent.

Errors:
- `404` — session not found
- `409` — session has no strokes, or session is in error state

### `GET /api/v2/sessions/{id}/events`

All events emitted on the session so far, chronological. For polling-style consumers; prefer the WS variant for real-time push.

```json
{
  "session_id": "...",
  "events": [
    {
      "type": "session_created",
      "stroke_number": null,
      "payload": { "session_id": "...", "pathway": "genie", "iterative": true, "max_strokes": 3 },
      "emitted_at": "2026-05-06T18:00:00Z"
    },
    {
      "type": "stroke_started",
      "stroke_number": 1,
      "payload": { "pathway": "genie" },
      "emitted_at": "2026-05-06T18:00:01Z"
    },
    /* ... */
  ]
}
```

### `WS /api/v2/sessions/{id}/events/stream`

Real-time event stream. On connect, all past events are replayed immediately (so a late subscriber sees the full timeline up to "now"); subsequent events stream live.

Each message is a JSON-serialized `SessionEvent`. The server closes the connection cleanly after sending a terminal event (`session_complete` or `error`).

Close codes:
- `1000` — normal (terminal event reached or consumer disconnected)
- `1008` — policy violation (session not found)

The full set of event types:

| Type | When it fires | Payload |
| --- | --- | --- |
| `session_created` | At session construction | session_id, pathway, iterative, max_strokes |
| `stroke_started` | Before each stroke begins | pathway |
| `synthesis_complete` | After each synthesis call returns | the StrokeResult |
| `stroke_completed` | After each stroke is recorded | stroke_number, type |
| `session_complete` | Terminal — session.complete() called | final_text_len |
| `error` | Terminal — session.fail() called | message, exc_type |
| `oracle_request` | Reserved for future Oracle-creation flow (not emitted in v1) | subject, surgical_prompt |
| `oracle_created`, `oracle_harvested`, `blueprint_ready` | Reserved for future Oracle flow | — |

## Code examples

### curl

```bash
# Create a session
SESSION=$(curl -s -X POST http://127.0.0.1:8000/api/v2/sessions \
  -H "Content-Type: application/json" \
  -d '{
    "scenario": {
      "current_state": "We are at point A.",
      "wished_for_state": "Reach point B without alerting the gatekeeper."
    },
    "pathway": "genie",
    "iterative": false,
    "max_strokes": 1
  }' | jq -r .session_id)
echo "Session: $SESSION"

# Synthesize one stroke
curl -s -X POST "http://127.0.0.1:8000/api/v2/sessions/$SESSION/synthesize" \
  -H "Content-Type: application/json" \
  -d '{
    "truth_packets": [
      {
        "subject": "Gatekeeper schedule",
        "content": "Gatekeeper rotates posts every 4 hours; current rotation began at 14:00.",
        "source_label": "Field observation"
      }
    ]
  }' | jq

# Finalize
curl -s -X POST "http://127.0.0.1:8000/api/v2/sessions/$SESSION/complete" | jq
```

### Python (synchronous, with `httpx` or `requests`)

```python
import httpx

BASE = "http://127.0.0.1:8000"

def run_single_pass(scenario: dict, packets: list[dict]) -> dict:
    with httpx.Client(base_url=BASE, timeout=600.0) as client:
        # Create
        r = client.post("/api/v2/sessions", json={
            "scenario": scenario,
            "pathway": "genie",
            "iterative": False,
            "max_strokes": 1,
        })
        r.raise_for_status()
        sid = r.json()["session_id"]

        # Synthesize
        r = client.post(f"/api/v2/sessions/{sid}/synthesize",
                        json={"truth_packets": packets})
        r.raise_for_status()
        stroke = r.json()["stroke"]

        # Complete
        r = client.post(f"/api/v2/sessions/{sid}/complete")
        r.raise_for_status()
        return r.json()["final_resolution"]


resolution = run_single_pass(
    scenario={
        "current_state": "We are at point A.",
        "wished_for_state": "Reach point B without alerting the gatekeeper.",
    },
    packets=[
        {"subject": "Gatekeeper schedule",
         "content": "Gatekeeper rotates posts every 4 hours; current rotation began at 14:00.",
         "source_label": "Field observation"},
    ],
)
print(resolution["final_text"])
```

### Python (async, with WebSocket event streaming)

```python
import asyncio
import json
import httpx
import websockets

BASE = "http://127.0.0.1:8000"
WS_BASE = "ws://127.0.0.1:8000"

async def run_iterative_with_progress(scenario, packets, on_event):
    async with httpx.AsyncClient(base_url=BASE, timeout=900.0) as client:
        # Create iterative session
        r = await client.post("/api/v2/sessions", json={
            "scenario": scenario,
            "pathway": "genie",
            "iterative": True,
            "max_strokes": 3,
        })
        r.raise_for_status()
        sid = r.json()["session_id"]

        # Subscribe via WS while /iterate runs in parallel
        async def stream_events():
            async with websockets.connect(f"{WS_BASE}/api/v2/sessions/{sid}/events/stream") as ws:
                async for msg in ws:
                    event = json.loads(msg)
                    on_event(event)
                    if event["type"] in ("session_complete", "error"):
                        break

        async def drive_iterate():
            r = await client.post(
                f"/api/v2/sessions/{sid}/iterate",
                json={"truth_packets": packets},
            )
            r.raise_for_status()
            return r.json()["strokes"]

        _, strokes = await asyncio.gather(stream_events(), drive_iterate())

        # Finalize
        r = await client.post(f"/api/v2/sessions/{sid}/complete")
        r.raise_for_status()
        return r.json()["final_resolution"]


def print_event(event):
    print(f"  [{event['type']}] stroke={event.get('stroke_number')}")


resolution = asyncio.run(run_iterative_with_progress(
    scenario={
        "current_state": "...",
        "wished_for_state": "...",
    },
    packets=[ /* ... */ ],
    on_event=print_event,
))
```

### TypeScript (Node, fetch + ws)

```typescript
const BASE = "http://127.0.0.1:8000";

async function runSinglePass(scenario: object, packets: object[]) {
  // Create
  const create = await fetch(`${BASE}/api/v2/sessions`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      scenario,
      pathway: "genie",
      iterative: false,
      max_strokes: 1,
    }),
  }).then(r => r.json());
  const sid = create.session_id;

  // Synthesize
  await fetch(`${BASE}/api/v2/sessions/${sid}/synthesize`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ truth_packets: packets }),
  }).then(r => r.json());

  // Complete
  return fetch(`${BASE}/api/v2/sessions/${sid}/complete`, {
    method: "POST",
  }).then(r => r.json());
}
```

For event streaming in TypeScript, see `examples/prisonbreak_consumer.md` — PrisonBreak's runner uses 2-second polling against `/events` instead of WS, which is simpler and avoids a websocket library dependency.

## Operational guarantees

### Cooldown discipline

Ganymede enforces a hard 8-second floor between any two NotebookLM API calls (configurable via `GANYMEDE_NOTEBOOKLM_COOLDOWN`). This is non-negotiable — the unofficial NotebookLM API has invisible rate-limit triggers and the gate is what keeps the project's account un-flagged. See [`../protocols/Account_Safety.md`](../protocols/Account_Safety.md) for the full rationale.

For consumers, this means:
- **You don't manage rate limits.** The backend enforces them transparently.
- **A 3-stroke iterative run takes at minimum ~24s of cooldown** (3 calls × 8s) on top of the actual NotebookLM response times. Don't expect sub-second responses.
- **Hitting `/iterate` in a tight loop will block, not 429.** Each call waits its turn against the gate.
- **Inter-session cooldowns** (60s by default) are advisory; consumers can call `/health` to see current cooldown stats and decide whether to defer a new run.

### Session persistence (or lack of)

Sessions are **in-memory** in v1. If the Ganymede backend restarts mid-session, all session state is lost. Consumers that need persistence should:

- Persist their own `(consumer_session_id, ganymede_session_id)` mapping in their own DB
- On Ganymede restart, treat any in-flight session as failed and start a fresh one
- Frozen `FinalResolution` payloads should be persisted on the consumer side as soon as `/complete` returns

This is deliberate. Persistence within Ganymede would create cross-consumer state that complicates multi-tenancy. Per [`module_design.md`](module_design.md), each consumer carries its own Ganymede instance OR shares the process and accepts in-memory ephemerality.

### Concurrency

A single Ganymede instance is single-tenant. The cooldown gate is process-global; multiple sessions running concurrently against the same backend will serialize at the NotebookLM call layer regardless. If a consumer needs more parallelism, run multiple Ganymede instances on separate ports (each with its own NotebookLM session — non-trivial; not the v1 supported shape).

## Notebook lifecycle, Studio, Deep Research (added 2026-05)

The session-based endpoints above cover *strategic synthesis* over pre-harvested Truth Packets — the primary consumer flow. A second endpoint surface, added in milestone 31, covers *notebook-side* operations: creating notebooks, configuring personas, generating Studio outputs (audio / video / infographic), and kicking off Deep Research. These are the primitives consumers like the Realist 10-notebook substrate build and the Persona Expansion experiment use directly.

Long-running operations (Studio generation, Deep Research) return a `task_id` immediately (HTTP 202) and the consumer polls `/api/v2/tasks/{task_id}` until `status == 'completed'` or `'error'`. Studio generations typically take 5-30 minutes; Deep Research is similar. Same cooldown gate as the session endpoints — no separate rate-limit budget.

### Notebook lifecycle

```
POST /api/v2/notebooks
  body: { title }
  → 201 { notebook_id, title }

POST /api/v2/notebooks/{id}/configure-persona
  body: { custom_prompt, response_length="LONGER" }
  → 200 { notebook_id, response_length, persona_char_count }
  → 403 if id is CHESS_ENGINE_ID / MIRROR_AUDITOR_ID / LEGACY_ENGINE_ID
        (read-only canonical notebooks — use the named configure_chess_engine /
         configure_mirror_auditor primitives if you need to refresh those)

POST /api/v2/notebooks/{id}/sources/url
  body: { url }
  → 200 { notebook_id, url, status="uploaded" }
```

### Studio outputs (background task)

```
POST /api/v2/notebooks/{id}/studio/audio
  body: { instructions, audio_format="DEEP_DIVE", audio_length="LONG",
          language="en", download=true }
  → 202 { task_id, kind="audio", notebook_id, status="running", poll_url }

POST /api/v2/notebooks/{id}/studio/video
  body: { instructions, video_format="EXPLAINER", video_style="CLASSIC",
          language="en", download=true }
  → 202 { task_id, kind="video", ... }

POST /api/v2/notebooks/{id}/studio/infographic
  body: { instructions, orientation="PORTRAIT", detail_level="DETAILED",
          style="PROFESSIONAL", language="en", download=true }
  → 202 { task_id, kind="infographic", ... }
```

The `download` flag (default true) controls whether the task waits for the upstream artifact to finish generating and downloads it to `<GANYMEDE_MEDIA_DIR>/<run_id>/<kind>.<ext>` (default `media/`). With `download=false`, the task completes as soon as the create call returns a NotebookLM task ID; the caller polls NotebookLM separately. Most consumers want `download=true`.

On completion, `result` carries `{ task_id, status, is_complete, downloaded_path }`. `status` is one of `"ok"`, `"timeout"`, `"silent_rejection"` — silent rejection means NotebookLM accepted the create call but never started generation (their server quietly refused); the wrapper retries up to 3× automatically before surfacing this.

### Deep Research (background task)

```
POST /api/v2/notebooks/{id}/research
  body: { query, source="web", mode="deep", auto_import=false,
          max_sources=null, poll_interval=null, timeout=null }
  → 202 { task_id, kind="research", ... }
```

On completion, `result` carries `{ task_id, status, query, sources, summary, report, imported }`. `imported` is the list of sources imported back into the notebook (empty unless `auto_import=true`).

### Task lifecycle

```
GET /api/v2/tasks/{task_id}
  → 200 { task_id, kind, notebook_id, status, result, error_message,
          exc_type, created_at, completed_at }

DELETE /api/v2/tasks/{task_id}
  → 200 { task_id, cancelled: bool }
  → 404 if task not found
  (cancelled=false if the task already completed; result/error preserved)

GET /api/v2/tasks
  → 200 { tasks: [...] }   (debug; not paginated)
```

Cancellation issues `asyncio.Task.cancel()`. For Studio / Research that's already in flight upstream, cancellation stops our local polling — the upstream generation continues on NotebookLM's side until it completes (and the resulting artifact sits in the notebook unused).

## Auth pill endpoints (added 2026-05)

The Z-SPAN-style auth health flow. Stateless wrappers over `app.services.notebooklm.auth_check`. The `AuthPill` component in `ganymede-ui/src/components/AuthPill.tsx` is the reference consumer.

```
GET /api/v2/auth/status              (optional ?force=true)
  → 200 { status: "valid"|"expired"|"missing"|"unknown",
          details, checked_at, cached, cache_age_seconds }

POST /api/v2/auth/relogin
  → 200 { spawned, cmd, pid, note, error? }
  (spawns `python -m notebooklm login` which opens a browser for Google OAuth)

POST /api/v2/auth/relogin/confirm
  body: { timeout_seconds=30 }
  → 200 { confirmed, exit_code, output, note?, error? }
  (feeds ENTER to the subprocess so it saves cookies and exits — call AFTER
   the user has completed sign-in in the browser)

GET /api/v2/auth/relogin/status
  → 200 { in_flight, exited, pid?, exit_code? }
```

Cache TTL is 300s by default (tunable via `GANYMEDE_NOTEBOOKLM_AUTH_CHECK_TTL`). The `relogin` and `confirm` calls automatically invalidate the cache so the next status probe re-runs.

## What's not in v1

These are deliberate non-goals for the current API surface, not bugs:

- **Oracle creation through the API.** The PKI Oracle harvest path (where Ganymede spins up new persona-locked notebooks to research subjects on demand) exists in the orchestrator but is not exposed in v2. Consumers ship pre-harvested Truth Packets instead. This is the right answer for any consumer that already has its own grounded RAG layer (PrisonBreak, Polymarket-Validator, etc). When/if the Oracle approval gate gets a v2 surface, the event-stream types `oracle_request`, `oracle_created`, `oracle_harvested` are reserved for it.
- **Persistence.** As noted above. Background tasks are also in-memory; a backend restart loses any in-flight task. Consumers persist their own task ID mappings if they need durability across restarts.
- **Authentication.** None. The backend listens on `127.0.0.1:8000` and trusts every caller. Don't bind to `0.0.0.0` without putting auth in front of it.
- **Multi-tenancy.** Out of scope. One Ganymede instance, one NotebookLM session, one Engine notebook.
- **Mirror Validation as a standalone pathway runnable through the API.** It's currently driven internally by `/iterate` (Stroke 2). If a consumer wants to audit a specific external piece of analysis (no preceding Stroke 1 from the same session), use the `mirror_audit` pathway with `prior_resolution` in the Scenario.
- **Remote download of Studio artifacts.** When a Studio task completes, `result.downloaded_path` is the *server-side* file path. Same-host consumers can open it directly; a remote consumer would need a `GET /api/v2/tasks/{id}/download` endpoint that streams the file. Not in v1 — add when a remote consumer asks.

## Where to look in the source

If the doc above leaves a question unanswered, the source is the canonical reference:

| Question | File |
| --- | --- |
| Exact request/response shapes | `ganymede-backend/app/v2_routes.py` |
| The Pydantic v2 contracts | `ganymede-backend/app/contracts.py` |
| What each pathway's prompt looks like | `ganymede-backend/app/services/orchestrator.py` (templates near the top) |
| Cooldown gate implementation | `ganymede-backend/app/services/notebooklm_service.py` (`_CooldownGate`) |
| Engine + Auditor personas | `docs/protocols/Engine_Persona.md`, `docs/protocols/Mirror_Auditor_Persona.md` |
| The high-level architecture story | `docs/OVERVIEW.md` |

## Examples

Consumers built against this API:

- [`examples/prisonbreak_consumer.md`](examples/prisonbreak_consumer.md) — PrisonBreak's case-grounded strategic-simulation integration (Genie pathway, errors-as-truth-packets, socket.io progress streaming). The first concrete consumer; useful as a reference for "how does this look in a real codebase."

When more consumers exist, they'll be filed in `examples/`.

## Mocked-mode for development

If you're iterating on a consumer's UI or wiring and don't want to burn live NotebookLM quota, use `ganymede-backend/start_mocked.py` instead of plain `uvicorn`. It boots the same v2 API but monkey-patches `query_chess_engine` and `query_mirror_auditor` to return canned responses with simulated latency. Useful for end-to-end consumer testing without needing a working NotebookLM session.

```powershell
cd ganymede-backend
.\venv_312\Scripts\activate
python start_mocked.py
```

The mock returns plausible-shaped Stroke-1 / Stroke-2 / Stroke-3 outputs so iterative runs and event ordering work realistically.
