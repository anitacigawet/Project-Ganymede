"""Session-aware HTTP API (v2) for the Ganymede pluggable module.

This is the surface external consumers (PrisonBreak, future projects) call.
The legacy primitive endpoints in ``main.py`` (``/api/triage``,
``/api/oracle``, etc.) remain unchanged — those are operator-facing and
not part of the module contract.

Endpoint set (Phase 3, request/response only — Phase 4 adds WS streaming):

    GET  /api/v2/health                       Liveness + cooldown stats
    POST /api/v2/sessions                     Create a new session
    GET  /api/v2/sessions/{id}                Get session state
    POST /api/v2/sessions/{id}/synthesize     Run a synthesis stroke
    POST /api/v2/sessions/{id}/complete       Finalize the session
    GET  /api/v2/sessions/{id}/events         Get all events emitted so far

Conventions:
    - 404 if session not found.
    - 409 if session is not in a state that allows the operation.
    - 422 if the request body is malformed (FastAPI default).
    - 500 if the orchestrator raises something unexpected.
"""

from __future__ import annotations

import logging
from typing import Optional

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
