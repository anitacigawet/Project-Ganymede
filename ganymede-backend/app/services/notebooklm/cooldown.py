"""Cooldown gate for all NotebookLM API calls.

The unofficial NotebookLM API has invisible safety triggers. The gate is what
keeps us from finding them. Pattern adapted from the Z-SPAN bridge; see
``docs/protocols/Account_Safety.md`` for the rationale and tunable env vars.

Single module-global ``_GATE`` instance shared across the process. Every
method in :class:`~app.services.notebooklm.client.NotebookLMService` that
invokes ``self.client.X`` calls ``await _GATE.acquire()`` immediately before
the call. Studio and Deep Research mixins do the same.

Tunable env vars (all documented in ``docs/protocols/Account_Safety.md``):
    GANYMEDE_NOTEBOOKLM_COOLDOWN          — per-call floor (default 8s)
    GANYMEDE_NOTEBOOKLM_SESSION_COOLDOWN  — inter-session floor (default 60s)
    GANYMEDE_NOTEBOOKLM_HOURLY_CAP        — soft hourly cap (default 20)
    GANYMEDE_NOTEBOOKLM_DAILY_CAP         — soft daily cap (default 100)
"""

from __future__ import annotations

import asyncio
import logging
import os
import time
from collections import deque

logger = logging.getLogger(__name__)


_API_COOLDOWN_SEC = float(os.getenv("GANYMEDE_NOTEBOOKLM_COOLDOWN", "8"))
_SESSION_COOLDOWN_SEC = float(os.getenv("GANYMEDE_NOTEBOOKLM_SESSION_COOLDOWN", "60"))
_HOURLY_SOFT_CAP = int(os.getenv("GANYMEDE_NOTEBOOKLM_HOURLY_CAP", "20"))
_DAILY_SOFT_CAP = int(os.getenv("GANYMEDE_NOTEBOOKLM_DAILY_CAP", "100"))


class _CooldownGate:
    """Single global gate enforcing minimum spacing between NotebookLM API calls.

    Async-safe. All API methods call :meth:`acquire` immediately before any
    ``self.client.X`` invocation.
    """

    def __init__(self):
        self._lock = asyncio.Lock()
        self._last_call_at: float = 0.0  # monotonic
        # Wall-clock timestamps of recent calls, kept for soft-cap warnings.
        self._recent: deque[float] = deque()
        # Mark of the start of the current session, for inter-session cooldown
        # checks. None means "no session in progress."
        self._session_started_at: float | None = None

    async def acquire(self):
        """Block until it's safe to make the next NotebookLM API call.

        Enforces the per-call cooldown (hard floor) and emits warnings if
        soft caps are being approached.
        """
        async with self._lock:
            now = time.monotonic()
            elapsed = now - self._last_call_at
            if self._last_call_at > 0 and elapsed < _API_COOLDOWN_SEC:
                wait = _API_COOLDOWN_SEC - elapsed
                logger.info(
                    "NotebookLM cooldown: waiting %.1fs before next call",
                    wait,
                )
                await asyncio.sleep(wait)

            # Soft-cap warnings (advisory, never blocking)
            self._prune_old_calls()
            now_wall = time.time()
            in_last_hour = sum(1 for t in self._recent if t > now_wall - 3600)
            if in_last_hour >= _HOURLY_SOFT_CAP:
                logger.warning(
                    "NotebookLM hourly soft cap reached: %d calls in last hour "
                    "(cap %d). Continuing but consider stopping the session.",
                    in_last_hour, _HOURLY_SOFT_CAP,
                )
            in_last_day = sum(1 for t in self._recent if t > now_wall - 86400)
            if in_last_day >= _DAILY_SOFT_CAP:
                logger.warning(
                    "NotebookLM daily soft cap reached: %d calls in last 24h "
                    "(cap %d). Strongly consider stopping for the day.",
                    in_last_day, _DAILY_SOFT_CAP,
                )

            self._last_call_at = time.monotonic()
            self._recent.append(now_wall)

    async def mark_session_boundary(self):
        """Wait the inter-session cooldown before the next call.

        Call this between distinct experimental runs (e.g. between a Powell
        run and a Tokenized Land run, or between a Mirror Validation audit
        and an unrelated Cleanroom run). Within a single multi-step
        workflow (Triage → Oracles → Synthesis), do NOT call this — the
        per-call cooldown is sufficient.

        Idempotent: calling it twice in a row only waits once.
        """
        async with self._lock:
            now = time.monotonic()
            if self._session_started_at is None:
                self._session_started_at = now
                return
            elapsed = now - self._session_started_at
            if elapsed < _SESSION_COOLDOWN_SEC:
                wait = _SESSION_COOLDOWN_SEC - elapsed
                logger.info(
                    "NotebookLM session boundary: waiting %.1fs before next session",
                    wait,
                )
                await asyncio.sleep(wait)
            self._session_started_at = time.monotonic()

    def _prune_old_calls(self):
        cutoff = time.time() - 86400  # keep last 24h
        while self._recent and self._recent[0] < cutoff:
            self._recent.popleft()

    def stats(self) -> dict:
        """Snapshot of cooldown gate state, for ops/observability."""
        self._prune_old_calls()
        now_wall = time.time()
        return {
            "calls_last_hour": sum(1 for t in self._recent if t > now_wall - 3600),
            "calls_last_24h": len(self._recent),
            "hourly_cap": _HOURLY_SOFT_CAP,
            "daily_cap": _DAILY_SOFT_CAP,
            "api_cooldown_sec": _API_COOLDOWN_SEC,
            "session_cooldown_sec": _SESSION_COOLDOWN_SEC,
        }


# Module-global gate. Single instance shared across all NotebookLMService
# instances within the process — accidental concurrent instances (e.g. tests
# vs main app) would otherwise each run their own cooldown clock, defeating
# the purpose. One process, one gate.
_GATE = _CooldownGate()
