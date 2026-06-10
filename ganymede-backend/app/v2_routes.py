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
from app.services.orchestrator import GanymedeOrchestrator, SessionCancelledError
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


class SessionSummary(BaseModel):
    """One row for the ``GET /api/v2/sessions`` list endpoint.

    Lightweight by design — the list view is for browsing history (Z-SPAN
    walking back through prior strategic-planning sessions), not for
    loading full stroke text. Use ``GET /sessions/{id}`` and
    ``GET /sessions/{id}/strokes`` for detail.
    """
    model_config = ConfigDict(extra="forbid")
    session_id: str
    status: str
    pathway: Pathway
    iterative: bool
    max_strokes: int
    created_at: str
    """ISO-8601 UTC timestamp string. The store persists timestamps as
    strings so passing them through here without round-tripping to
    datetime keeps the API surface noise-free."""
    completed_at: Optional[str] = None
    error_message: Optional[str] = None
    scenario: Scenario
    final_text_preview: Optional[str] = None
    """First 200 chars of the session's ``final_text`` if the session
    completed, else None. Helps the list view show what each session
    actually resolved to without forcing a per-row detail fetch."""


class SessionsListResponse(BaseModel):
    """Paginated response for ``GET /api/v2/sessions``."""
    model_config = ConfigDict(extra="forbid")
    sessions: list[SessionSummary]
    total: int
    """Total matching rows. Lets clients render pagination UI without
    a second count query."""
    limit: int
    offset: int


class SessionStrokesResponse(BaseModel):
    """Response for ``GET /api/v2/sessions/{id}/strokes``."""
    model_config = ConfigDict(extra="forbid")
    session_id: str
    strokes: list[StrokeResult]
    translations: dict[str, str] = Field(default_factory=dict)
    """Pl3 Operator Lens translations keyed by ``"{stroke_number}:{register}"``.
    Returned alongside strokes so clients can render the translation panel
    state in one round-trip rather than firing per-stroke translation
    fetches."""


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
    ``max_strokes >= 2``. With Bridge enabled (default) the server runs
    Stroke 1 (thesis synthesis), Stroke 2 (Mirror Auditor audit), Stroke
    2b (Connection Bridge audit), and Stroke 3 (friction-injected
    re-synthesis with BOTH audits in the prompt) in sequence. With
    ``include_bridge=False`` the loop reverts to the historic 3-stroke
    shape (Stroke 1 → Auditor → re-synthesis with Auditor-only friction).

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
            "the audit stroke without re-synthesis. NOTE: with Bridge "
            "enabled the loop has 4 stroke slots (S1, Auditor, Bridge, "
            "re-synth); ``max_strokes`` caps at that number too."
        ),
    )
    include_bridge: bool = Field(
        default=True,
        description=(
            "Run the Connection Bridge as Stroke 2b alongside the Mirror "
            "Auditor. Default True — Bicameral Convergence Level 1 is "
            "the production audit shape. Adds ~3-5 min wall time (Bridge "
            "notebook provisioning + 1 audit query) and ~14 NotebookLM "
            "calls per run. Set False for the historic 3-stroke shape."
        ),
    )
    bridge_notebook_id: Optional[str] = Field(
        default=None,
        description=(
            "Existing Bridge notebook ID to reuse. Optional. When None and "
            "``include_bridge=True``, the orchestrator auto-provisions a "
            "fresh Bridge notebook inline (synchronous; adds ~3 min to the "
            "iterate response). Reusing a Bridge notebook across runs is "
            "faster but only valid if the substrate (foundations + Truth "
            "Packets) hasn't changed. Must NOT be a canonical notebook ID."
        ),
    )


class IterateResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    strokes: list[StrokeResult]
    state: SessionStateResponse


class BicameralLoopRequest(BaseModel):
    """Drive the Bicameral Convergence Level 2 closed-loop mirror-bounce.

    Engine ↔ Bridge iteration until convergence or hard cap. Where
    ``/iterate`` (Level 1) is a 3-stroke thesis-antithesis-synthesis with
    single-pass audit, this is N-stroke closed-loop convergence with
    Bridge as the sole friction lens.

    The endpoint blocks until the loop terminates. WS subscribers see
    BICAMERAL_ITERATION_START/END events around each iteration and one of
    BICAMERAL_CONVERGED / BICAMERAL_HARD_CAP_REACHED at termination. The
    operator can cancel mid-loop via ``POST /sessions/{id}/cancel``; the
    loop observes the flag at its next NotebookLM-call boundary, raises
    ``SessionCancelledError``, and this endpoint returns 200 with the
    strokes that landed before cancellation (per the same pattern as
    ``/iterate``).
    """
    model_config = ConfigDict(extra="forbid")
    truth_packets: list[TruthPacket] = Field(min_length=1)
    max_iterations: int = Field(
        default=5, ge=1, le=10,
        description=(
            "Hard iteration cap. Loop terminates with "
            "BICAMERAL_HARD_CAP_REACHED if no convergence by this point. "
            "1-10 inclusive. Default 5."
        ),
    )
    min_inter_iteration_delay: float = Field(
        default=5.0, ge=2.0, le=30.0,
        description=(
            "Seconds to sleep between iterations (after Bridge audit, "
            "before next Engine synthesis). Operator-tunable inspection "
            "window — gives time to watch WS events + decide whether to "
            "cancel before the next iteration kicks off. 2-30s inclusive. "
            "Default 5s."
        ),
    )
    bridge_notebook_id: Optional[str] = Field(
        default=None,
        description=(
            "Existing Bridge notebook ID to reuse across all iterations. "
            "Optional. When None, auto-provisions on iteration 1 and "
            "reuses across subsequent iterations. Reusing pre-built "
            "Bridge notebooks across runs is faster but only valid if "
            "the substrate (foundations + Truth Packets) hasn't changed. "
            "Must NOT be a canonical notebook ID."
        ),
    )


class BicameralLoopResponse(BaseModel):
    """Response shape for ``POST /api/v2/sessions/{id}/bicameral-loop``.

    ``strokes`` includes every stroke produced during the loop — 2 per
    iteration (Engine synthesis + Bridge audit), plus partial strokes if
    cancellation interrupted mid-iteration. ``state`` reflects terminal
    status (``complete`` on natural termination after caller's
    ``/complete``, ``cancelled`` on operator cancel, ``error`` on
    failure mid-loop, ``running`` if the caller invokes
    ``/bicameral-loop`` and then handles ``/complete`` separately).
    """
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


class CancelResponse(BaseModel):
    """Response shape for ``POST /api/v2/sessions/{id}/cancel``.

    ``cancelled=True`` means this call transitioned the session to the
    ``cancelled`` terminal state. ``cancelled=False`` means the session
    was already terminal (complete / error / cancelled) and this call
    was a no-op (idempotent).

    Any in-flight orchestrator loop running on the session observes the
    cancel flag at its next NotebookLM-call boundary and raises
    ``SessionCancelledError``, which the ``/iterate`` endpoint catches
    and returns as a 200 with whatever partial strokes had landed.
    """
    model_config = ConfigDict(extra="forbid")
    cancelled: bool
    session_id: str
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
# Managed run — the canonical entry point for session-as-consumer projects
#
# The granular API (/dispatch + /sessions + /iterate + /translate + /complete)
# requires the consumer to learn pathway selection, Truth Packet shape,
# iterative vs Bicameral Level 2 escalation, register choice — appropriate
# for embedded-app consumers like PrisonBreak that need fine-grained
# control over each step for the in-app UI.
#
# Session-as-consumer projects (Z-SPAN, future Claude sessions) don't need
# that control surface. They want to send a natural-language strategic
# question + their source-grounded context and get back analytical output.
# This endpoint bundles dispatch → create → iterate (or bicameral_loop) →
# translate → complete into one HTTP call so the consumer never has to
# learn the framework's internal vocabulary.
#
# Architectural call (milestone 48): the dispatcher is the canonical
# entry point for both human operators (via DispatcherPanel) and
# session-as-consumer projects (via this endpoint). One natural-language
# entry surface, two render-out surfaces (UI for humans, JSON for
# sessions). Same closed-RAG-sphere principle as Pl3 Operator Lens —
# the framework abstracts itself for the audience.
# ---------------------------------------------------------------------------

class ManagedRunRequest(BaseModel):
    """Inputs for ``POST /api/v2/managed-run``.

    The consumer brings two things: a natural-language strategic
    question + source-grounded Truth Packets. Ganymede handles
    everything else (pathway selection, multi-stroke orchestration,
    translation, session completion).
    """
    model_config = ConfigDict(extra="forbid")
    scenario_text: str = Field(min_length=1)
    """The strategic question in plain language. Examples:
    *"How should Z-SPAN respond to Granicus's defensive bundling move
    when civic-tech RFPs start asking for open-data export?"*
    *"Should Z-SPAN double down on 'Public Truth Ledger' terminology
    or pivot to 'Citizen-First Infrastructure'?"*
    The dispatcher classifies this into a pathway internally."""

    truth_packets: list[TruthPacket] = Field(min_length=1)
    """The consumer's source-grounded context. Operator-curated is fine;
    no RAG infrastructure required. Each packet has a subject (short
    label) + content (the body of the finding) + optional source_label
    (audit trail). 3-5 packets is the typical Z-SPAN shape."""

    register: str = Field(default="plain_english")
    """Translation register for the audited final. One of:
    ``plain_english`` (default — strip framework jargon),
    ``executive_brief`` (3-5 paragraph decision-maker summary),
    ``cube_of_space`` (geometric/spatial vocabulary).
    See ``app.contracts.TranslationRegister`` for the full descriptions."""

    depth: Literal["iterate", "bicameral_loop"] = "iterate"
    """Loop depth. Default ``iterate`` (Bicameral Convergence Level 1 —
    3 strokes with Bridge as Stroke 2b, ~10-15 min wall time).
    ``bicameral_loop`` (Level 2) iterates Engine↔Bridge until
    convergence or hard cap — longer wall time, higher decision-grade
    output. Escalate when Level 1's Bridge surfaces unresolved
    structural friction or when the question is high-enough-stakes
    to justify the extra time."""

    max_iterations: Optional[int] = Field(default=None, ge=1, le=10)
    """Hard iteration cap for ``depth=bicameral_loop``. Default 5
    (the loop's own default). Ignored when ``depth=iterate``."""

    include_bridge: bool = True
    """Whether to run the Connection Bridge alongside the Mirror
    Auditor for ``depth=iterate``. Default True — Bicameral
    Convergence Level 1 is the production audit shape. Ignored when
    ``depth=bicameral_loop`` (which always uses Bridge)."""

    pathway_override: Optional[Pathway] = None
    """If the consumer already knows the pathway (skip the dispatcher's
    Gemini Flash call), set this. Default None — let the dispatcher
    classify. Useful for batch/testing scenarios where the pathway is
    known and the Gemini call is unnecessary overhead."""


class ManagedRunResponse(BaseModel):
    """Response for ``POST /api/v2/managed-run``.

    Carries everything the consumer needs: the session_id (for later
    browsing via ``GET /sessions/{id}/strokes``), the chosen pathway
    (transparency on the dispatcher's classification), the audited
    final text (raw, framework-vocabulary), the translated text (in
    the chosen register, audience-facing), and the full stroke history
    (for when the consumer wants to understand the per-stage
    reasoning behind the final output).
    """
    model_config = ConfigDict(extra="forbid")
    session_id: str
    pathway_chosen: Pathway
    dispatch_confidence: float = Field(ge=0.0, le=1.0)
    """The dispatcher's classification confidence in [0, 1]. 1.0 when
    ``pathway_override`` was supplied. Low values (< 0.5) mean the
    dispatcher wasn't sure — the consumer can check
    ``clarifying_questions`` for follow-up prompts."""
    dispatch_rationale: str
    """One-sentence explanation of why the dispatcher chose this pathway.
    Useful for the consumer to sanity-check the classification before
    acting on the output."""
    clarifying_questions: list[str]
    """Up to 2 questions the dispatcher would have wanted answered for
    a more confident classification. Empty when confidence was clean.
    The consumer may re-run with ``scenario_text`` refined."""

    depth: str
    """Echo of the depth used (``iterate`` or ``bicameral_loop``)."""

    register: str
    """Echo of the register used."""

    final_text: str
    """The audited final, in framework vocabulary. For iterative runs
    this is the Stroke 3 ``final_resolution`` (preferring
    ``cleaned_response`` if P1-03b's CTA-strip ran). For Bicameral
    Level 2 runs it's the final iteration's synthesis. This is the
    technical artifact — file it in the consumer's audit trail for
    traceability. The ``translated_text`` is what to read to a
    human."""

    translated_text: str
    """The same audited final, re-expressed in the chosen ``register``.
    Preserves the analytical claims 1:1 while swapping framework
    jargon for legible vocabulary. This is the canonical
    audience-facing artifact."""

    strokes: list[StrokeResult]
    """Full stroke history, in order. Useful when the consumer wants
    to understand WHY the final output is what it is — Stroke 1
    (thesis), Stroke 2 (Mirror Auditor critique), Stroke 2b (Connection
    Bridge missed-connections audit if include_bridge=True), Stroke 3
    (re-synthesis with both audits as friction). For Bicameral Level 2
    runs this carries every iteration's Engine + Bridge pair."""

    state: SessionStateResponse
    """Final session state snapshot for cross-call consistency with the
    rest of the v2 API."""


@router.post(
    "/managed-run",
    response_model=ManagedRunResponse,
    status_code=200,
)
async def managed_run(req: ManagedRunRequest) -> ManagedRunResponse:
    """Single-call composition of dispatch → create → iterate (or bicameral_loop) → translate → complete.

    The recommended entry point for session-as-consumer projects
    (Z-SPAN, future Claude sessions). The consumer sends a
    natural-language strategic question + source-grounded Truth
    Packets + an optional register; Ganymede internally classifies
    pathway, drives the multi-stroke loop, translates the audited
    final into the chosen register, and completes the session.

    The granular API (/dispatch + /sessions + /iterate + /translate +
    /complete) remains the right surface for embedded-app consumers
    (PrisonBreak) that need fine-grained control over each step for
    the in-app UI. Both shapes are first-class.

    Wall time:
        - ``depth=iterate``: ~10-15 minutes (4 NotebookLM strokes +
          Bridge provision + translation call).
        - ``depth=bicameral_loop``: ~10-30 minutes depending on
          iteration count (per-iteration Engine + Bridge pair until
          convergence or hard cap).

    WS subscribers can watch live progress on
    ``/sessions/{session_id}/events/stream`` — the session is created
    and persisted before the loop fires, so the WS subscription works
    from the moment this endpoint accepts the request.

    Errors:
        422 — empty scenario_text, empty truth_packets, malformed
              register, or other contract validation failures.
        500 — dispatcher failure, orchestrator failure, translation
              failure (session transitioned to error state internally).

    Cancel semantics: if the operator hits ``POST /sessions/{id}/cancel``
    mid-loop, this endpoint catches ``SessionCancelledError`` and
    returns 200 with partial strokes (matching the ``/iterate`` /
    ``/bicameral-loop`` pattern). ``translated_text`` is best-effort
    on the last completed stroke.
    """
    # 1. Dispatcher: classify pathway + extract scenario fields
    if req.pathway_override is not None:
        # Consumer skipped dispatch. Build a minimal scenario from the
        # text using ``question`` as the default field — the orchestrator's
        # pathway-templates will fall back to other fields per the
        # ``Pathway`` it was told to use.
        pathway = req.pathway_override
        scenario = Scenario(question=req.scenario_text)
        dispatch_confidence = 1.0
        dispatch_rationale = (
            f"Consumer-supplied pathway_override={pathway.value}; "
            f"dispatcher skipped."
        )
        clarifying_questions: list[str] = []
    else:
        svc = _get_gemini_dispatch_service()
        try:
            dispatch_result = await svc.dispatch_intent(req.scenario_text)
        except Exception as exc:
            logger.exception("managed_run: dispatcher failed")
            raise HTTPException(status_code=500, detail=f"Dispatch failed: {exc}")

        pathway = Pathway(dispatch_result["pathway"])
        allowed_fields = set(Scenario.model_fields.keys())
        filtered_scenario = {
            k: v
            for k, v in (dispatch_result.get("scenario") or {}).items()
            if k in allowed_fields
        }
        try:
            scenario = Scenario(**filtered_scenario)
        except Exception as exc:
            logger.warning(
                "managed_run: scenario construction from dispatch failed "
                "(%s); falling back to question-only",
                exc,
            )
            scenario = Scenario(question=req.scenario_text)
        dispatch_confidence = dispatch_result["confidence"]
        dispatch_rationale = dispatch_result["rationale"]
        clarifying_questions = list(dispatch_result["clarifying_questions"])

    # 2. Create session — always iterative since managed-run is the
    # heavy-shape path. max_strokes=3 fits Stroke 1 + Stroke 2 (audit) +
    # Stroke 3 (re-synthesis); the Bridge as Stroke 2b runs inside that
    # budget.
    try:
        session = await registry().create(
            scenario=scenario,
            pathway=pathway,
            iterative=True,
            max_strokes=3,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    orch = _get_orchestrator()

    # 3. Drive the loop. Cancellation produces partial strokes; the
    # endpoint still returns 200 with the partial result.
    try:
        if req.depth == "iterate":
            strokes = await orch.run_iterative_engine(
                session,
                truth_packets=req.truth_packets,
                include_bridge=req.include_bridge,
            )
        else:  # bicameral_loop
            max_iter = (
                req.max_iterations if req.max_iterations is not None else 5
            )
            strokes = await orch.run_bicameral_loop(
                session,
                truth_packets=req.truth_packets,
                max_iterations=max_iter,
            )
    except SessionCancelledError as exc:
        logger.info(
            "managed_run: session %s cancelled at %s; returning partial",
            session.id, exc.where,
        )
        partial = session.strokes
        partial_translated = ""
        if partial:
            try:
                partial_translated = await orch.run_translation(
                    session, partial[-1].stroke_number, req.register,
                )
            except Exception as t_exc:
                logger.warning(
                    "managed_run: partial-translation failed for %s: %s",
                    session.id, t_exc,
                )
        return ManagedRunResponse(
            session_id=session.id,
            pathway_chosen=pathway,
            dispatch_confidence=dispatch_confidence,
            dispatch_rationale=dispatch_rationale,
            clarifying_questions=clarifying_questions,
            depth=req.depth,
            register=req.register,
            final_text=(
                partial[-1].cleaned_response or partial[-1].raw_response
                if partial else ""
            ),
            translated_text=partial_translated,
            strokes=partial,
            state=_state(session),
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except RuntimeError as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    except Exception as exc:
        logger.exception("managed_run: loop failed for session %s", session.id)
        raise HTTPException(status_code=500, detail=f"Loop failed: {exc}")

    if not strokes:
        raise HTTPException(
            status_code=500,
            detail=f"Loop returned no strokes for session {session.id}",
        )

    # 4. Translate the final stroke into the chosen register.
    final_stroke = strokes[-1]
    try:
        translated_text = await orch.run_translation(
            session, final_stroke.stroke_number, req.register,
        )
    except Exception as exc:
        logger.warning(
            "managed_run: translation failed for session %s (%s) — "
            "returning untranslated final as translated_text",
            session.id, exc,
        )
        translated_text = (
            final_stroke.cleaned_response or final_stroke.raw_response
        )

    # 5. Complete the session.
    try:
        final_resolution = await session.complete()
    except Exception as exc:
        logger.exception(
            "managed_run: complete failed for session %s", session.id,
        )
        raise HTTPException(status_code=500, detail=f"Complete failed: {exc}")

    return ManagedRunResponse(
        session_id=session.id,
        pathway_chosen=pathway,
        dispatch_confidence=dispatch_confidence,
        dispatch_rationale=dispatch_rationale,
        clarifying_questions=clarifying_questions,
        depth=req.depth,
        register=req.register,
        final_text=final_resolution.final_text,
        translated_text=translated_text,
        strokes=strokes,
        state=_state(session),
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


@router.get("/sessions", response_model=SessionsListResponse)
async def list_sessions(
    status: Optional[str] = None,
    pathway: Optional[Pathway] = None,
    q: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
) -> SessionsListResponse:
    """List prior sessions, ordered newest-first.

    Pl2-01: the surface Z-SPAN (the first Pl2 consumer) uses to browse
    its accumulated strategic-planning sessions weeks after they were
    initially run.

    Filters:
        status   — running / complete / error / cancelled (exact match)
        pathway  — cleanroom / genie / offensive / mirror_audit
        q        — substring match over scenario JSON + final_text. Plain
                   SQLite LIKE; FTS5 if needed at scale.
        limit    — 1..200 (default 50)
        offset   — pagination offset

    Returns ``{ sessions, total, limit, offset }``. Persisted store is
    the source of truth — in-memory-only mode (no store bound) returns
    empty.
    """
    if limit < 1 or limit > 200:
        raise HTTPException(status_code=422, detail="limit must be 1..200")
    if offset < 0:
        raise HTTPException(status_code=422, detail="offset must be >= 0")

    store = registry().store
    if store is None:
        # In-memory-only mode (tests / GANYMEDE_DISABLE_SESSION_PERSISTENCE=1)
        return SessionsListResponse(sessions=[], total=0, limit=limit, offset=offset)

    pathway_str = pathway.value if pathway is not None else None
    import asyncio as _asyncio

    if q:
        # search() doesn't honor status/pathway/offset; we filter post-hoc.
        # Z-SPAN's q-with-filter case is rare; keeping the store API tight.
        rows = await _asyncio.to_thread(store.search, q, limit + offset + 200)
        if status:
            rows = [r for r in rows if r["status"] == status]
        if pathway_str:
            rows = [r for r in rows if r["pathway"] == pathway_str]
        total = len(rows)
        rows = rows[offset : offset + limit]
    else:
        total = await _asyncio.to_thread(store.count, status, pathway_str)
        rows = await _asyncio.to_thread(
            store.list_summaries, status, pathway_str, limit, offset,
        )

    summaries: list[SessionSummary] = []
    for r in rows:
        try:
            scenario = Scenario.model_validate_json(r["scenario_json"])
        except Exception as exc:
            logger.warning(
                "list_sessions: malformed scenario_json for %s — surfacing "
                "empty scenario in the summary row (%s)",
                r["id"], exc,
            )
            scenario = Scenario()
        final_text = r.get("final_text")
        preview = (final_text[:200] + "…") if final_text and len(final_text) > 200 else final_text
        summaries.append(
            SessionSummary(
                session_id=r["id"],
                status=r["status"],
                pathway=Pathway(r["pathway"]),
                iterative=bool(r["iterative"]),
                max_strokes=int(r["max_strokes"]),
                created_at=r["created_at"],
                completed_at=r["completed_at"],
                error_message=r["error_message"],
                scenario=scenario,
                final_text_preview=preview,
            )
        )

    return SessionsListResponse(
        sessions=summaries, total=total, limit=limit, offset=offset,
    )


@router.get("/sessions/{session_id}", response_model=SessionStateResponse)
async def get_session(session_id: str) -> SessionStateResponse:
    """Get a snapshot of the session's current state."""
    return _state(_require_session(session_id))


@router.get(
    "/sessions/{session_id}/strokes",
    response_model=SessionStrokesResponse,
)
async def get_session_strokes(session_id: str) -> SessionStrokesResponse:
    """Return all strokes recorded on a session, plus any Operator Lens
    translations keyed by ``{stroke_number}:{register}``.

    Pl2-01: the natural endpoint Z-SPAN hits when the operator clicks
    into a prior session from the list view. State summary is on
    ``GET /sessions/{id}``; the event timeline is on
    ``GET /sessions/{id}/events``; this one is the stroke-detail view.
    """
    session = _require_session(session_id)
    return SessionStrokesResponse(
        session_id=session.id,
        strokes=session.strokes,
        translations=session.translations,
    )


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
            include_bridge=req.include_bridge,
            bridge_notebook_id=req.bridge_notebook_id,
        )
    except SessionCancelledError as exc:
        # Operator hit POST /sessions/{id}/cancel mid-loop. Session is
        # already in the "cancelled" terminal state (the cancel endpoint
        # transitions it synchronously). Return 200 with whatever strokes
        # had landed before cancellation so the caller can see partial
        # progress. The session.strokes snapshot is what made it onto the
        # session via record_stroke; orch.run_iterative_engine's local
        # `results` list may not have been appended for the in-flight
        # stroke at cancellation, but session.strokes is the source of
        # truth and matches what the caller saw via WS events.
        logger.info(
            "iterate_session: session %s cancelled at %s; returning %d partial stroke(s)",
            session_id, exc.where, len(session.strokes),
        )
        return IterateResponse(strokes=session.strokes, state=_state(session))
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
    "/sessions/{session_id}/bicameral-loop",
    response_model=BicameralLoopResponse,
)
async def bicameral_loop_session(
    session_id: str,
    req: BicameralLoopRequest,
) -> BicameralLoopResponse:
    """Run the Bicameral Convergence Level 2 closed-loop mirror-bounce (E1-06).

    Each iteration: Engine synthesizes (with prior iteration's Bridge
    findings as friction, if any) → Bridge audits → convergence check.
    Loop terminates when no new STRUCTURAL/IMPLIED bridges are surfaced
    (no_new_structural criterion), when the Engine's FINAL RESOLUTION
    section is functionally unchanged across iterations (resolution_stable
    criterion), or when ``max_iterations`` is reached without convergence
    (hard cap).

    Subscribe to the WS stream at
    ``/api/v2/sessions/{id}/events/stream`` to render live progress —
    BICAMERAL_ITERATION_START/END events around each iteration plus one
    of BICAMERAL_CONVERGED / BICAMERAL_HARD_CAP_REACHED at termination.

    Long-running: each iteration is ~2-3 min (Engine synthesis + Bridge
    audit + delay), plus ~3-5 min on iteration 1 for Bridge notebook
    auto-provisioning if no ``bridge_notebook_id`` is supplied. Worst-
    case wall time at default settings (5 iterations, 5s delay): ~20 min.

    Cancel handling: operator hits ``POST /sessions/{id}/cancel`` to
    interrupt mid-loop. The loop observes the cancel flag at iteration
    boundaries + before each NotebookLM call, raises
    ``SessionCancelledError``, and this endpoint returns 200 with
    ``session.strokes`` (partial progress preserved). Same pattern as
    ``/iterate``.

    Errors:
        404 if the session doesn't exist.
        409 if the session is not in a runnable state (already completed,
            not iterative).
        422 if ``max_iterations`` / ``min_inter_iteration_delay`` are
            out of bounds or the session is not iterative.
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
        strokes = await orch.run_bicameral_loop(
            session,
            truth_packets=req.truth_packets,
            max_iterations=req.max_iterations,
            min_inter_iteration_delay=req.min_inter_iteration_delay,
            bridge_notebook_id=req.bridge_notebook_id,
        )
    except SessionCancelledError as exc:
        # Operator cancelled mid-loop. session.strokes is the source of
        # truth for what landed before cancellation. Return 200 with
        # the partial result list — same pattern as iterate_session.
        logger.info(
            "bicameral_loop_session: session %s cancelled at %s; returning %d partial stroke(s)",
            session_id, exc.where, len(session.strokes),
        )
        return BicameralLoopResponse(strokes=session.strokes, state=_state(session))
    except ValueError as exc:
        # Non-iterative session, max_iterations out of range, or delay out of range
        raise HTTPException(status_code=422, detail=str(exc))
    except RuntimeError as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    except Exception as exc:
        logger.exception("bicameral_loop_session failed for session %s", session_id)
        raise HTTPException(status_code=500, detail=str(exc))

    return BicameralLoopResponse(strokes=strokes, state=_state(session))


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


@router.post(
    "/sessions/{session_id}/cancel",
    response_model=CancelResponse,
)
async def cancel_session(session_id: str) -> CancelResponse:
    """Cancel an in-flight session (E1-01 — Bicameral Convergence Level 2 prerequisite).

    Sets the session's ``cancel_requested`` flag and transitions it to
    the ``cancelled`` terminal state synchronously. Any in-flight
    orchestrator loop (e.g. ``run_iterative_engine`` invoked via
    ``/iterate``) observes the flag at its next NotebookLM-call
    boundary and raises ``SessionCancelledError``, which the
    ``/iterate`` endpoint catches and returns as a 200 with whatever
    partial strokes had landed.

    Idempotent. If the session is already terminal (complete / error /
    cancelled), returns ``cancelled=False`` and 200 — no exception
    raised — so polling consumers don't have to special-case the race
    between "loop finished on its own" and "cancel landed first."

    Errors:
        404 if the session doesn't exist.

    Returns:
        200 with ``{cancelled, session_id, state}``. ``cancelled=True``
        means this call transitioned the session; ``cancelled=False``
        means the session was already terminal (no-op).
    """
    session = _require_session(session_id)
    cancelled = await session.request_cancel()
    return CancelResponse(
        cancelled=cancelled,
        session_id=session.id,
        state=_state(session),
    )


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
                SessionEventType.SESSION_CANCELLED,
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
# Pl3 Operator Lens — translation endpoint
#
# Takes a previously-recorded stroke + a register, returns the translation.
# Translation is server-cached on the session so re-fetching the same
# (stroke, register) pair doesn't burn another Gemini call.
# ---------------------------------------------------------------------------

class TranslateRequest(BaseModel):
    """Translate a stroke into an operator-facing vocabulary register.

    The translation preserves the analytical claims 1:1 while swapping
    framework jargon for legible operator-facing vocabulary. Routes
    through the canonical NotebookLM Engine (NOT Gemini Flash) so the
    model has foundations-corpus grounding when translating — the same
    grounding that made the milestone 43 Cube-of-Space exchange work in
    the first place. Closed-RAG-sphere discipline preserved.
    """
    model_config = ConfigDict(extra="forbid")
    stroke_number: int = Field(ge=1)
    """The stroke to translate (1-indexed). Use the stroke_number from
    StrokeResult or the SYNTHESIS_COMPLETE event's payload."""
    register: str = Field(min_length=1)
    """One of: ``plain_english`` / ``cube_of_space`` / ``executive_brief``.
    See ``app.contracts.TranslationRegister`` for descriptions."""


class TranslateResponse(BaseModel):
    """Response shape for ``POST /api/v2/sessions/{id}/translate``."""
    model_config = ConfigDict(extra="forbid")
    stroke_number: int
    register: str
    translated_text: str
    source_length: int
    """Length of the source text (cleaned_response if P1-03b stripped a
    CTA, otherwise raw_response). Useful for the UI to compute compression
    ratio + decide whether to show side-by-side or stacked."""
    translated_length: int


@router.post(
    "/sessions/{session_id}/translate",
    response_model=TranslateResponse,
)
async def translate_stroke(
    session_id: str,
    req: TranslateRequest,
) -> TranslateResponse:
    """Translate a stroke into the chosen operator-facing register (Pl3).

    Preserves the analytical claims 1:1 while swapping framework jargon
    for legible vocabulary. Routes through the canonical NotebookLM
    Engine (NOT Gemini Flash) — translation is analytical content (it
    carries strategic claims forward), so it lives in the closed RAG
    sphere alongside Engine / Auditor / Bridge. The foundations-corpus
    grounding is what lets the model actually understand what the
    framework concepts mean during translation — same grounding that
    made the milestone 43 Cube-of-Space exchange work.

    Operational cost: one cooldown-gated NotebookLM call per translation
    (~30-50s wall — same speed as a normal synthesis stroke). Cached
    server-side on the session so re-fetching the same (stroke, register)
    pair returns the prior result without another NotebookLM call.
    (Currently the endpoint always re-translates and overwrites — future
    polish: ``?cached=true`` query arg to use the server-side cache.)

    Errors:
        404 if the session doesn't exist.
        422 if the stroke doesn't exist on the session, the stroke has
            empty response text, or the register is invalid.
        500 if NotebookLM fails — caller-visible (translation transients
            don't fail the session itself).
    """
    session = _require_session(session_id)
    orch = _get_orchestrator()

    try:
        translated = await orch.run_translation(
            session,
            stroke_number=req.stroke_number,
            register=req.register,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except RuntimeError as exc:
        logger.exception(
            "translate_stroke: Gemini failed for session %s stroke %d register %s",
            session_id, req.stroke_number, req.register,
        )
        raise HTTPException(status_code=500, detail=str(exc))

    # Find the source length for the response payload — the orchestrator
    # used cleaned_response or raw_response; we replicate that lookup so
    # the UI can show the compression ratio.
    source_length = 0
    for s in session.strokes:
        if s.stroke_number == req.stroke_number:
            source = s.cleaned_response or s.raw_response
            source_length = len(source or "")
            break

    return TranslateResponse(
        stroke_number=req.stroke_number,
        register=req.register,
        translated_text=translated,
        source_length=source_length,
        translated_length=len(translated),
    )


# ---------------------------------------------------------------------------
# Bridge notebook survey endpoint (P1-04 — operator-managed lifecycle)
#
# Per the 2026-06-06 operator decision: Bridge notebooks stay until the
# operator explicitly deletes them (no auto-cleanup). To make that
# manageable as the consumer surface grows (Z-SPAN as Pl2 first consumer),
# the GET /api/v2/bridge/notebooks endpoint returns a categorized survey
# table the operator UI renders with per-row delete buttons + suggested
# action labels ("delete" / "review" / "keep") + a one-line reason per
# suggestion. The operator clicks delete on the rows they decide are
# safe; the existing DELETE /api/v2/notebooks/{id} endpoint handles the
# actual delete + deregisters from the survey registry.
#
# The registry is populated server-side at provision time
# (run_iterative_engine Level 1, run_bicameral_loop Level 2, and the
# standalone /bridge/provision endpoint). It does NOT see operator-
# curated notebooks created outside the orchestrator's auto-provision
# paths — those remain manually managed.
# ---------------------------------------------------------------------------

class BridgeNotebookRow(BaseModel):
    """One row in the bridge-notebook survey table."""
    model_config = ConfigDict(extra="forbid")
    notebook_id: str
    title: str
    created_at: str
    """ISO-8601 UTC timestamp."""
    age_hours: float
    session_id: Optional[str] = None
    session_status: Optional[str] = None
    """``running`` / ``complete`` / ``cancelled`` / ``error`` if the
    originating session is still tracked; null when the session is gone
    (process restart / discard) or wasn't tracked (standalone path)."""
    provision_path: str
    """Which code path provisioned this notebook:
        ``"iterate_level_1"`` / ``"bicameral_loop_level_2"`` / ``"standalone_provision"``."""
    foundations_uploaded: int
    truth_packets_uploaded: int
    suggested_action: str
    """One of ``"delete"`` / ``"review"`` / ``"keep"`` — advisory.
    Operator makes the final call; this row reflects what the heuristic
    thinks based on session status + notebook age."""
    suggested_category: str
    """One of ``"likely_safe_to_delete"`` / ``"review"`` / ``"recently_used"``.
    UI renders with a color-coded badge."""
    reason: str
    """Human-readable one-line explanation surfaced inline next to the
    category badge."""


class BridgeNotebookSurveyResponse(BaseModel):
    """Response shape for ``GET /api/v2/bridge/notebooks``."""
    model_config = ConfigDict(extra="forbid")
    notebooks: list[BridgeNotebookRow]
    total: int
    safe_to_delete: int
    """Count of rows where suggested_action == "delete" — drives the
    UI's badge count for "you could clean N notebooks right now"."""
    needs_review: int
    """Count of rows where suggested_action == "review"."""
    keep: int
    """Count of rows where suggested_action == "keep"."""


@router.get(
    "/bridge/notebooks",
    response_model=BridgeNotebookSurveyResponse,
)
async def bridge_notebook_survey() -> BridgeNotebookSurveyResponse:
    """List auto-provisioned Bridge notebooks with per-row delete suggestions.

    Returns every Bridge notebook the orchestrator has auto-provisioned
    in the current backend process, with metadata + a categorization
    suggestion per row. The operator UI renders this as a table with
    delete buttons + color-coded badges; the operator decides which rows
    to delete.

    Categorization heuristic (see ``BridgeNotebookRegistry.list_with_suggestions``
    for the exact rules) considers session status + notebook age:
        - Session terminal AND >2h old → likely_safe_to_delete + delete
        - Session terminal AND ≤2h old → review (recent — may re-audit)
        - Session running → recently_used + keep
        - Session unknown AND >48h old → likely_safe_to_delete + delete
        - Session unknown AND ≤48h old → review

    The registry is in-memory: clears on backend restart. Operator-
    curated notebooks (created outside the orchestrator's auto-provision
    paths) are NOT in this survey; manage those via raw API calls.
    """
    from app.services.bridge_registry import registry as bridge_notebook_registry

    # Build the session-status lookup so the survey can categorize based
    # on whether the originating session is still running.
    session_status_lookup = {
        s.id: s.status for s in registry().list_all()
    }
    rows_data = bridge_notebook_registry().list_with_suggestions(
        session_status_lookup=session_status_lookup,
    )

    rows = [
        BridgeNotebookRow(
            notebook_id=r.notebook_id,
            title=r.title,
            created_at=r.created_at.isoformat(),
            age_hours=round(r.age_hours, 2),
            session_id=r.session_id,
            session_status=r.session_status,
            provision_path=r.provision_path,
            foundations_uploaded=r.foundations_uploaded,
            truth_packets_uploaded=r.truth_packets_uploaded,
            suggested_action=r.suggested_action,
            suggested_category=r.suggested_category,
            reason=r.reason,
        )
        for r in rows_data
    ]
    safe_to_delete = sum(1 for r in rows if r.suggested_action == "delete")
    needs_review = sum(1 for r in rows if r.suggested_action == "review")
    keep = sum(1 for r in rows if r.suggested_action == "keep")
    return BridgeNotebookSurveyResponse(
        notebooks=rows,
        total=len(rows),
        safe_to_delete=safe_to_delete,
        needs_review=needs_review,
        keep=keep,
    )


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


class AutoReloginResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    auto_relogin: bool
    """True iff the end-to-end auto-relogin flow ran (subprocess spawn +
    prompt detection + ENTER feed). False on early bailouts (spawn failure,
    auto-relogin disabled by env var)."""
    confirmed: bool
    """True iff the ``notebooklm login`` subprocess exited cleanly (cookies
    saved successfully)."""
    exit_code: Optional[int] = None
    client_initialized: bool
    """Whether ``notebooklm_svc.client`` is alive AFTER the relogin+reinit.
    May be False even when ``confirmed=True`` if reinit itself failed."""
    output: Optional[str] = None
    """Captured stdout from the ``notebooklm login`` subprocess. Useful for
    debugging when ``confirmed=False``."""
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


@router.post("/auth/auto-relogin", response_model=AutoReloginResponse)
async def auth_auto_relogin() -> AutoReloginResponse:
    """End-to-end auto re-auth: spawn ``notebooklm login``, automate ENTER, reinit.

    Wraps :func:`app.services.notebooklm.auth_check.auto_relogin`. Pattern
    ported from Z-SPAN's pre-flight auth check: the ``notebooklm login`` CLI
    uses Playwright's persistent profile, so if the operator's still signed
    in to Google in that profile (the steady state), the OAuth auto-completes
    and only the ENTER confirmation needs automation. Closes the recurring
    "cookies expired again, hit the AuthPill" interruption when the profile
    is healthy.

    Falls back gracefully if the profile is NOT healthy — the function returns
    ``confirmed=false`` with an explanatory ``error``; the caller should then
    use the manual ``/auth/relogin`` + ``/auth/relogin/confirm`` flow.

    On a successful relogin, this endpoint ALSO reinitialises the
    ``notebooklm_svc`` singleton so subsequent calls pick up the fresh
    cookies without a second round-trip to ``/auth/reinitialize``.

    Set ``GANYMEDE_AUTO_RELOGIN=0`` to disable auto-relogin entirely (the
    function will return early with ``auto_relogin=false`` and an error
    naming the env var).
    """
    from app.main import notebooklm_svc

    if not auth_check.auto_relogin_enabled():
        return AutoReloginResponse(
            auto_relogin=False,
            confirmed=False,
            client_initialized=notebooklm_svc.client is not None,
            error=(
                "Auto-relogin is disabled (GANYMEDE_AUTO_RELOGIN=0). "
                "Use POST /api/v2/auth/relogin + /auth/relogin/confirm "
                "for the manual flow."
            ),
        )

    # auto_relogin is synchronous (it manages a subprocess + thread); run
    # it on the default executor so we don't block the event loop for
    # the ~10-20s the relogin takes.
    import asyncio
    loop = asyncio.get_running_loop()
    try:
        result = await loop.run_in_executor(None, auth_check.auto_relogin)
    except Exception as exc:
        logger.exception("auto_relogin raised")
        return AutoReloginResponse(
            auto_relogin=False,
            confirmed=False,
            client_initialized=notebooklm_svc.client is not None,
            error=f"auto_relogin raised: {type(exc).__name__}: {exc}",
        )

    # If the relogin confirmed, reinitialize the service so callers don't
    # have to hit /auth/reinitialize separately.
    client_initialized = notebooklm_svc.client is not None
    if result.get("confirmed"):
        try:
            await notebooklm_svc.close()
        except Exception:
            logger.debug(
                "notebooklm_svc.close() raised during post-relogin reinit; ignoring"
            )
        try:
            await notebooklm_svc.initialize()
            auth_check.invalidate_cache()
            client_initialized = notebooklm_svc.client is not None
        except Exception as exc:
            logger.exception("notebooklm_svc reinit failed after auto-relogin")
            result["error"] = (
                (result.get("error") or "")
                + f" (warning: reinit failed after relogin: {exc})"
            ).strip()

    return AutoReloginResponse(
        auto_relogin=bool(result.get("auto_relogin")),
        confirmed=bool(result.get("confirmed")),
        exit_code=result.get("exit_code"),
        client_initialized=client_initialized,
        output=result.get("output"),
        error=result.get("error"),
    )
