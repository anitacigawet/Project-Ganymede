"""Session abstraction.

Holds in-memory state for one in-progress Engine run. A consumer creates
a Session via :class:`SessionRegistry`, the orchestrator drives it through
phases (recording StrokeResults and emitting SessionEvents), and the
consumer eventually retrieves the :class:`FinalResolution`.

Design notes:
    - Sessions are single-process, in-memory. Persistence is a Phase-3+
      concern; the registry interface is built so persistence can be
      bolted on later without changing call sites.
    - Each Session owns a list of :class:`SessionEvent`. In Phase 4 this
      list will be backed by an ``asyncio.Queue`` for WebSocket
      streaming, but for now consumers retrieve events by polling
      :meth:`Session.events`.
    - The cooldown gate (``_GATE`` in ``app.services.notebooklm.cooldown``)
      handles all NotebookLM rate limiting transparently. The Session does
      not need to think about it.

See :doc:`docs/integration/module_design.md` for the full API design.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Optional

from app.contracts import (
    FinalResolution,
    Pathway,
    Scenario,
    SessionEvent,
    SessionEventType,
    StrokeResult,
    new_session_id,
    utcnow,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Session
# ---------------------------------------------------------------------------

class Session:
    """One in-progress Engine run.

    Constructed via :meth:`SessionRegistry.create`. Mutated by the
    orchestrator through :meth:`emit`, :meth:`record_stroke`, and the
    completion methods. Read by consumers via the property accessors and
    :meth:`events`.

    Lifecycle states (``status``):
        ``running``    — created; strokes may still be added
        ``complete``   — :meth:`complete` was called; final resolution is set
        ``error``      — :meth:`fail` was called; ``error_message`` is set
        ``cancelled``  — :meth:`request_cancel` was called by the operator;
                         any in-flight orchestrator loop terminates at its
                         next check point. Partial strokes are preserved.
    """

    def __init__(
        self,
        scenario: Scenario,
        pathway: Pathway,
        iterative: bool,
        max_strokes: int,
    ):
        self.id: str = new_session_id()
        self.scenario: Scenario = scenario
        self.pathway: Pathway = pathway
        self.iterative: bool = iterative
        self.max_strokes: int = max_strokes

        self.status: str = "running"
        self.error_message: Optional[str] = None
        self.created_at = utcnow()
        self.completed_at: Optional[Any] = None  # set on terminal transition

        # Cancel flag — set by ``request_cancel()`` and observed by the
        # orchestrator loop at each NotebookLM-call await point. Atomic
        # reads (bool, GIL-protected) so the orchestrator can check
        # without locking. Writes go through ``request_cancel()`` which
        # acquires ``self._lock`` for the state transition.
        self.cancel_requested: bool = False

        self._events: list[SessionEvent] = []
        self._strokes: list[StrokeResult] = []
        self._final: Optional[FinalResolution] = None
        # Pl3 Operator Lens — translations of strokes into operator-facing
        # registers. Keyed by ``f"{stroke_number}:{register}"`` so the same
        # stroke can be translated into multiple registers without
        # collision. Set via ``record_translation``; read via
        # ``get_translation`` / ``translations``.
        self._translations: dict[str, str] = {}

        # Lock to serialize state mutations from concurrent orchestrator
        # tasks. Reads (e.g. ``events``, ``strokes``) are not locked —
        # they return snapshots.
        self._lock = asyncio.Lock()

        # Subscriber queues for live event streaming (WebSocket consumers
        # added in Phase 4). Each subscriber receives every event the
        # session emits, including the SESSION_CREATED below since
        # subscribe() drains history first.
        self._subscribers: list[asyncio.Queue[SessionEvent]] = []

        # Emit the create event synchronously at construction time. We
        # deliberately don't await here — the constructor is sync.
        self._events.append(
            SessionEvent(
                type=SessionEventType.SESSION_CREATED,
                stroke_number=None,
                payload={
                    "session_id": self.id,
                    "pathway": self.pathway.value,
                    "iterative": self.iterative,
                    "max_strokes": self.max_strokes,
                },
                emitted_at=self.created_at,
            )
        )

    # --------------------------------------------------------------- mutators

    def _emit_locked(
        self,
        event_type: SessionEventType,
        payload: Optional[dict[str, Any]] = None,
        stroke_number: Optional[int] = None,
    ) -> SessionEvent:
        """Append an event + notify subscribers, assuming the lock is already held.

        Internal helper. Public callers use :meth:`emit`. Other Session
        methods (:meth:`complete`, :meth:`fail`) use this when they're
        already inside ``async with self._lock`` to avoid deadlocking on
        re-acquisition.
        """
        event = SessionEvent(
            type=event_type,
            stroke_number=stroke_number,
            payload=payload or {},
            emitted_at=utcnow(),
        )
        self._events.append(event)
        logger.debug(
            "Session %s emit %s (stroke=%s)",
            self.id, event_type.value, stroke_number,
        )
        # Notify live subscribers. ``put_nowait`` because subscriber
        # queues are unbounded; if a subscriber's loop is too slow to
        # drain, that's a subscriber-side bug, not something the
        # emitter should block on.
        for q in self._subscribers:
            q.put_nowait(event)
        return event

    async def emit(
        self,
        event_type: SessionEventType,
        payload: Optional[dict[str, Any]] = None,
        stroke_number: Optional[int] = None,
    ) -> SessionEvent:
        """Append a new event to the session timeline and notify subscribers.

        Returns the appended event so callers can log it or correlate.
        """
        async with self._lock:
            return self._emit_locked(event_type, payload, stroke_number)

    async def record_stroke(self, stroke: StrokeResult) -> None:
        """Record a completed StrokeResult on the session.

        Validates that the stroke number is sequential. The orchestrator
        is expected to call :meth:`emit` with ``STROKE_COMPLETED``
        immediately after this.
        """
        async with self._lock:
            expected = len(self._strokes) + 1
            if stroke.stroke_number != expected:
                raise ValueError(
                    f"Session {self.id}: stroke {stroke.stroke_number} "
                    f"recorded out of order (expected {expected})"
                )
            self._strokes.append(stroke)

    async def complete(self) -> FinalResolution:
        """Mark the session complete and return the FinalResolution.

        Idempotent: calling twice returns the same FinalResolution and
        does not re-emit the SESSION_COMPLETE event.
        """
        async with self._lock:
            if self._final is not None:
                return self._final
            if not self._strokes:
                raise RuntimeError(
                    f"Session {self.id}: cannot complete with no strokes"
                )

            now = utcnow()
            final_text = self._derive_final_text()
            self._final = FinalResolution(
                session_id=self.id,
                pathway=self.pathway,
                iterative=self.iterative,
                strokes=list(self._strokes),  # snapshot
                final_text=final_text,
                started_at=self.created_at,
                completed_at=now,
                total_engine_calls=len(self._strokes),
            )
            self.status = "complete"
            self.completed_at = now
            self._emit_locked(
                SessionEventType.SESSION_COMPLETE,
                payload={"final_text_len": len(final_text)},
                stroke_number=None,
            )
            return self._final

    async def fail(self, message: str, exc_type: str = "Exception") -> None:
        """Mark the session failed. Terminal."""
        async with self._lock:
            if self.status != "running":
                return  # idempotent
            self.status = "error"
            self.error_message = message
            self.completed_at = utcnow()
            self._emit_locked(
                SessionEventType.ERROR,
                payload={"message": message, "exc_type": exc_type},
                stroke_number=None,
            )

    async def request_cancel(self, message: str = "Cancelled by operator") -> bool:
        """Request cancellation of the session. Terminal.

        Atomically:
            1. Sets ``cancel_requested = True`` (so the in-flight loop's
               next check point observes it and raises
               ``SessionCancelledError``).
            2. Transitions ``status`` to ``"cancelled"``.
            3. Sets ``completed_at`` to now.
            4. Emits ``SESSION_CANCELLED`` so live subscribers see the
               terminal state immediately.

        Idempotent: calling on an already-terminal session returns False
        without re-emitting. Returns True iff this call transitioned the
        session.

        Any partial strokes recorded before this call remain on the session
        and are accessible via ``self.strokes``. Callers that ran a loop
        which terminated due to cancellation typically return those partial
        strokes to the HTTP consumer so they can see what work landed.
        """
        async with self._lock:
            if self.status != "running":
                return False  # idempotent: already complete/error/cancelled
            self.cancel_requested = True
            self.status = "cancelled"
            self.completed_at = utcnow()
            self._emit_locked(
                SessionEventType.SESSION_CANCELLED,
                payload={"message": message},
                stroke_number=None,
            )
            logger.info("Session %s cancelled by operator: %s", self.id, message)
            return True

    # ---------------------------------------------------------------- readers

    @property
    def events(self) -> list[SessionEvent]:
        """Snapshot of events emitted so far. Returns a copy."""
        return list(self._events)

    # -------------------------------------------------- subscriber lifecycle

    async def subscribe(self) -> asyncio.Queue[SessionEvent]:
        """Register a new event subscriber and return its queue.

        The queue is pre-populated with all events the session has emitted
        so far (chronological order), then receives every subsequent
        event in real time as it's emitted.

        The caller is responsible for invoking :meth:`unsubscribe` when
        done — typically in a ``finally`` block of a WebSocket handler.
        Never abandon a subscriber; an abandoned subscriber accumulates
        events indefinitely and leaks memory.
        """
        q: asyncio.Queue[SessionEvent] = asyncio.Queue()
        async with self._lock:
            for event in self._events:
                q.put_nowait(event)
            self._subscribers.append(q)
        logger.debug("Session %s: subscriber registered (now %d active)",
                     self.id, len(self._subscribers))
        return q

    async def unsubscribe(self, q: asyncio.Queue[SessionEvent]) -> None:
        """Remove a previously-registered subscriber. Idempotent."""
        async with self._lock:
            try:
                self._subscribers.remove(q)
                logger.debug("Session %s: subscriber removed (now %d active)",
                             self.id, len(self._subscribers))
            except ValueError:
                pass  # already removed

    @property
    def subscriber_count(self) -> int:
        """How many live subscribers are currently attached. For ops/tests."""
        return len(self._subscribers)

    @property
    def strokes(self) -> list[StrokeResult]:
        """Snapshot of strokes recorded so far. Returns a copy."""
        return list(self._strokes)

    # ------------------------------------------- Pl3 Operator Lens translations

    async def record_translation(
        self,
        stroke_number: int,
        register: str,
        translated_text: str,
    ) -> None:
        """Record a translation of ``stroke_number`` into ``register``.

        Overwrites any prior translation for the same (stroke, register)
        pair — re-translating is allowed and produces the latest result.
        """
        key = f"{stroke_number}:{register}"
        async with self._lock:
            self._translations[key] = translated_text

    def get_translation(
        self,
        stroke_number: int,
        register: str,
    ) -> Optional[str]:
        """Return the translation of ``stroke_number`` in ``register``, or None."""
        return self._translations.get(f"{stroke_number}:{register}")

    @property
    def translations(self) -> dict[str, str]:
        """Snapshot of all recorded translations. Keyed by
        ``f"{stroke_number}:{register}"``. Returns a copy."""
        return dict(self._translations)

    @property
    def final(self) -> Optional[FinalResolution]:
        """The FinalResolution if the session has completed, else None."""
        return self._final

    # --------------------------------------------------------------- internal

    def _derive_final_text(self) -> str:
        """Pick the canonical 'this is the answer' text from the strokes.

        Heuristic:
            - If iterative: the last stroke's ``final_resolution``
              (falling back to ``raw_response`` if extraction was empty).
            - Otherwise: the first (and only) stroke's ``final_resolution``
              (falling back to ``raw_response``).

        Audit-only sessions (MIRROR_AUDIT pathway, no synthesis stroke)
        return the audit stroke's ``raw_response`` since there's no
        ``final_resolution`` field.
        """
        last = self._strokes[-1]
        return last.final_resolution or last.raw_response


# ---------------------------------------------------------------------------
# SessionRegistry
# ---------------------------------------------------------------------------

class SessionRegistry:
    """In-memory registry of active Sessions.

    Single-process, no persistence. Phase-3+ work will swap this for a
    persistence-backed implementation; the interface is what callers
    rely on.
    """

    def __init__(self):
        self._sessions: dict[str, Session] = {}
        self._lock = asyncio.Lock()

    async def create(
        self,
        scenario: Scenario,
        pathway: Pathway,
        iterative: bool = False,
        max_strokes: int = 1,
    ) -> Session:
        """Create a new Session and register it.

        ``max_strokes`` defaults to 1 (single-pass). For iterative runs,
        callers typically pass ``iterative=True, max_strokes=3``
        (Stroke 1 thesis + Stroke 2 audit + Stroke 3 synthesis).
        """
        if iterative and max_strokes < 2:
            raise ValueError("Iterative sessions need max_strokes >= 2")
        if max_strokes < 1:
            raise ValueError("max_strokes must be >= 1")

        async with self._lock:
            session = Session(
                scenario=scenario,
                pathway=pathway,
                iterative=iterative,
                max_strokes=max_strokes,
            )
            self._sessions[session.id] = session
            logger.info(
                "Session created: %s pathway=%s iterative=%s max_strokes=%d",
                session.id, pathway.value, iterative, max_strokes,
            )
            return session

    def get(self, session_id: str) -> Optional[Session]:
        """Return the session with the given ID, or None."""
        return self._sessions.get(session_id)

    def list_active(self) -> list[Session]:
        """Snapshot of currently-running sessions."""
        return [s for s in self._sessions.values() if s.status == "running"]

    def list_all(self) -> list[Session]:
        """Snapshot of all sessions in the registry (active + terminal)."""
        return list(self._sessions.values())

    async def discard(self, session_id: str) -> bool:
        """Remove a session from the registry. Returns True if removed."""
        async with self._lock:
            return self._sessions.pop(session_id, None) is not None


# Module-global registry. Single instance per process — same pattern as
# the cooldown gate. Tests that need an isolated registry should
# instantiate ``SessionRegistry()`` directly.
_REGISTRY = SessionRegistry()


def registry() -> SessionRegistry:
    """Accessor for the module-global registry. Use this rather than
    importing ``_REGISTRY`` directly so the global is encapsulated."""
    return _REGISTRY
