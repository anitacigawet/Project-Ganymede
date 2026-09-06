"""Session API for the portable Project Ganymede runtime."""

from __future__ import annotations

import asyncio
import logging
from typing import Literal, Optional

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, ConfigDict, Field

from app.contracts import FinalResolution, Pathway, Scenario, SessionEvent, SessionEventType, StrokeResult, TruthPacket
from app.services.orchestrator import GanymedeOrchestrator, SessionCancelledError
from app.services.session import Session, registry

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v2", tags=["sessions"])


def _orchestrator() -> GanymedeOrchestrator:
    from app.main import orchestrator

    return orchestrator


def _session(session_id: str) -> Session:
    found = registry().get(session_id)
    if found is None:
        raise HTTPException(status_code=404, detail=f"Session not found: {session_id}")
    return found


class SessionState(BaseModel):
    model_config = ConfigDict(extra="forbid")
    session_id: str
    status: str
    pathway: Pathway
    iterative: bool
    max_strokes: int
    strokes_so_far: int
    error_message: Optional[str] = None
    has_final_resolution: bool


def _state(session: Session) -> SessionState:
    return SessionState(
        session_id=session.id,
        status=session.status,
        pathway=session.pathway,
        iterative=session.iterative,
        max_strokes=session.max_strokes,
        strokes_so_far=len(session.strokes),
        error_message=session.error_message,
        has_final_resolution=session.final is not None,
    )


@router.get("/health")
async def health() -> dict[str, object]:
    runtime = _orchestrator().svc
    provider = runtime.provider_status()
    return {
        "status": "healthy" if provider["available"] else "setup_required",
        "provider": provider,
        "active_sessions": len(registry().list_active()),
        "usage": runtime.cooldown_stats(),
    }


class DispatchRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    text: str = Field(min_length=1)


class DispatchResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    pathway: Pathway
    confidence: float = Field(ge=0, le=1)
    scenario: Scenario
    needs_external_knowledge: bool
    rationale: str
    clarifying_questions: list[str]


@router.post("/dispatch", response_model=DispatchResponse)
async def dispatch(req: DispatchRequest) -> DispatchResponse:
    from app.services.dispatcher import DispatcherService

    result = await DispatcherService(_orchestrator().svc.engine.prompt_dir).dispatch_intent(req.text)
    return DispatchResponse.model_validate(result)


class CreateSessionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    scenario: Scenario
    pathway: Pathway
    iterative: bool = False
    max_strokes: int = Field(1, ge=1, le=20)


class CreateSessionResponse(BaseModel):
    session_id: str
    state: SessionState


@router.post("/sessions", response_model=CreateSessionResponse, status_code=201)
async def create_session(req: CreateSessionRequest) -> CreateSessionResponse:
    try:
        session = await registry().create(
            scenario=req.scenario,
            pathway=req.pathway,
            iterative=req.iterative,
            max_strokes=req.max_strokes,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return CreateSessionResponse(session_id=session.id, state=_state(session))


@router.get("/sessions")
async def list_sessions() -> dict[str, object]:
    rows = sorted(registry().list_all(), key=lambda item: item.created_at, reverse=True)
    return {
        "sessions": [
            {
                "session_id": item.id,
                "status": item.status,
                "pathway": item.pathway,
                "iterative": item.iterative,
                "max_strokes": item.max_strokes,
                "created_at": item.created_at,
                "completed_at": item.completed_at,
                "error_message": item.error_message,
                "scenario": item.scenario,
                "final_text_preview": (
                    item.final.final_text[:200] if item.final is not None else None
                ),
            }
            for item in rows
        ],
        "total": len(rows),
        "limit": len(rows),
        "offset": 0,
    }


@router.get("/sessions/{session_id}", response_model=SessionState)
async def get_session(session_id: str) -> SessionState:
    return _state(_session(session_id))


@router.get("/sessions/{session_id}/strokes")
async def get_strokes(session_id: str) -> dict[str, object]:
    session = _session(session_id)
    return {
        "session_id": session.id,
        "strokes": session.strokes,
        "translations": session.translations,
    }


class SynthesizeRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    truth_packets: list[TruthPacket] = Field(min_length=1)
    framing: Optional[str] = None


@router.post("/sessions/{session_id}/synthesize")
async def synthesize(session_id: str, req: SynthesizeRequest) -> dict[str, object]:
    session = _session(session_id)
    try:
        if session.pathway is Pathway.MIRROR_AUDIT:
            stroke = await _orchestrator().run_audit_stroke(session)
        else:
            stroke = await _orchestrator().run_synthesis_stroke(
                session, req.truth_packets, framing=req.framing
            )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return {"stroke": stroke, "state": _state(session)}


class IterateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    truth_packets: list[TruthPacket] = Field(min_length=1)
    max_strokes: Optional[int] = Field(None, ge=1, le=20)
    include_bridge: bool = True


@router.post("/sessions/{session_id}/iterate")
async def iterate(session_id: str, req: IterateRequest) -> dict[str, object]:
    session = _session(session_id)
    try:
        strokes = await _orchestrator().run_iterative_engine(
            session,
            truth_packets=req.truth_packets,
            max_strokes=req.max_strokes or session.max_strokes,
            include_bridge=req.include_bridge,
        )
    except SessionCancelledError:
        strokes = session.strokes
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return {"strokes": strokes, "state": _state(session)}


class BicameralRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    truth_packets: list[TruthPacket] = Field(min_length=1)
    max_iterations: int = Field(5, ge=1, le=10)
    min_inter_iteration_delay: float = Field(2, ge=2, le=30)


@router.post("/sessions/{session_id}/bicameral-loop")
async def bicameral_loop(session_id: str, req: BicameralRequest) -> dict[str, object]:
    session = _session(session_id)
    try:
        strokes = await _orchestrator().run_bicameral_loop(
            session,
            truth_packets=req.truth_packets,
            max_iterations=req.max_iterations,
            min_inter_iteration_delay=req.min_inter_iteration_delay,
        )
    except SessionCancelledError:
        strokes = session.strokes
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return {"strokes": strokes, "state": _state(session)}


class FullLoopRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    max_subjects: int = Field(3, ge=1, le=5)
    deep_research_timeout: float = Field(1800, gt=60, le=3600)
    max_sources_per_oracle: int = Field(30, ge=1, le=100)
    research_mode: Literal["fast", "deep"] = "deep"


@router.post("/sessions/{session_id}/run-full-loop", status_code=202)
async def run_full_loop(session_id: str, req: FullLoopRequest) -> dict[str, object]:
    session = _session(session_id)
    if session.status != "running":
        raise HTTPException(status_code=409, detail=f"Session is {session.status}")
    if session.pathway is Pathway.MIRROR_AUDIT:
        raise HTTPException(status_code=422, detail="Mirror Audit does not use WebSearch harvesting")

    async def drive() -> None:
        try:
            await _orchestrator().run_universal_loop(
                session,
                max_subjects=req.max_subjects,
                deep_research_timeout=req.deep_research_timeout,
                max_sources_per_oracle=req.max_sources_per_oracle,
                research_mode=req.research_mode,
            )
            await session.complete()
        except SessionCancelledError:
            return
        except Exception as exc:
            logger.exception("Full loop failed for %s", session.id)
            await session.fail(str(exc), type(exc).__name__)

    try:
        await session.start_operation(drive)
    except RuntimeError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return {
        "session_id": session.id,
        "status": "running",
        "poll_url": f"/api/v2/sessions/{session.id}",
        "ws_url": f"/api/v2/sessions/{session.id}/events/stream",
        "estimated_minutes": (2, max(5, req.max_subjects * 5)),
    }


@router.post("/sessions/{session_id}/complete")
async def complete(session_id: str) -> dict[str, object]:
    session = _session(session_id)
    if session.status == "error":
        raise HTTPException(status_code=409, detail=session.error_message or "Session failed")
    try:
        final: FinalResolution = await session.complete()
    except RuntimeError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return {"final_resolution": final, "state": _state(session)}


@router.post("/sessions/{session_id}/cancel")
async def cancel(session_id: str) -> dict[str, object]:
    session = _session(session_id)
    changed = await session.request_cancel()
    return {"cancelled": changed, "session_id": session.id, "state": _state(session)}


@router.get("/sessions/{session_id}/events")
async def events(session_id: str) -> dict[str, object]:
    session = _session(session_id)
    return {"session_id": session.id, "events": session.events}


@router.websocket("/sessions/{session_id}/events/stream")
async def event_stream(websocket: WebSocket, session_id: str) -> None:
    session = registry().get(session_id)
    await websocket.accept()
    if session is None:
        await websocket.close(code=1008, reason="session not found")
        return
    queue = await session.subscribe()
    try:
        while True:
            event: SessionEvent = await queue.get()
            await websocket.send_json(event.model_dump(mode="json"))
            if event.type in {
                SessionEventType.SESSION_COMPLETE,
                SessionEventType.SESSION_CANCELLED,
                SessionEventType.ERROR,
            }:
                break
    except WebSocketDisconnect:
        pass
    finally:
        await session.unsubscribe(queue)
        try:
            await websocket.close(code=1000)
        except Exception:
            pass


class TranslateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    stroke_number: int = Field(ge=1)
    register_name: str = Field(min_length=1, alias="register")


@router.post("/sessions/{session_id}/translate")
async def translate(session_id: str, req: TranslateRequest) -> dict[str, object]:
    session = _session(session_id)
    try:
        translated = await _orchestrator().run_translation(
            session, req.stroke_number, req.register_name
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    source = next(
        (
            stroke.cleaned_response or stroke.raw_response
            for stroke in session.strokes
            if stroke.stroke_number == req.stroke_number
        ),
        "",
    )
    return {
        "stroke_number": req.stroke_number,
        "register": req.register_name,
        "translated_text": translated,
        "source_length": len(source),
        "translated_length": len(translated),
    }
