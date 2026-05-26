"""Background task registry for long-running NotebookLM operations.

Studio output generation and Deep Research can take 5-30 minutes per call.
HTTP requests can't reasonably block for that long, so the v2 endpoints
spawn an ``asyncio.Task`` per operation and return a ``task_id`` the
consumer polls.

Same in-memory, single-process design as :class:`~app.services.session.SessionRegistry`
— persistence is a consumer-side concern. If the backend restarts mid-task,
the consumer should treat the task as failed and re-start.

The wrappers (:meth:`NotebookLMService.generate_audio_overview`, etc.) are
already cooldown-gated, so a burst of task starts will serialize at the
NotebookLM call layer regardless.
"""

from __future__ import annotations

import asyncio
import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Awaitable, Callable, Optional

logger = logging.getLogger(__name__)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class BackgroundTask:
    """One in-progress Studio or Research operation.

    Lifecycle states (``status``):
        ``running``    — asyncio.Task is in flight
        ``completed``  — task finished cleanly; ``result`` is set
        ``error``      — task raised; ``error_message`` and ``exc_type`` set

    The underlying ``asyncio.Task`` is held in ``_task`` so callers can
    optionally ``cancel()`` it through the registry.
    """

    def __init__(self, kind: str, notebook_id: Optional[str], context: dict[str, Any]):
        self.id: str = uuid.uuid4().hex
        self.kind: str = kind  # "audio" | "video" | "infographic" | "research"
        self.notebook_id: Optional[str] = notebook_id
        self.context: dict[str, Any] = context  # original request payload, for debugging

        self.status: str = "running"
        self.result: Optional[dict[str, Any]] = None
        self.error_message: Optional[str] = None
        self.exc_type: Optional[str] = None

        self.created_at: str = _now_iso()
        self.completed_at: Optional[str] = None

        self._task: Optional[asyncio.Task] = None

    def attach(self, task: asyncio.Task) -> None:
        """Attach the asyncio.Task this BackgroundTask wraps."""
        self._task = task

    def cancel(self) -> bool:
        """Cancel the in-flight asyncio.Task. Returns True if a cancel was issued.

        The task transitions to ``error`` with ``exc_type='CancelledError'``
        once the cancellation propagates. Returns False if the task has
        already completed.
        """
        if self._task is None or self._task.done():
            return False
        self._task.cancel()
        return True

    def to_dict(self) -> dict[str, Any]:
        """JSON-serializable snapshot, suitable for HTTP responses."""
        return {
            "task_id": self.id,
            "kind": self.kind,
            "notebook_id": self.notebook_id,
            "status": self.status,
            "result": self.result,
            "error_message": self.error_message,
            "exc_type": self.exc_type,
            "created_at": self.created_at,
            "completed_at": self.completed_at,
        }


class BackgroundTaskRegistry:
    """In-memory registry of BackgroundTasks. Process-global singleton.

    Same shape as :class:`~app.services.session.SessionRegistry`.
    """

    def __init__(self):
        self._tasks: dict[str, BackgroundTask] = {}
        self._lock = asyncio.Lock()

    async def submit(
        self,
        kind: str,
        coro_factory: Callable[[], Awaitable[dict[str, Any]]],
        notebook_id: Optional[str] = None,
        context: Optional[dict[str, Any]] = None,
    ) -> BackgroundTask:
        """Register a new task and start its asyncio.Task.

        ``coro_factory`` is a zero-arg callable that returns the coroutine
        to run. We construct the coroutine inside this method (not before)
        so that if registration fails, no orphan coroutine is leaked.

        The wrapped coroutine's return value is stored as ``task.result``.
        Any exception is captured into ``task.error_message`` and
        ``task.exc_type``; the task transitions to ``error`` state.

        Returns the BackgroundTask immediately — caller polls
        :meth:`get` for status.
        """
        task_obj = BackgroundTask(
            kind=kind,
            notebook_id=notebook_id,
            context=context or {},
        )
        async with self._lock:
            self._tasks[task_obj.id] = task_obj

        async def _runner():
            try:
                result = await coro_factory()
            except asyncio.CancelledError:
                task_obj.status = "error"
                task_obj.exc_type = "CancelledError"
                task_obj.error_message = "Task was cancelled"
                task_obj.completed_at = _now_iso()
                logger.info("Task %s (%s) cancelled", task_obj.id, kind)
                raise
            except Exception as exc:
                task_obj.status = "error"
                task_obj.exc_type = type(exc).__name__
                task_obj.error_message = str(exc)
                task_obj.completed_at = _now_iso()
                logger.exception(
                    "Task %s (%s) failed: %s", task_obj.id, kind, exc,
                )
            else:
                task_obj.status = "completed"
                task_obj.result = result
                task_obj.completed_at = _now_iso()
                logger.info("Task %s (%s) completed", task_obj.id, kind)

        aio_task = asyncio.create_task(_runner(), name=f"bg-{kind}-{task_obj.id[:8]}")
        task_obj.attach(aio_task)
        logger.info(
            "Task %s submitted (kind=%s, notebook=%s)",
            task_obj.id, kind, notebook_id,
        )
        return task_obj

    def get(self, task_id: str) -> Optional[BackgroundTask]:
        return self._tasks.get(task_id)

    def list_active(self) -> list[BackgroundTask]:
        return [t for t in self._tasks.values() if t.status == "running"]

    def list_all(self) -> list[BackgroundTask]:
        return list(self._tasks.values())

    async def cancel(self, task_id: str) -> bool:
        """Cancel a task by ID. Returns False if not found or already done."""
        task = self._tasks.get(task_id)
        if task is None:
            return False
        return task.cancel()


# Module-global registry. Single instance per process.
_REGISTRY = BackgroundTaskRegistry()


def registry() -> BackgroundTaskRegistry:
    """Accessor for the module-global registry."""
    return _REGISTRY
