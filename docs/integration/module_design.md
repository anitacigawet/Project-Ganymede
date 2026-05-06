# Ganymede Module — Integration Design

**Status:** Design proposal. Nothing built against this yet. Awaiting user review.

## What a consumer needs from Ganymede

Any project that wants to use Ganymede as a strategic-analysis module needs to be able to:

1. **Send a scenario.** Either a wish-shape (current_state, wished_for_state) or a question-shape ("will X happen", "what's the best move on Y") plus optional pre-existing context (documents, prior analysis findings, Truth Packets the consumer has already harvested itself).
2. **Receive a session handle.** A reference the consumer can use to track the run, subscribe to updates, and approve oracle creations.
3. **Receive structured progress.** Stroke-by-stroke output for Iterative Engine runs; per-Oracle harvest events; per-stroke synthesis results. Strongly typed, not free-text.
4. **Approve every Oracle creation.** The runaway-prevention guardrail (every PKI Oracle creation requires explicit caller intent) means the consumer is in the loop on each new notebook. The module needs an approve/reject mechanism — likely a callback URL or a long-poll handle.
5. **Receive a final structured resolution.** Strategic Lasso, Incomprehensible Move, Resolution text, plus per-stroke history if Iterative Engine was used. Citations preserved.

## Two integration shapes (a consumer should be able to pick either)

### Shape 1: HTTP API + WebSocket

For consumers that aren't Python (TypeScript / Node / any other language). Already partially implemented in `ganymede-backend/app/main.py`; needs extension to support multi-stroke sessions.

```
POST /api/sessions                  → start a run; returns { session_id }
GET  /api/sessions/{id}             → poll status / fetch full state
WS   /api/sessions/{id}/events      → stream stroke / oracle / harvest / synthesis events
POST /api/sessions/{id}/approve     → approve a pending Oracle creation
POST /api/sessions/{id}/reject      → reject a pending Oracle creation
POST /api/sessions/{id}/inject      → (Iterative Engine) inject friction between strokes
DELETE /api/sessions/{id}           → cancel an in-flight session
```

### Shape 2: Python library import

For Python consumers that want zero network hop. The same `GanymedeOrchestrator` class that backs the HTTP API, exposed as a public Python interface.

```python
from ganymede import GanymedeOrchestrator, Session

session = await GanymedeOrchestrator.start(
    scenario=Scenario(current_state=..., wished_for_state=...),
    pathway="genie",                        # or "cleanroom" / "offensive" / "mirror_validation"
    iterative=True,                          # multi-stroke
    max_oracles=5,                           # runaway prevention
    on_oracle_request=approve_callback,      # caller decides each new Oracle
    context_truth_packets=[...],             # optional pre-harvested facts
)

async for event in session.events():
    handle(event)

resolution = await session.result()
```

Both shapes wrap the same core. The HTTP shape is just the WS-aware wrapper around the same code.

## The core types

```python
@dataclass
class Scenario:
    """What the consumer wants the Engine to reason about."""
    # For Cleanroom / prediction-shape:
    question: Optional[str] = None

    # For Genie / Architect-shape:
    current_state: Optional[str] = None
    wished_for_state: Optional[str] = None

    # Common framing controls:
    dream_state: bool = True            # apply Genie Prime priming
    pathway: Pathway = Pathway.CLEANROOM


@dataclass
class TruthPacket:
    """A research finding the consumer wants to feed in pre-harvested."""
    subject: str                        # e.g. "Document Findings", "Prior Analysis"
    content: str                        # raw text, hash-cited
    source_label: str                   # human-readable provenance


@dataclass
class StrokeResult:
    stroke_number: int                  # 1, 2, 3
    architectural_blueprint: Optional[str]
    truth_packets: list[TruthPacket]
    resolution_text: str
    strategic_lasso: Optional[str]
    incomprehensible_move: Optional[str]


@dataclass
class SessionEvent:
    """Streamed to the consumer as the run progresses."""
    type: Literal[
        "stroke_started",
        "blueprint_ready",
        "oracle_request",       # consumer must approve before Oracle is created
        "oracle_created",
        "oracle_harvested",
        "synthesis_complete",
        "stroke_completed",
        "session_complete",
        "error",
    ]
    stroke_number: int
    payload: dict


@dataclass
class FinalResolution:
    pathway: Pathway
    strokes: list[StrokeResult]         # 1 entry for single-pass; 3 for full Iterative
    final_resolution: str
    citations: list[str]
    blind_validation_audit: Optional[str]   # if validation step was requested
```

## Lifecycle of a typical session

```
1. consumer        → POST /api/sessions { scenario, pathway, iterative, max_oracles }
                  ← 201 { session_id, status: "running" }

2. ganymede        sends Genie Prime to 9D Chess Engine
                  emits event { type: "stroke_started", stroke: 1 }
                  emits event { type: "blueprint_ready", payload: { blueprint } }

3. ganymede        parses blueprint, identifies first Oracle target
                  emits event { type: "oracle_request", payload: { subject, surgical_prompt } }
                  PAUSES execution

4. consumer        receives event, shows confirmation UI
                  POSTs /api/sessions/{id}/approve

5. ganymede        creates Oracle, sends prompt
                  emits event { type: "oracle_created", payload: { id, name } }
                  waits for user-side Import click on NotebookLM
                  ⚠ this is currently manual; see "Open: the Import-click problem" below

6. ganymede        harvests Truth Packet
                  emits event { type: "oracle_harvested", payload: { subject, truth_packet } }

7. (loop 3-6 for each Oracle the blueprint requested)

8. ganymede        runs synthesis on assembled Truth Packet stack
                  emits event { type: "synthesis_complete", payload: { stroke_result } }
                  emits event { type: "stroke_completed", stroke: 1 }

9. if iterative:
   ganymede        emits event { type: "stroke_started", stroke: 2 }
                  fires the meta-prompt asking Engine to red-team itself
                  ...
                  (or consumer can POST /api/sessions/{id}/inject with an explicit friction
                   payload to override the default red-team prompt)

10. ganymede       emits event { type: "session_complete", payload: { final_resolution } }
                  marks session as done

11. consumer       GETs /api/sessions/{id} for the persisted final state
                  stores it locally, displays it
```

## What's not yet implemented (gap analysis vs. the existing backend)

The current `app/services/orchestrator.py` exposes the right primitives but is single-call (`triage`, `create_oracle`, `send_go`, `harvest`, `synthesize`, `resolution_check`). It does not yet have:

- **A session abstraction.** Right now every endpoint is one HTTP call; there is no concept of an in-progress run that the consumer can subscribe to. Need a `Session` class that holds state across calls.
- **An event stream.** No WebSocket support. The current FastAPI app is synchronous request/response. Need to add `socketio` or FastAPI's native `WebSocket` support and route events through it.
- **Iterative Engine in code.** Currently a documented methodology; needs to be a `run_multi_stroke()` method on the Session that wires Stroke 1 → friction-injection → Stroke 2 → synthesis prompt → Stroke 3.
- **Oracle approval gate.** Currently `create_oracle()` just runs synchronously. For a session-based API, this needs to become a pause/resume around the consumer's approval.
- **Pathway selection.** The pathway-specific framings (Cleanroom prompts vs. Genie prompts vs. Architect prompts) are documented but not encoded as `Pathway` enum values that drive prompt selection.
- **Pre-harvested Truth Packet ingestion.** Right now `synthesize()` takes Truth Packets the orchestrator harvested. For consumers like PrisonBreak that already have NotebookLM-harvested findings, the API needs to accept those as Truth Packets without going back through Oracle creation.

This is roughly a 1–2 week build, depending on how clean we want the WebSocket layer.

## Open: the Import-click problem

The single biggest friction point in the current methodology — see [`../learnings/Iterative_Operational_Learnings.md`](../learnings/Iterative_Operational_Learnings.md) — is that every PKI Oracle's Deep Research session requires a manual UI Import click in the NotebookLM web app before its findings can be queried. The Python `notebooklm-py` wrapper does not expose a programmatic Import.

For consumers like PrisonBreak that want to embed Ganymede as a black-box module, this manual step is a problem. Three possible solutions:

1. **Browser automation in the bridge.** Use Playwright (already a dep) to drive the Import click. Risk: increased fragility against NotebookLM UI changes.
2. **Skip Oracle deep research; use only pre-harvested Truth Packets.** Consumers like PrisonBreak already have NotebookLM-grounded findings; they can pass those in as Truth Packets and skip the Oracle creation path entirely. This is probably the right answer for the PrisonBreak case specifically — see [`prisonbreak_consumer.md`](prisonbreak_consumer.md).
3. **Module surfaces a "click these buttons" instruction in the event stream.** If a session needs new Oracles, the event stream emits an `oracle_pending_import` event with a notebook URL; the consuming UI shows the user a "click Import in this notebook" message; the consumer POSTs `/oracle/{id}/import_done` once they've clicked.

(2) is the path of least resistance for the first integration. (3) is the right answer for sessions that genuinely need new Oracle research, and is acceptable as long as the consumer's UI surfaces it cleanly.

## Open: where Ganymede runs

Two deployment shapes:

- **Co-located Python process.** Consumer spawns Ganymede as a subprocess (the way PrisonBreak spawns its NotebookLM bridge) or runs it inline in a Python consumer.
- **HTTP service on a known port.** Consumer talks to `localhost:8000` — Ganymede running as a separate process.

The HTTP shape is more flexible but requires the consumer to manage the lifecycle. The subprocess shape is more zero-config but couples the consumer to Python being available. Reasonable to support both.

## Open questions for the user

1. **Pathway scope for v1.** Do we ship the module with all four pathways enabled (Cleanroom / Mirror / Offensive / Genie), or with just one or two? The simplest v1 is **Cleanroom + Genie**, since those are the two with confirmed runs. Mirror Validation requires the contrast notebook (not yet stood up) and Offensive shares 99% of code with Genie (just a different prompt).

2. **Pre-harvested Truth Packets vs. Oracle creation.** For the PrisonBreak case specifically, the cleanest integration is "PrisonBreak does its own NotebookLM analysis, ships Truth Packets to Ganymede, Ganymede synthesizes — no new Oracles created." Should the v1 module expose an "import-only" path that skips the Oracle creation flow entirely? My recommendation: yes, ship that path first, since it eliminates the Import-click problem.

3. **Persistence.** Sessions could be in-memory (lost on restart) or persisted (SQLite, the way PrisonBreak persists case state). Module should probably default to in-memory but expose a hook for consumers that want to persist their own way.

4. **Multi-tenancy.** The current backend is single-user (one NotebookLM auth, one Engine notebook). The module pattern doesn't change that — each consumer carries its own Ganymede instance. Cross-consumer isolation is the consumer's job. Confirm this is the model going forward.
