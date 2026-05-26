"""Session-aware HTTP API (v2) for the Ganymede pluggable module.

This is the surface external consumers (PrisonBreak, future projects) call.
The legacy primitive endpoints in ``main.py`` (``/api/triage``,
``/api/oracle``, etc.) remain unchanged — those are operator-facing and
not part of the module contract.

Endpoint set:

    GET  /api/v2/health                       Liveness + cooldown stats

  Sessions (Phase 3+4 — request/response + WS streaming):
    POST /api/v2/sessions                     Create a new session
    GET  /api/v2/sessions/{id}                Get session state
    POST /api/v2/sessions/{id}/synthesize     Run a synthesis stroke
    POST /api/v2/sessions/{id}/iterate        Run full Iterative Engine loop
    POST /api/v2/sessions/{id}/bridge-audit   Bicameral Convergence Level 1
    POST /api/v2/sessions/{id}/complete       Finalize the session
    GET  /api/v2/sessions/{id}/events         Get all events emitted so far
    WS   /api/v2/sessions/{id}/events/stream  Live event push

  Auth pill (Phase 5 — Z-SPAN integration):
    GET  /api/v2/auth/status                  Cached NotebookLM auth probe
    POST /api/v2/auth/relogin                 Spawn ``notebooklm login`` subprocess
    POST /api/v2/auth/relogin/confirm         Feed ENTER + wait for cookie save
    GET  /api/v2/auth/relogin/status          Probe the in-flight login subprocess

Conventions:
    - 404 if session not found.
    - 409 if session is not in a state that allows the operation.
    - 422 if the request body is malformed (FastAPI default).
    - 500 if the orchestrator raises something unexpected.
"""

from __future__ import annotations

import logging
from typing import Literal, Optional

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, ConfigDict, Field

from app.contracts import (
    FinalResolution,
    Pathway,
    Scenario,
    SessionEvent,
    SessionEventType,
    StrokeResult,
    TruthPacket,
)
from app.services.notebooklm import auth_check
from app.services.orchestrator import GanymedeOrchestrator
from app.services.session import Session, registry

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v2", tags=["v2-module"])


# ---------------------------------------------------------------------------
# Dependency injection of the orchestrator
#
# The orchestrator is a process-global singleton constructed in main.py and
# attached to the FastAPI app. v2_routes pulls it from there at request
# time so tests can substitute a fixture without monkey-patching globals.
# ---------------------------------------------------------------------------

def _get_orchestrator() -> GanymedeOrchestrator:
    # main.py exposes ``orchestrator`` at module scope and attaches it to
    # the FastAPI app via ``app.state.orchestrator`` for testability.
    from app.main import orchestrator as _orch
    return _orch


# ---------------------------------------------------------------------------
# Request / response shapes
#
# Only what's not already in app.contracts. Existing contracts (Scenario,
# TruthPacket, StrokeResult, etc.) are reused directly as request/response
# bodies — Pydantic v2 + FastAPI does the rest.
# ---------------------------------------------------------------------------

class CreateSessionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    scenario: Scenario
    pathway: Pathway
    iterative: bool = False
    max_strokes: int = Field(1, ge=1, le=10)


class SessionStateResponse(BaseModel):
    """Lightweight snapshot of session state. For the full event timeline
    use ``GET /api/v2/sessions/{id}/events``."""
    model_config = ConfigDict(extra="forbid")
    session_id: str
    status: str
    pathway: Pathway
    iterative: bool
    max_strokes: int
    strokes_so_far: int
    error_message: Optional[str] = None
    has_final_resolution: bool


class CreateSessionResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    session_id: str
    state: SessionStateResponse


class SynthesizeRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    truth_packets: list[TruthPacket] = Field(min_length=1)
    framing: Optional[str] = None
    """Optional override for the synthesis prompt template. Most consumers
    leave this null and use the default holistic framing."""


class SynthesizeResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    stroke: StrokeResult
    state: SessionStateResponse


class IterateRequest(BaseModel):
    """Drive the full Iterative Engine multi-stroke loop in one call.

    The session must have been created with ``iterative=True`` and
    ``max_strokes >= 2``. The server runs Stroke 1 (thesis synthesis),
    Stroke 2 (Mirror Auditor audit), and Stroke 3 (friction-injected
    re-synthesis) in sequence, emitting STROKE_STARTED/STROKE_COMPLETED
    events on the session as it goes. WebSocket subscribers see each
    stroke land in real time.

    The HTTP request blocks until the loop terminates (or fails) — for
    UI consumers, prefer subscribing to the WS stream so the UI can
    render strokes as they arrive instead of waiting on a single
    long-blocking call. The HTTP response carries the full result list
    for callers that want it as one payload.
    """
    model_config = ConfigDict(extra="forbid")
    truth_packets: list[TruthPacket] = Field(min_length=1)
    max_strokes: Optional[int] = Field(
        default=None, ge=1, le=10,
        description=(
            "Cap on strokes for this loop. Defaults to the session's own "
            "``max_strokes``. Pass a smaller value (e.g. 2) to stop after "
            "the audit stroke without re-synthesis."
        ),
    )


class IterateResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    strokes: list[StrokeResult]
    state: SessionStateResponse


class BridgeAuditRequest(BaseModel):
    """Run a single Connection Bridge audit stroke against a Stroke 1 (or
    arbitrary target) text. Bicameral Convergence Level 1.

    The Bridge enumerates *missed connections* between Truth Packets that
    the Engine's synthesis didn't draw — an orthogonal lens to the Mirror
    Auditor's fault-mode enumeration. See
    ``docs/concepts/Bicameral_Convergence.md`` for the architectural
    framing.

    The caller must provide ``bridge_notebook_id`` for a non-canonical
    notebook with the foundations corpus + the scenario's Truth Packets
    pre-loaded. Setup flow (typically via the ``/api/v2/notebooks/*``
    endpoints): create a notebook, upload foundations + Truth Packets,
    then pass the resulting ID here. The Bridge persona is re-applied
    at call time (idempotent), so the notebook doesn't need to have been
    pre-configured as a Bridge.

    Operational cost: one NotebookLM query call (gated by the cooldown).
    The setup cost — creating + uploading sources — is borne separately
    and is typically ~15+ calls.
    """
    model_config = ConfigDict(extra="forbid")
    bridge_notebook_id: str = Field(
        min_length=1,
        description=(
            "Notebook ID to use as the Bridge. Must NOT be one of the "
            "canonical IDs (CHESS_ENGINE_ID, MIRROR_AUDITOR_ID, "
            "LEGACY_ENGINE_ID). The notebook should already have the "
            "foundations corpus + scenario Truth Packets uploaded."
        ),
    )
    target_text: Optional[str] = Field(
        default=None,
        description=(
            "The analysis text to bridge-audit. Defaults to the most "
            "recent stroke's raw_response (the natural Stroke 1 → Bridge "
            "audit pattern). Pass an explicit value to audit something "
            "other than the most recent stroke."
        ),
    )
    scenario_context: Optional[str] = Field(
        default=None,
        description=(
            "Optional override for the scenario framing. Defaults to "
            "derived from the session's scenario."
        ),
    )


class BridgeAuditResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    stroke: StrokeResult
    state: SessionStateResponse


class CompleteResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    final_resolution: FinalResolution
    state: SessionStateResponse


class EventsResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    session_id: str
    events: list[SessionEvent]
    """All events emitted on the session so far, in chronological order.
    Phase 4 will add a WebSocket variant that pushes new events as they're
    emitted, instead of requiring polling."""


class CooldownStatsResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    calls_last_hour: int
    calls_last_24h: int
    hourly_cap: int
    daily_cap: int
    api_cooldown_sec: float
    session_cooldown_sec: float


class HealthResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    status: str
    cooldown: CooldownStatsResponse
    active_sessions: int


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _state(session: Session) -> SessionStateResponse:
    return SessionStateResponse(
        session_id=session.id,
        status=session.status,
        pathway=session.pathway,
        iterative=session.iterative,
        max_strokes=session.max_strokes,
        strokes_so_far=len(session.strokes),
        error_message=session.error_message,
        has_final_resolution=session.final is not None,
    )


def _require_session(session_id: str) -> Session:
    s = registry().get(session_id)
    if s is None:
        raise HTTPException(status_code=404, detail=f"Session not found: {session_id}")
    return s


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------

@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    """Liveness check + cooldown gate stats + active session count.

    Consumers should hit this before starting a multi-step operation to
    confirm the gate isn't already saturated.
    """
    orch = _get_orchestrator()
    stats = orch.svc.cooldown_stats()
    return HealthResponse(
        status="healthy",
        cooldown=CooldownStatsResponse(**stats),
        active_sessions=len(registry().list_active()),
    )


# ---------------------------------------------------------------------------
# Dispatcher (Intent Router) — the opinionated wrapper on the open primitive.
#
# Single free-text input -> lightweight Gemini Flash classification -> pathway
# + extracted scenario parameters + optional clarifying questions. The
# frontend uses this so operators don't have to pick a pathway and fill in
# pathway-specific form fields manually. Sits in front of POST /sessions.
# ---------------------------------------------------------------------------

_gemini_dispatch_svc = None


def _get_gemini_dispatch_service():
    """Lazy singleton for the dispatcher's Gemini client.

    Defers construction (and therefore the GOOGLE_API_KEY env-var check)
    until the first /dispatch call, so tests and Studio-only flows don't
    require Gemini credentials.
    """
    global _gemini_dispatch_svc
    if _gemini_dispatch_svc is None:
        from app.services.gemini_service import GeminiService
        _gemini_dispatch_svc = GeminiService()
    return _gemini_dispatch_svc


class DispatchRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    text: str = Field(min_length=1)
    """Free-text scenario description from the operator. The dispatcher
    classifies the intent and extracts the matching pathway-shaped
    parameters."""


class DispatchResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    pathway: Pathway
    confidence: float = Field(ge=0.0, le=1.0)
    """Classifier confidence in [0, 1]. Low values mean the user's text was
    ambiguous; the frontend should foreground ``clarifying_questions`` in
    that case rather than auto-proceeding to /sessions."""

    scenario: Scenario
    """Populated with the pathway-specific fields the classifier extracted.
    The operator reviews this before kicking off the 3-stroke loop."""

    rationale: str
    """One-sentence explanation of why this pathway was chosen — surfaced to
    the operator so they can sanity-check the classification."""

    clarifying_questions: list[str]
    """Up to 2 questions the classifier wants answered before it can fill
    out the scenario confidently. Empty when the classification is clean."""


@router.post("/dispatch", response_model=DispatchResponse)
async def dispatch_intent(req: DispatchRequest) -> DispatchResponse:
    """Classify a free-text scenario into a pathway + populated parameters.

    This is the opinionated wrapper that hides the v2 API's jargon (DAP,
    SDS, ROEM, Lasso, the Cleanroom/Genie/Offensive/Mirror-Audit
    distinction) behind a single conversational text box. The classifier
    is a lightweight Gemini Flash call — fast, cheap, separate from the
    heavy NotebookLM Engine calls.

    Workflow expected by the frontend:

        1. Operator types a natural-language scenario.
        2. Frontend POSTs to ``/api/v2/dispatch``.
        3. Frontend surfaces the response: classified pathway, confidence,
           extracted scenario, rationale, and any clarifying questions.
        4. Operator reviews / edits / answers clarifications.
        5. Frontend POSTs the (possibly edited) scenario to ``/api/v2/sessions``.

    On Gemini failures the service falls back to ``cleanroom`` with the
    user's text as the question and confidence ``0.0`` + an explanatory
    clarifying question — so the frontend never has to handle a 500 from
    this endpoint, just a low-confidence response it can guide the user
    through.
    """
    svc = _get_gemini_dispatch_service()
    result = await svc.dispatch_intent(req.text)

    # Filter the scenario dict to only the known Scenario fields so an
    # over-eager Gemini emission can't trip Scenario's extra=forbid.
    allowed_fields = set(Scenario.model_fields.keys())
    filtered_scenario = {
        k: v for k, v in (result.get("scenario") or {}).items() if k in allowed_fields
    }

    try:
        scenario = Scenario(**filtered_scenario)
    except Exception as exc:
        logger.warning("dispatch: scenario construction failed (%s); using empty scenario", exc)
        scenario = Scenario()

    return DispatchResponse(
        pathway=Pathway(result["pathway"]),
        confidence=result["confidence"],
        scenario=scenario,
        rationale=result["rationale"],
        clarifying_questions=result["clarifying_questions"],
    )


# ---------------------------------------------------------------------------
# Sessions
# ---------------------------------------------------------------------------

@router.post(
    "/sessions",
    response_model=CreateSessionResponse,
    status_code=201,
)
async def create_session(req: CreateSessionRequest) -> CreateSessionResponse:
    """Create a new Session. The session is stored in-memory in the
    process-global registry and is ready to receive synthesis strokes."""
    try:
        session = await registry().create(
            scenario=req.scenario,
            pathway=req.pathway,
            iterative=req.iterative,
            max_strokes=req.max_strokes,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    logger.info(
        "v2 session created: %s pathway=%s iterative=%s",
        session.id, req.pathway.value, req.iterative,
    )
    return CreateSessionResponse(session_id=session.id, state=_state(session))


@router.get("/sessions/{session_id}", response_model=SessionStateResponse)
async def get_session(session_id: str) -> SessionStateResponse:
    """Get a snapshot of the session's current state."""
    return _state(_require_session(session_id))


@router.post(
    "/sessions/{session_id}/synthesize",
    response_model=SynthesizeResponse,
)
async def synthesize_stroke(
    session_id: str,
    req: SynthesizeRequest,
) -> SynthesizeResponse:
    """Run one synthesis stroke against the canonical Engine using the
    pre-harvested Truth Packets supplied in the request body.

    This is the path consumers like PrisonBreak use — they have their own
    grounded RAG layer (NotebookLM in PrisonBreak's case) that has already
    produced source-cited findings, so Ganymede skips the Oracle creation
    and harvest stages and goes straight to Engine synthesis.

    The session's strokes list grows by 1 on success. The session does
    NOT auto-complete; the caller drives ``/complete`` when ready.

    Returns the new StrokeResult plus a snapshot of session state.
    """
    session = _require_session(session_id)
    orch = _get_orchestrator()

    if session.status != "running":
        raise HTTPException(
            status_code=409,
            detail=f"Session {session_id} is not running (status={session.status})",
        )

    try:
        stroke = await orch.run_synthesis_stroke(
            session,
            truth_packets=req.truth_packets,
            framing=req.framing,
        )
    except ValueError as exc:
        # Pathway/contract mismatch
        raise HTTPException(status_code=422, detail=str(exc))
    except RuntimeError as exc:
        # Session in wrong state
        raise HTTPException(status_code=409, detail=str(exc))
    except Exception as exc:
        logger.exception("synthesize_stroke failed for session %s", session_id)
        # Session.fail() was already called inside run_synthesis_stroke
        raise HTTPException(status_code=500, detail=str(exc))

    return SynthesizeResponse(stroke=stroke, state=_state(session))


@router.post(
    "/sessions/{session_id}/iterate",
    response_model=IterateResponse,
)
async def iterate_session(
    session_id: str,
    req: IterateRequest,
) -> IterateResponse:
    """Run the full Iterative Engine multi-stroke loop in one HTTP call.

    Convenience over making N separate ``/synthesize`` calls. The
    orchestrator drives Stroke 1 → Stroke 2 (audit) → Stroke 3 internally
    and emits stroke events on the session as each lands; WS subscribers
    see them in real time. Returns when the loop terminates.

    Errors:
        409 if the session is not in a runnable state (e.g. already
            completed, or not iterative).
        422 if ``max_strokes`` is out of bounds for this session.
        500 on unexpected orchestrator failure (the session is also
            transitioned to error state internally).
    """
    session = _require_session(session_id)
    orch = _get_orchestrator()

    if session.status != "running":
        raise HTTPException(
            status_code=409,
            detail=f"Session {session_id} is not running (status={session.status})",
        )

    max_strokes = req.max_strokes if req.max_strokes is not None else session.max_strokes
    try:
        strokes = await orch.run_iterative_engine(
            session,
            truth_packets=req.truth_packets,
            max_strokes=max_strokes,
        )
    except ValueError as exc:
        # Non-iterative session or max_strokes out of range
        raise HTTPException(status_code=422, detail=str(exc))
    except RuntimeError as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    except Exception as exc:
        logger.exception("iterate_session failed for session %s", session_id)
        raise HTTPException(status_code=500, detail=str(exc))

    return IterateResponse(strokes=strokes, state=_state(session))


@router.post(
    "/sessions/{session_id}/bridge-audit",
    response_model=BridgeAuditResponse,
)
async def bridge_audit_session(
    session_id: str,
    req: BridgeAuditRequest,
) -> BridgeAuditResponse:
    """Run one Connection Bridge audit stroke — Bicameral Convergence Level 1.

    Structural sibling of the Mirror Auditor's audit (which is invoked
    inline as Stroke 2 of ``/iterate``). The Bridge runs on a
    caller-supplied non-canonical notebook and enumerates *missed
    connections* between Truth Packets that the Engine's synthesis didn't
    draw — an orthogonal lens to the Auditor's fault-mode catches.

    Typical caller flow:
        1. POST /api/v2/sessions  (create session)
        2. POST /api/v2/sessions/{id}/synthesize  (run Stroke 1)
        3. POST /api/v2/notebooks  (create Bridge notebook)
        4. POST /api/v2/notebooks/{id}/sources/file  (upload foundations
           corpus, repeat per source file)
        5. POST /api/v2/notebooks/{id}/sources/file  (upload scenario
           Truth Packets, repeat per packet)
        6. POST /api/v2/sessions/{id}/bridge-audit  ← this endpoint
           (Bridge persona is auto-applied; one audit query fires)
        7. POST /api/v2/notebooks/{id} DELETE  (clean up Bridge notebook
           — optional, but recommended if the notebook isn't reused)

    Setup steps 3-5 are ~15+ NotebookLM calls; this endpoint itself is
    1 call. For ad-hoc audits the setup is meaningful overhead; for
    long-lived scenarios the same Bridge notebook can be reused across
    many audits.

    Errors:
        404 if the session doesn't exist.
        409 if the session is not running.
        422 if ``bridge_notebook_id`` is one of the canonical IDs (Engine,
            Auditor, Legacy), or if there's no prior stroke and no
            ``target_text`` was supplied.
        500 on unexpected orchestrator failure (the session is also
            transitioned to error state internally).
    """
    session = _require_session(session_id)
    orch = _get_orchestrator()

    if session.status != "running":
        raise HTTPException(
            status_code=409,
            detail=f"Session {session_id} is not running (status={session.status})",
        )

    try:
        stroke = await orch.audit_with_bridge(
            session,
            bridge_notebook_id=req.bridge_notebook_id,
            target_text=req.target_text,
            scenario_context=req.scenario_context,
        )
    except ValueError as exc:
        # Canonical notebook ID supplied, or no prior stroke + no
        # target_text. Both are caller errors — 422 Unprocessable Entity.
        raise HTTPException(status_code=422, detail=str(exc))
    except RuntimeError as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    except Exception as exc:
        logger.exception("bridge_audit_session failed for session %s", session_id)
        raise HTTPException(status_code=500, detail=str(exc))

    return BridgeAuditResponse(stroke=stroke, state=_state(session))


class RunFullLoopRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    max_subjects: int = Field(default=3, ge=1, le=5)
    """How many PKI Oracles to spawn. Each Oracle = 1 notebook + Deep
    Research run (5-20min) + harvest. Capped at 5 to keep total runtime
    sane; default 3 matches the historic Powell-class runs."""
    deep_research_timeout: float = Field(default=1800.0, gt=60.0, le=3600.0)
    """Per-Oracle Deep Research timeout in seconds (default 30 min)."""
    max_sources_per_oracle: int = Field(default=30, ge=1, le=100)
    research_mode: Literal["fast", "deep"] = Field(default="deep")
    """NotebookLM research mode. ``deep`` is multi-minute web-grounded
    Deep Research (default — what historic Powell-class runs used);
    ``fast`` is a single quick pass with a much smaller source pool but
    completes in seconds-to-minutes. Useful for iterating on the scenario
    text without burning a full 20-30 min on every test."""


class RunFullLoopResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    session_id: str
    status: str
    poll_url: str
    ws_url: str
    estimated_minutes: tuple[int, int]
    """Rough wall-clock estimate (low, high) in minutes — based on
    max_subjects × per-Oracle Deep Research time."""


@router.post(
    "/sessions/{session_id}/run-full-loop",
    response_model=RunFullLoopResponse,
    status_code=202,
)
async def run_full_loop(
    session_id: str,
    req: RunFullLoopRequest,
) -> RunFullLoopResponse:
    """Kick off the full Universal Logic Loop on a session as a background task.

    Phase 1 (Triage with structured Hit List) → Phase 2 (per-subject PKI
    Oracle creation + programmatic Deep Research + Import + harvest) →
    Phase 3 (Synthesis at the Engine using the harvested Truth Packets).

    Returns 202 immediately with poll/WS URLs. Subscribe to the WS stream
    for live events: ``blueprint_ready``, ``oracle_request``,
    ``oracle_created``, ``oracle_harvested``, ``stroke_started``,
    ``synthesis_complete``, ``stroke_completed``, ``session_complete``.

    Long-running: 15-60 minutes for 3 Oracles depending on Deep Research
    speed. The session is auto-completed (or auto-failed) when the loop
    finishes — caller does NOT need to POST /complete separately.
    """
    import asyncio  # local import — used only on this path

    session = _require_session(session_id)
    orch = _get_orchestrator()

    if session.status != "running":
        raise HTTPException(
            status_code=409,
            detail=f"Session {session_id} is not running (status={session.status})",
        )
    if session.pathway.value not in ("cleanroom", "genie", "offensive"):
        raise HTTPException(
            status_code=422,
            detail=(
                f"run_full_loop does not support pathway {session.pathway.value}. "
                "Mirror Audit operates on supplied prior_resolution and does "
                "not spawn Oracles."
            ),
        )

    async def _drive_loop() -> None:
        try:
            await orch.run_universal_loop(
                session,
                max_subjects=req.max_subjects,
                deep_research_timeout=req.deep_research_timeout,
                max_sources_per_oracle=req.max_sources_per_oracle,
                research_mode=req.research_mode,
            )
            # Auto-finalise — Phase 3's run_synthesis_stroke already
            # recorded the synthesis stroke; complete() seals the session
            # and emits SESSION_COMPLETE.
            await session.complete()
        except Exception as exc:
            logger.exception("Full Universal Logic Loop failed for session %s", session_id)
            await session.fail(str(exc), exc_type=type(exc).__name__)

    # Fire-and-track: caller polls /sessions/{id} or subscribes to WS.
    asyncio.create_task(_drive_loop(), name=f"ul-loop-{session.id[:8]}")

    # Rough estimate: Triage ~30s + per-Oracle (Deep Research 3-15min +
    # 4 gated calls × 8s + harvest) + Synthesis ~30s.
    low = max(2, req.max_subjects * 4)
    high = max(10, req.max_subjects * 18)

    return RunFullLoopResponse(
        session_id=session.id,
        status="running",
        poll_url=f"/api/v2/sessions/{session.id}",
        ws_url=f"/api/v2/sessions/{session.id}/events/stream",
        estimated_minutes=(low, high),
    )


@router.post(
    "/sessions/{session_id}/complete",
    response_model=CompleteResponse,
)
async def complete_session(session_id: str) -> CompleteResponse:
    """Finalize the session and return the FinalResolution.

    Idempotent — calling on an already-completed session returns the
    same FinalResolution. Returns 409 if the session has no strokes.
    Returns 409 if the session is in error state.
    """
    session = _require_session(session_id)
    if session.status == "error":
        raise HTTPException(
            status_code=409,
            detail=f"Session {session_id} is errored: {session.error_message}",
        )
    try:
        final = await session.complete()
    except RuntimeError as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    return CompleteResponse(final_resolution=final, state=_state(session))


@router.get(
    "/sessions/{session_id}/events",
    response_model=EventsResponse,
)
async def get_events(session_id: str) -> EventsResponse:
    """Get all events emitted on the session so far, in chronological order.

    For polling-style consumers. Real-time push is at the WS endpoint
    below — preferred for UI consumers that want stroke-by-stroke
    rendering as the work happens.
    """
    session = _require_session(session_id)
    return EventsResponse(session_id=session.id, events=session.events)


# ---------------------------------------------------------------------------
# WebSocket event stream
#
# Real-time push of SessionEvents to a connected consumer. The connection
# starts by replaying every event the session has emitted so far (so the
# consumer's UI can render the full timeline up to "now"), then streams
# every subsequent event as it's emitted, and closes cleanly on the first
# terminal event (SESSION_COMPLETE or ERROR).
# ---------------------------------------------------------------------------

# WebSocket close codes used here:
#   1000  Normal closure (terminal event reached)
#   1008  Policy violation (session not found)
_WS_NORMAL = 1000
_WS_NOT_FOUND = 1008


@router.websocket("/sessions/{session_id}/events/stream")
async def stream_events(websocket: WebSocket, session_id: str) -> None:
    """Real-time SessionEvent stream for one Session.

    Wire format: each message is a JSON object matching the
    :class:`SessionEvent` schema (``type``, ``stroke_number``,
    ``payload``, ``emitted_at``). The server closes the connection
    after sending the terminal event (SESSION_COMPLETE or ERROR).

    If the consumer disconnects mid-stream, the server's subscriber is
    cleaned up automatically (no leak).
    """
    session = registry().get(session_id)
    if session is None:
        # Accept then close with a policy code so the client gets a
        # structured signal rather than an opaque connection failure.
        await websocket.accept()
        await websocket.close(code=_WS_NOT_FOUND, reason="session not found")
        return

    await websocket.accept()
    queue = await session.subscribe()
    try:
        while True:
            event = await queue.get()
            await websocket.send_json(event.model_dump(mode="json"))
            if event.type in (
                SessionEventType.SESSION_COMPLETE,
                SessionEventType.ERROR,
            ):
                # Drain any remaining events the emitter may have queued
                # immediately after the terminal one (defensive — there
                # shouldn't be any, but a misbehaving emitter shouldn't
                # leave us stuck).
                while not queue.empty():
                    extra = queue.get_nowait()
                    await websocket.send_json(extra.model_dump(mode="json"))
                break
    except WebSocketDisconnect:
        # Consumer dropped; nothing to send.
        pass
    finally:
        await session.unsubscribe(queue)
        try:
            await websocket.close(code=_WS_NORMAL)
        except Exception:
            # If the socket is already closed (consumer disconnected, or
            # we sent a terminal event and the client closed first),
            # close() may raise. Safe to ignore.
            pass


# ---------------------------------------------------------------------------
# Auth pill endpoints (Phase 5 — Z-SPAN bridge integration)
#
# Stateless wrappers over the ``app.services.notebooklm.auth_check`` module.
# Lets a consumer (or a future Ganymede UI) check session-cookie health,
# spawn ``notebooklm login`` as a subprocess for re-auth, then confirm once
# the user has completed the browser sign-in.
#
# These endpoints do not pass through the cooldown gate — ``check_auth_status``
# loads cookies from disk and at most makes one cheap verification call;
# the relogin endpoints drive a local subprocess and don't touch the
# upstream API directly.
# ---------------------------------------------------------------------------

class AuthStatusResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    status: str
    """One of: ``valid``, ``expired``, ``missing``, ``unknown``."""
    details: Optional[str] = None
    checked_at: Optional[str] = None
    cached: bool = False
    cache_age_seconds: Optional[float] = None
    client_initialized: bool = True
    """Whether the backend's ``notebooklm_svc.client`` is alive. This can
    drift from ``status``: if cookies were refreshed outside the app (e.g.
    ``python -m notebooklm login`` in a separate terminal), ``status``
    flips to ``valid`` immediately but the in-process service object is
    still the failed one from startup. Frontend uses this to detect the
    mismatch and auto-fire ``POST /api/v2/auth/reinitialize``."""


class AuthForceQuery(BaseModel):
    """Optional ``?force=true`` query string for ``GET /api/v2/auth/status``.

    Defined as a Pydantic model so the FastAPI OpenAPI surface documents the
    parameter explicitly. Most consumers leave force=False and accept the
    300s-TTL cached response.
    """
    model_config = ConfigDict(extra="forbid")
    force: bool = False


class ReloginSpawnResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    spawned: bool
    cmd: Optional[str] = None
    pid: Optional[int] = None
    note: Optional[str] = None
    error: Optional[str] = None


class ReloginConfirmRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    timeout_seconds: float = Field(30.0, gt=0, le=300)
    """How long to wait for the login subprocess to exit after we feed ENTER.
    30s is usually plenty — the CLI just saves cookies and exits."""


class ReloginConfirmResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    confirmed: bool
    exit_code: Optional[int] = None
    output: Optional[str] = None
    note: Optional[str] = None
    error: Optional[str] = None


class ReloginStatusResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    in_flight: bool
    exited: bool
    pid: Optional[int] = None
    exit_code: Optional[int] = None


@router.get("/auth/status", response_model=AuthStatusResponse)
async def auth_status(force: bool = False) -> AuthStatusResponse:
    """Cached NotebookLM auth probe + backend-client liveness.

    Returns whether the locally-stored session cookies are valid AND
    whether the in-process ``notebooklm_svc.client`` is alive. The two
    can disagree: cookies refreshed outside the app (terminal-side
    ``notebooklm login``) make ``status=valid`` immediately but leave
    ``client_initialized=false`` until the service is re-initialized.

    The auth-status result is cached for 300s (tunable via
    ``GANYMEDE_NOTEBOOKLM_AUTH_CHECK_TTL``); pass ``?force=true`` to
    bypass the cache. The ``client_initialized`` field is always live.
    """
    from app.main import notebooklm_svc
    result = await auth_check.check_auth_status_async(force=force)
    return AuthStatusResponse(
        **result,
        client_initialized=notebooklm_svc.client is not None,
    )


@router.post("/auth/relogin", response_model=ReloginSpawnResponse)
async def auth_relogin() -> ReloginSpawnResponse:
    """Spawn ``python -m notebooklm login`` as a child subprocess.

    The subprocess opens a browser to Google's OAuth page, then blocks on
    stdin waiting for ENTER. Returns immediately so the UI can prompt the
    user to complete sign-in. After the user finishes in the browser,
    call :func:`auth_relogin_confirm` to feed ENTER and finalize the
    cookie save.

    If a previous relogin is still in flight, it is killed before a new
    one is spawned.
    """
    return ReloginSpawnResponse(**auth_check.spawn_relogin())


@router.post("/auth/relogin/confirm", response_model=ReloginConfirmResponse)
async def auth_relogin_confirm(req: ReloginConfirmRequest) -> ReloginConfirmResponse:
    """Feed ENTER to the in-flight ``notebooklm login`` subprocess.

    Call this ONLY after the user has actually completed Google sign-in
    in the launched browser. The subprocess will save cookies on receiving
    ENTER, then exit. ``confirmed=True`` indicates a clean exit code.

    On a successful confirm, the singleton ``notebooklm_svc`` is reinitialised
    so the fresh cookies are picked up immediately. Without this, a backend
    that started with expired cookies would have ``svc.client is None`` and
    every subsequent NotebookLM call would fail with
    "NotebookLMClient is not initialized" even though storage_state.json is
    now healthy.
    """
    result = auth_check.confirm_relogin(timeout_seconds=req.timeout_seconds)
    if result.get("confirmed"):
        from app.main import notebooklm_svc
        try:
            # close() is a no-op when the service was never initialised
            # (e.g. the backend started with expired cookies); safe either way.
            await notebooklm_svc.close()
        except Exception:
            logger.debug("notebooklm_svc.close() raised during reinit; ignoring")
        try:
            await notebooklm_svc.initialize()
            logger.info("notebooklm_svc reinitialised after relogin confirm")
        except Exception as exc:
            logger.exception("notebooklm_svc reinit failed after relogin")
            result["note"] = (
                (result.get("note") or "")
                + f" (warning: backend service reinit failed: {exc}; restart backend manually)"
            ).strip()
    return ReloginConfirmResponse(**result)


@router.get("/auth/relogin/status", response_model=ReloginStatusResponse)
async def auth_relogin_status() -> ReloginStatusResponse:
    """Lightweight probe of the relogin subprocess state.

    Returns whether a subprocess is currently in flight, whether it has
    already exited (waiting for confirm), or absent.
    """
    return ReloginStatusResponse(**auth_check.relogin_status())


class ReinitializeResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    reinitialized: bool
    client_initialized: bool
    """Whether ``notebooklm_svc.client`` is alive AFTER the reinit attempt.
    True even if the close() leg threw, as long as initialize() succeeded."""
    details: Optional[str] = None
    error: Optional[str] = None


@router.post("/auth/reinitialize", response_model=ReinitializeResponse)
async def auth_reinitialize() -> ReinitializeResponse:
    """Close + re-initialize the backend's ``notebooklm_svc``.

    Use when cookies were refreshed outside the app (e.g. terminal-side
    ``python -m notebooklm login``) and the in-process service object is
    still the failed one from startup. The AuthPill auto-fires this when
    it sees ``status=valid`` paired with ``client_initialized=false``.

    Idempotent and safe — if the close fails, init still runs; if init
    fails, the field reports the error and the service stays unhealthy
    so the next call surfaces the same problem cleanly.
    """
    from app.main import notebooklm_svc

    try:
        await notebooklm_svc.close()
    except Exception:
        logger.debug("notebooklm_svc.close() raised during reinit; ignoring")

    try:
        await notebooklm_svc.initialize()
        # Invalidate the cached auth-status so the next pill probe is fresh.
        auth_check.invalidate_cache()
        return ReinitializeResponse(
            reinitialized=True,
            client_initialized=notebooklm_svc.client is not None,
            details="NotebookLMService re-initialized; cookies in use are now whatever is on disk.",
        )
    except Exception as exc:
        logger.exception("notebooklm_svc reinit failed")
        return ReinitializeResponse(
            reinitialized=False,
            client_initialized=False,
            details="Initialize failed — cookies on disk may still be expired.",
            error=str(exc),
        )
