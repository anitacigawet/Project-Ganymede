"""Public data contracts for the Ganymede module.

These are the types a *consuming project* would interact with — both via the
HTTP API in :mod:`app.main` and (eventually, when published) via direct
Python import. Designed to be consumer-agnostic: PrisonBreak is the first
validation case but nothing in this module references it specifically.

Pydantic v2 models are used throughout so the same definitions can serve
both as in-memory contracts and as FastAPI request/response schemas with
automatic JSON Schema export for TypeScript consumers.

Conventions:
    - All datetimes are timezone-aware UTC.
    - All durations are floats in seconds.
    - All IDs are UUIDv4 strings.
    - Enum values are lowercase strings (TypeScript-friendly).

See :doc:`docs/integration/module_design.md` for the API design rationale.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field


# ---------------------------------------------------------------------------
# Pathway — which 9D-Chess Engine framing the Session uses
# ---------------------------------------------------------------------------

class TranslationRegister(str, Enum):
    """Pl3 Operator Lens — vocabulary register for downstream translation
    of a stroke's analytical output.

    The translation stroke (``GanymedeOrchestrator.run_translation``)
    takes a previously-recorded stroke's ``raw_response`` and re-expresses
    it in the chosen register, preserving the analytical claims 1:1 while
    swapping the framework jargon for legible operator-facing vocabulary.

    Pl3 surfaced 2026-06-06 from the Cube-of-Space transcript exchange.
    The kernel does the analytical work; the register shifts vocabulary.
    """

    PLAIN_ENGLISH = "plain_english"
    """Strip framework jargon (DAI / SDS / ROEM / Strategic Lasso /
    Set/Horus / Go/Chess) and re-express in plain everyday English while
    preserving the analytical structure (per-dimension breakdown + final
    resolution). Useful for non-framework-native operators + first-touch
    consumer-facing surfaces."""

    CUBE_OF_SPACE = "cube_of_space"
    """Visceral geometric vocabulary from the 2026-06-06 Frameworks
    Notebook exchange: gravity well, central intersection, North/South
    face, "actualizes the concept instead of avoiding it", inward-outward
    spirals. Same analytical kernel; spatial/geometric register."""

    EXECUTIVE_BRIEF = "executive_brief"
    """Tight 3-5 paragraph decision-maker summary. Bottom-line claim +
    mechanism + falsification risk + what-to-watch. Drops the
    per-dimension breakdown + framework vocabulary entirely."""


class Pathway(str, Enum):
    """The four pathways currently defined in ``docs/experiments/pathways/``.

    A Session picks one pathway at construction time. The pathway determines
    which prompt template the Engine receives at synthesis time. The
    underlying NotebookLM API and Engine notebook are the same across all
    pathways — only the framing differs.
    """

    CLEANROOM = "cleanroom"
    """Predictor silo. Falsifiable scenario, blind validation. Genie Prime
    framing applied to a question-shaped scenario. Powell, Tokenized Land,
    Musk-Altman runs all used this pathway."""

    GENIE = "genie"
    """Envisioner silo. Wish-fulfillment pathfinding. Genie Prime framing
    applied to a (current_state, wished_for_state) pair. Giant-Slayer run
    used this pathway."""

    OFFENSIVE = "offensive"
    """Envisioner silo, Architect-stance variant. Engine designs a strategic
    funnel against a target. Same code path as GENIE; differs only in the
    prompt framing (target + objective_state instead of current/wished)."""

    MIRROR_AUDIT = "mirror_audit"
    """Standalone Mirror Auditor invocation. The Session takes a Stroke-1
    output (provided as ``scenario.prior_resolution``) and routes it to the
    Mirror Auditor for fault enumeration. Used in the Amnesia validation
    run; also used as Stroke 2 in any iterative multi-stroke loop."""


# ---------------------------------------------------------------------------
# Scenario — what the consumer wants the Engine to reason about
# ---------------------------------------------------------------------------

class Scenario(BaseModel):
    """The user-facing description of what to analyze.

    Different pathways use different fields. CLEANROOM uses ``question``;
    GENIE uses ``current_state`` + ``wished_for_state``; OFFENSIVE uses
    ``target`` + ``objective_state``; MIRROR_AUDIT uses
    ``prior_resolution`` (the Stroke-1 text being audited).

    Validation is intentionally lax — the orchestrator picks the right
    field based on the chosen pathway. Empty unused fields are normal.
    """

    model_config = ConfigDict(extra="forbid")

    # Cleanroom-shape
    question: Optional[str] = None

    # Genie-shape
    current_state: Optional[str] = None
    wished_for_state: Optional[str] = None

    # Offensive-shape
    target: Optional[str] = None
    objective_state: Optional[str] = None

    # Mirror-audit-shape
    prior_resolution: Optional[str] = None
    """The Stroke-1 output text being audited. Required when pathway is
    MIRROR_AUDIT, ignored otherwise."""

    # Common framing controls
    dream_state: bool = True
    """Whether to apply the Genie Prime ('you are in a dream...') priming
    to the scenario before sending it to the Engine. Default True. The
    Mirror Auditor pathway ignores this flag — the auditor persona expects
    raw analysis text without dream framing."""

    extra_context: Optional[str] = None
    """Free-form additional context to include with the scenario. Useful
    for consumer-supplied background that doesn't fit any specific field."""


# ---------------------------------------------------------------------------
# TruthPacket — pre-harvested research finding
# ---------------------------------------------------------------------------

class TruthPacket(BaseModel):
    """A research finding the consumer wants to feed into the synthesis
    stage as if it had been harvested by a PKI Oracle.

    This is the path PrisonBreak (and similar consumers that already do
    their own document-grounded RAG) uses: the consumer's own RAG layer
    has already produced source-cited findings; rather than asking
    Ganymede to spin up new Oracles, the consumer ships the findings here
    and Ganymede synthesizes directly.

    Format mirrors the structure of an Oracle-produced Truth Packet so
    the Engine sees consistent input regardless of upstream source.
    """

    model_config = ConfigDict(extra="forbid")

    subject: str = Field(min_length=1)
    """Short label for what this packet is about. Will be rendered in the
    synthesis prompt as ``--- TRUTH PACKET: {subject} ---``."""

    content: str = Field(min_length=1)
    """The body of the finding, ideally hash-cited per the PKI Oracle
    persona convention but free-form is accepted. The orchestrator does
    not modify this text (Zero-Degradation rule)."""

    source_label: Optional[str] = None
    """Human-readable provenance. E.g. 'NotebookLM via PrisonBreak case
    7c91a3', 'Manual paste from analyst report', etc. Not sent to the
    Engine; for the consumer's own audit trail."""


# ---------------------------------------------------------------------------
# StrokeResult — output of one Engine fire
# ---------------------------------------------------------------------------

class StrokeResult(BaseModel):
    """Output of one Engine invocation within a Session.

    A single-pass run produces 1 StrokeResult. An Iterative Engine
    multi-stroke run produces N StrokeResults (typically 1=Thesis,
    2=Antithesis/audit, 3=Synthesis).

    The fields below are what we extract from the Engine response. Many
    are optional because not every stroke produces all of them — the
    audit stroke (Mirror Auditor) produces fault enumeration in
    ``audit_findings`` but no ``strategic_lasso`` or
    ``incomprehensible_move``.
    """

    model_config = ConfigDict(extra="forbid")

    stroke_number: int = Field(ge=1)
    pathway: Pathway
    raw_response: str
    """The Engine's complete unmodified response text. Source of truth;
    other fields below are extracted from this for convenience."""

    # Extracted from synthesis-style strokes (Cleanroom / Genie / Offensive)
    strategic_lasso: Optional[str] = None
    incomprehensible_move: Optional[str] = None
    final_resolution: Optional[str] = None

    # Extracted from audit-style strokes (Mirror Auditor)
    audit_findings: Optional[list[str]] = None
    """One entry per fault category the auditor enumerated. Order matches
    the auditor persona's category sequence: rigidity, pattern-matching,
    confidence-evidence-gaps, dimensional-greeds."""

    audit_kind: Optional[str] = None
    """Distinguishes audit-style strokes (``pathway=mirror_audit``) by which
    instance produced them. ``"mirror_auditor"`` for Mirror Auditor strokes,
    ``"bridge"`` for Connection Bridge strokes (Bicameral Convergence Level 1).
    None for non-audit strokes (cleanroom / genie / offensive synthesis).
    Lets UI consumers render Auditor and Bridge strokes distinctly without
    inspecting the stroke event payloads."""

    cleaned_response: Optional[str] = None
    """P1-03b CTA-suppression post-processor output. Populated only when
    the orchestrator's ``_strip_trailing_cta`` helper detected a trailing
    chatbot-CTA paragraph in ``raw_response`` and stripped it. UI consumers
    should display ``cleaned_response`` when present, falling back to
    ``raw_response`` otherwise — same display semantics as a pre-cleaning
    stroke. None when no CTA was found (most strokes — observed leak rate
    is ~33-43%). ``raw_response`` is left untouched in either case as the
    source of truth."""

    stripped_cta: Optional[str] = None
    """The actual CTA text that was stripped by ``_strip_trailing_cta``,
    preserved for forensic visibility + analysis of substrate behavior
    over time. None when no CTA was found. When set, it's the verbatim
    paragraph that was sliced from the trailing end of ``raw_response``."""

    # Metadata
    started_at: datetime
    completed_at: datetime

    @property
    def duration_seconds(self) -> float:
        return (self.completed_at - self.started_at).total_seconds()


# ---------------------------------------------------------------------------
# SessionEvent — emitted as the Session progresses
# ---------------------------------------------------------------------------

class SessionEventType(str, Enum):
    """The set of event types a Session emits over its lifecycle."""

    SESSION_CREATED = "session_created"
    STROKE_STARTED = "stroke_started"
    BLUEPRINT_READY = "blueprint_ready"
    """Fired when the Engine has produced its Architectural Blueprint and
    the orchestrator is about to start scaffolding Oracles. Payload:
    ``{ "blueprint": str }``."""

    ORACLE_REQUEST = "oracle_request"
    """Fired when the Session needs caller approval before creating a new
    Oracle. The Session pauses until the consumer POSTs an approval (or
    rejection) via the HTTP API. Payload: ``{ "subject": str,
    "surgical_prompt": str }``. Not used in the pre-harvested-packet path."""

    ORACLE_CREATED = "oracle_created"
    ORACLE_HARVESTED = "oracle_harvested"
    SYNTHESIS_COMPLETE = "synthesis_complete"
    """Fired when an Engine synthesis call has returned and a StrokeResult
    has been recorded. Payload: ``{ "stroke": StrokeResult }``."""

    STROKE_COMPLETED = "stroke_completed"

    # ---- Bicameral Convergence Level 2 events (E1-02 / E1-03) ----
    # Emitted by ``run_bicameral_loop`` to give operators visual transparency
    # into the closed-loop mirror-bounce. Per the architectural spec at
    # ``docs/concepts/Bicameral_Convergence.md``, visual transparency is one
    # of the five mandatory operator control surfaces — the operator needs
    # to be able to see iteration progress in real time to know when to
    # intervene (cancel, adjust delays, etc.).
    #
    # Each iteration emits START + END around its Engine + Bridge pair.
    # Terminal outcomes emit either CONVERGED (clean termination — no new
    # bridges surfaced or resolution stabilized) or HARD_CAP_REACHED
    # (hit the iteration cap without converging, partial result returned).

    BICAMERAL_ITERATION_START = "bicameral_iteration_start"
    """Fired at the top of each Bicameral loop iteration, before the
    Engine synthesis kicks off. Payload: ``{ "iteration": int,
    "max_iterations": int, "include_bridge": bool }``."""

    BICAMERAL_ITERATION_END = "bicameral_iteration_end"
    """Fired at the bottom of each Bicameral loop iteration, after the
    Bridge audit completes (or after the Engine synthesis if Bridge was
    skipped this iteration). Payload: ``{ "iteration": int,
    "engine_stroke_number": int, "bridge_stroke_number": Optional[int],
    "new_bridges_surfaced": Optional[int] }``."""

    BICAMERAL_CONVERGED = "bicameral_converged"
    """Terminal event for ``run_bicameral_loop``. Indicates the loop
    detected convergence (no new STRUCTURAL/IMPLIED bridges in the last
    iteration, or resolution text stabilized between iterations). The
    session is NOT auto-completed by this event — the caller drives
    ``/complete`` afterward to finalize. Payload:
    ``{ "iterations": int, "criterion": str }``
    where ``criterion`` is one of ``"no_new_structural"``,
    ``"resolution_stable"``."""

    BICAMERAL_HARD_CAP_REACHED = "bicameral_hard_cap_reached"
    """Terminal event for ``run_bicameral_loop``. Indicates the loop
    hit ``max_iterations`` without converging. The partial result is
    still returned; the operator may choose to re-run with a higher
    cap or accept the partial. Payload: ``{ "iterations": int,
    "max_iterations": int }``."""

    SESSION_COMPLETE = "session_complete"
    """Terminal event. Payload: ``{ "final_resolution": FinalResolution }``."""

    SESSION_CANCELLED = "session_cancelled"
    """Terminal event indicating the operator cancelled the session via
    ``POST /api/v2/sessions/{id}/cancel`` (E1-01, Bicameral Convergence
    Level 2 prerequisite). Payload: ``{ "message": str }`` (operator-
    facing reason). Distinct from ``ERROR`` — no failure occurred;
    operator chose to stop. Any partial strokes that completed before
    cancellation remain on the session and are accessible via
    ``session.strokes``."""

    ERROR = "error"
    """Terminal event indicating the Session failed. Payload:
    ``{ "message": str, "exc_type": str }``."""


class SessionEvent(BaseModel):
    """One event in a Session's timeline."""

    model_config = ConfigDict(extra="forbid")

    type: SessionEventType
    stroke_number: Optional[int] = None
    """Stroke this event belongs to, if any. ``SESSION_CREATED`` and
    ``SESSION_COMPLETE`` are session-level (None)."""

    payload: dict[str, Any] = Field(default_factory=dict)
    emitted_at: datetime


# ---------------------------------------------------------------------------
# FinalResolution — what the consumer ultimately receives
# ---------------------------------------------------------------------------

class FinalResolution(BaseModel):
    """The terminal artifact of a completed Session.

    Composed of all StrokeResults produced during the Session, in order,
    plus a convenience ``final_text`` field that points to the most
    informative resolution (typically the last synthesis stroke for
    iterative runs, or the only stroke for single-pass runs).
    """

    model_config = ConfigDict(extra="forbid")

    session_id: str
    pathway: Pathway
    iterative: bool
    strokes: list[StrokeResult]
    final_text: str
    """Convenience: the canonical 'this is the answer' text. For single-
    pass runs this is ``strokes[0].final_resolution`` (or
    ``strokes[0].raw_response`` if extraction failed). For iterative runs
    it's the last synthesis stroke's ``final_resolution``, with the audit
    stroke's findings considered intermediate."""

    started_at: datetime
    completed_at: datetime
    total_engine_calls: int
    """Cumulative count of NotebookLM API calls made across all strokes.
    Useful for the consumer's billing / quota tracking."""


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def new_session_id() -> str:
    """Generate a fresh UUIDv4 session ID."""
    return str(uuid.uuid4())


def utcnow() -> datetime:
    """Timezone-aware UTC now. Single source of truth for timestamps."""
    return datetime.now(timezone.utc)
