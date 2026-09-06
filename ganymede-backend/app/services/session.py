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
    - Session ownership serializes its operations across provider awaits.
      The provider runner owns and cleans up each invocation's process tree.

See :doc:`docs/integration/module_design.md` for the full API design.
"""

from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager
from datetime import datetime
from functools import wraps
from typing import TYPE_CHECKING, Any, Optional

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

if TYPE_CHECKING:
    from app.services.session_store import SessionStore

logger = logging.getLogger(__name__)


class SessionCancelledError(RuntimeError):
    """An owned operation stopped; partial analysis remains available."""

    def __init__(self, where: str, session_id: str):
        self.where = where
        self.session_id = session_id
        super().__init__(f"Session {session_id} cancelled at {where}")


def session_operation(*, allow_terminal: bool = False):
    """Reserve a session across provider awaits, including nested strokes."""
    def decorate(method):
        @wraps(method)
        async def owned(self, session, *args, **kwargs):
            async with session.operation(allow_terminal=allow_terminal):
                return await method(self, session, *args, **kwargs)
        return owned
    return decorate


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
        store: Optional["SessionStore"] = None,
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

        # Pl2-01 persistence binding — if non-None, mutations to terminal
        # transitions / stroke recording / translation recording also write
        # to disk so the session survives a backend restart. Default None
        # keeps the in-memory-only behavior for tests + cases where no
        # store is configured.
        self._store: Optional["SessionStore"] = store

        # Cancel flag — set by ``request_cancel()`` and observed by the
        # orchestrator loop at each provider-call await point. Atomic
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
        self._operation_task: Optional[asyncio.Task] = None
        self._operation_depth = 0
        self._operation_cancelled = False

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

    def check_running(self, where: str) -> None:
        if self.cancel_requested or self._operation_cancelled or self.status == "cancelled":
            raise SessionCancelledError(where, self.id)
        if self.status != "running":
            raise RuntimeError(f"Session {self.id} is {self.status}")

    def _check_owner(self) -> None:
        if self._operation_task is not None and self._operation_task is not asyncio.current_task():
            raise RuntimeError(f"Session {self.id} already has an active operation")

    @asynccontextmanager
    async def operation(self, *, allow_terminal: bool = False):
        task = asyncio.current_task()
        async with self._lock:
            self._check_owner()
            if not allow_terminal:
                self.check_running("operation-start")
            if self._operation_task is None:
                self._operation_task = task
                self._operation_cancelled = False
            self._operation_depth += 1
        try:
            yield
        except asyncio.CancelledError:
            if self._operation_cancelled or self.cancel_requested:
                raise SessionCancelledError("operation-stopped", self.id) from None
            # An interrupted HTTP owner must not leave a resumable-looking run.
            if self.status == "running":
                await self.request_cancel("Operation interrupted")
            raise
        finally:
            async with self._lock:
                self._operation_depth -= 1
                if self._operation_depth == 0 and self._operation_task is task:
                    self._operation_task = None

    async def start_operation(self, factory) -> asyncio.Task:
        """Reserve before returning 202, not when the scheduled driver wakes."""
        async with self._lock:
            self._check_owner()
            self.check_running("background-start")
            if self._operation_task is not None:
                raise RuntimeError(f"Session {self.id} already has an active operation")

            async def drive():
                async with self.operation():
                    return await factory()

            task = asyncio.create_task(drive(), name=f"ganymede-{self.id[:8]}")
            self._operation_task = task
            self._operation_cancelled = False
            # Cancellation before first scheduling never enters the context.
            def released(done):
                if self._operation_task is done:
                    self._operation_task = None
                if not done.cancelled():
                    done.exception()  # retrieve a background cancellation/error
            task.add_done_callback(released)
            return task

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

    async def _persist(self) -> None:
        """Pl2-01: write current state to the bound SessionStore.

        Called from inside ``self._lock`` by all the mutating methods
        (record_stroke, record_translation, complete, fail,
        request_cancel) after their state changes have landed. No-op
        if no store is bound (the in-memory-only case).

        Persistence failures log but do NOT raise — a disk-write hiccup
        should not kill an in-progress run. The next mutation's persist
        will catch up if the underlying issue clears.

        The blocking SQLite write happens on a worker thread via
        ``asyncio.to_thread`` so the event loop stays responsive even
        if the disk is slow.
        """
        if self._store is None:
            return
        try:
            await asyncio.to_thread(self._store.save_session, self)
        except Exception as exc:
            logger.error("Session %s persist failed: %s", self.id, exc)

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
            self._check_owner()
            self.check_running("record-stroke")
            expected = len(self._strokes) + 1
            if stroke.stroke_number != expected:
                raise ValueError(
                    f"Session {self.id}: stroke {stroke.stroke_number} "
                    f"recorded out of order (expected {expected})"
                )
            self._strokes.append(stroke)
            await self._persist()

    async def complete(self) -> FinalResolution:
        """Mark the session complete and return the FinalResolution.

        Idempotent: calling twice returns the same FinalResolution and
        does not re-emit the SESSION_COMPLETE event.
        """
        async with self._lock:
            if self._final is not None:
                return self._final
            self._check_owner()
            self.check_running("complete")
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
            await self._persist()
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
            await self._persist()

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
            task = self._operation_task
            if self.status != "running" and (task is None or self._operation_cancelled):
                return False
            self._operation_cancelled = True
            if self.status == "running":
                self.cancel_requested = True
                self.status = "cancelled"
                self.completed_at = utcnow()
                self._emit_locked(
                    SessionEventType.SESSION_CANCELLED,
                    payload={"message": message},
                    stroke_number=None,
                )
                await self._persist()
            # A post-completion translation can stop without rewriting analysis.
            if task is not None and task is not asyncio.current_task():
                task.cancel()
        if task is not None and task is not asyncio.current_task():
            await asyncio.gather(task, return_exceptions=True)
        logger.info("Session %s operation cancelled: %s", self.id, message)
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
            self._check_owner()
            if self._operation_cancelled:
                raise SessionCancelledError("record-translation", self.id)
            self._translations[key] = translated_text
            await self._persist()

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

    # -------------------------------------------- Pl2-01 rehydration factory

    @classmethod
    def from_persisted_state(
        cls,
        data: dict[str, Any],
        store: Optional["SessionStore"] = None,
    ) -> "Session":
        """Rehydrate a Session from a ``SessionStore.load_all()`` row dict.

        Bypasses ``__init__``'s ``SESSION_CREATED`` event emit — the
        persisted events list already contains the original event from
        when the session was first created. Calling ``__init__`` here
        would append a duplicate.

        The reconstituted session is bound to ``store`` so subsequent
        mutations continue to persist. ``_lock`` and ``_subscribers``
        are fresh (process-local; not persisted).
        """
        instance = cls.__new__(cls)
        instance.id = data["id"]
        instance.scenario = Scenario.model_validate_json(data["scenario_json"])
        instance.pathway = Pathway(data["pathway"])
        instance.iterative = bool(data["iterative"])
        instance.max_strokes = int(data["max_strokes"])
        instance.status = data["status"]
        instance.error_message = data["error_message"]
        instance.created_at = datetime.fromisoformat(data["created_at"])
        instance.completed_at = (
            datetime.fromisoformat(data["completed_at"])
            if data["completed_at"]
            else None
        )
        instance.cancel_requested = instance.status == "cancelled"
        instance._operation_task = None
        instance._operation_depth = 0
        instance._operation_cancelled = False
        instance._events = [
            SessionEvent.model_validate(e) for e in data.get("events", [])
        ]
        instance._strokes = [
            StrokeResult.model_validate(s) for s in data.get("strokes", [])
        ]
        instance._translations = dict(data.get("translations", {}))
        instance._final = None
        if instance.status == "complete" and instance._strokes:
            final_text = data.get("final_text")
            if final_text is None:
                final_text = instance._derive_final_text()
            instance._final = FinalResolution(
                session_id=instance.id,
                pathway=instance.pathway,
                iterative=instance.iterative,
                strokes=list(instance._strokes),
                final_text=final_text,
                started_at=instance.created_at,
                completed_at=instance.completed_at or instance.created_at,
                total_engine_calls=len(instance._strokes),
            )
        instance._lock = asyncio.Lock()
        instance._subscribers = []
        instance._store = store
        return instance

    # --------------------------------------------------------------- internal

    def _derive_final_text(self) -> str:
        """Pick the canonical 'this is the answer' text from the strokes.

        Synthesis sessions use the latest synthesis, not a following critique.
        All strokes remain available in the final artifact.

        Audit-only sessions (MIRROR_AUDIT pathway, no synthesis stroke)
        return the audit stroke's ``raw_response`` since there's no
        ``final_resolution`` field.
        """
        eligible = self._strokes if self.pathway is Pathway.MIRROR_AUDIT else [
            stroke for stroke in self._strokes
            if stroke.pathway is not Pathway.MIRROR_AUDIT and not stroke.audit_kind
        ]
        if not eligible:
            raise RuntimeError(f"Session {self.id}: no synthesis is available to finalize")
        last = eligible[-1]
        return last.final_resolution or last.raw_response


# ---------------------------------------------------------------------------
# SessionRegistry
# ---------------------------------------------------------------------------

class SessionRegistry:
    """Registry of Sessions, optionally backed by persistent storage.

    Single-process registry of in-memory ``Session`` objects. When a
    ``SessionStore`` is bound (via the constructor or :meth:`bind_store`),
    every session created through :meth:`create` is also persisted to
    disk, and prior sessions can be rehydrated via :meth:`rehydrate`.

    With no store bound, the registry behaves as it always has — purely
    in-memory, ephemeral across process restarts. Tests can construct a
    fresh ``SessionRegistry()`` without a store.
    """

    def __init__(self, store: Optional["SessionStore"] = None):
        self._sessions: dict[str, Session] = {}
        self._lock = asyncio.Lock()
        self._store: Optional["SessionStore"] = store

    @property
    def store(self) -> Optional["SessionStore"]:
        """The bound SessionStore, or None for in-memory-only mode.

        Exposed so the API layer can query persisted-session lists/search
        without re-implementing those at the registry level — the store
        already owns that surface (``list_summaries``, ``search``,
        ``count``).
        """
        return self._store

    def bind_store(self, store: "SessionStore") -> None:
        """Attach a SessionStore to this registry. Used by ``main.py``'s
        startup hook so the module-global registry created at import time
        can be paired with the store that's created when env vars are
        available. Sessions created AFTER this call are persisted; those
        already in the registry (only relevant in tests) are not
        retroactively bound."""
        self._store = store

    async def rehydrate(self) -> int:
        """Rehydrate prior sessions from the bound store into the
        in-memory registry. Returns the count rehydrated.

        Idempotent in the sense that a session ID already in the
        in-memory registry is skipped — but normally this is called once
        at startup before any session creation, so collisions don't
        happen in practice.

        Before loading, marks any session left in ``running`` status on
        disk as ``error`` (the orchestrator that owned it died with the
        process; the loop can't resume). Returns the total count
        rehydrated into memory.
        """
        if self._store is None:
            return 0
        rescued = await asyncio.to_thread(
            self._store.mark_orphan_running_as_error,
            "Backend restarted during run; partial state preserved.",
        )
        if rescued:
            logger.warning(
                "SessionRegistry: rescued %d orphan running session(s) on startup",
                len(rescued),
            )
        rows = await asyncio.to_thread(self._store.load_all)
        added = 0
        async with self._lock:
            for row in rows:
                sid = row["id"]
                if sid in self._sessions:
                    continue
                try:
                    self._sessions[sid] = Session.from_persisted_state(
                        row, store=self._store
                    )
                    added += 1
                except Exception as exc:
                    logger.error(
                        "SessionRegistry: skipping malformed persisted "
                        "session %s: %s",
                        sid, exc,
                    )
        logger.info("SessionRegistry: rehydrated %d session(s) from store", added)
        return added

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

        If a store is bound, the new session is immediately persisted so
        a crash before the first stroke still leaves a recoverable row
        on disk.
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
                store=self._store,
            )
            self._sessions[session.id] = session
            logger.info(
                "Session created: %s pathway=%s iterative=%s max_strokes=%d",
                session.id, pathway.value, iterative, max_strokes,
            )

        # Persist the freshly-created session OUTSIDE the registry lock —
        # no other coroutine has a reference to it yet, so there's no
        # in-flight mutation to race with. Inside the registry lock would
        # also be safe, but we'd be holding the registry lock during a
        # disk write, which we'd like to avoid.
        await session._persist()
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
        """Remove a session from the registry. Returns True if removed.

        Also deletes the session from the bound store if present, so
        discarding actually frees the persistent row, not just the
        in-memory entry.
        """
        async with self._lock:
            removed = self._sessions.pop(session_id, None) is not None
        if removed and self._store is not None:
            try:
                await asyncio.to_thread(self._store.delete, session_id)
            except Exception as exc:
                logger.error(
                    "SessionRegistry: store delete failed for %s: %s",
                    session_id, exc,
                )
        return removed


# Module-global registry. Single instance per process — same pattern as
# the cooldown gate. Tests that need an isolated registry should
# instantiate ``SessionRegistry()`` directly.
_REGISTRY = SessionRegistry()


def registry() -> SessionRegistry:
    """Accessor for the module-global registry. Use this rather than
    importing ``_REGISTRY`` directly so the global is encapsulated."""
    return _REGISTRY
