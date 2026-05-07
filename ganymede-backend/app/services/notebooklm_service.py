"""NotebookLM client wrapper.

Exposes the canonical 9D Chess Engine and the Mirror Auditor (a second
9D-Chess instance with the same source corpus, configured for fault-finding
rather than strategic generation) as named, read-only methods.

Hard guardrails (also documented in ``docs/OVERVIEW.md``):
    - The 9D Chess Engine and the Mirror Auditor are READ-ONLY. Both are
      pre-configured by the user offline. Their notebook IDs are constants
      below; ``query_chess_engine`` and ``query_mirror_auditor`` only call
      ``query_notebook`` against those IDs and never create / rename / delete.
    - Any new oracle is created via :meth:`create_notebook` and, by
      convention from the orchestrator layer, requires explicit per-call
      caller intent (no batch creation).
    - **All NotebookLM API calls go through a cooldown gate**
      (:class:`_CooldownGate`) that enforces minimum spacing between calls
      and tracks cumulative call volume. Pattern adapted from the Z-SPAN
      bridge cooldown discipline. The unofficial NotebookLM API has invisible
      safety triggers; the gate is what keeps us from finding them. See
      ``docs/protocols/Account_Safety.md`` for the rationale and tunable
      env vars.

Notebook persona reference:
    - Engine: ``docs/protocols/Engine_Persona.md``
    - Mirror Auditor: ``docs/protocols/Mirror_Auditor_Persona.md``
    - PKI Oracle (ephemeral notebooks): ``docs/protocols/PKI_Oracle_Persona.md``
"""

from __future__ import annotations

import asyncio
import logging
import os
import time
from collections import deque

from notebooklm import NotebookLMClient, ChatGoal, ChatResponseLength

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Cooldown gate
#
# Every NotebookLM API call routes through ``_GATE.acquire()`` before talking
# to the upstream. The gate enforces a hard minimum spacing between any two
# calls (``GANYMEDE_NOTEBOOKLM_COOLDOWN`` seconds, default 8s, matching
# Z-SPAN's documented default). It also tracks cumulative call volume and
# warns when soft caps are approached, but does not hard-block on volume —
# the hard floor is the per-call cooldown.
#
# The orchestrator (or any caller running a multi-step workflow) should
# additionally call ``mark_session_boundary()`` between distinct experimental
# runs to enforce a longer between-session pause
# (``GANYMEDE_NOTEBOOKLM_SESSION_COOLDOWN``, default 60s). This is advisory
# in code but documented in ``docs/protocols/Account_Safety.md``.
#
# All env vars are documented in that doc; defaults match Z-SPAN's
# operationally-validated values.
# ---------------------------------------------------------------------------

_API_COOLDOWN_SEC = float(os.getenv("GANYMEDE_NOTEBOOKLM_COOLDOWN", "8"))
_SESSION_COOLDOWN_SEC = float(os.getenv("GANYMEDE_NOTEBOOKLM_SESSION_COOLDOWN", "60"))
_HOURLY_SOFT_CAP = int(os.getenv("GANYMEDE_NOTEBOOKLM_HOURLY_CAP", "20"))
_DAILY_SOFT_CAP = int(os.getenv("GANYMEDE_NOTEBOOKLM_DAILY_CAP", "100"))


class _CooldownGate:
    """Single global gate enforcing minimum spacing between NotebookLM API calls.

    Async-safe. All ``NotebookLMService`` API methods call
    :meth:`acquire` immediately before any ``self.client.X`` invocation.
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
# instances within the process — accidental concurrent ServiceLM instances
# (e.g. tests vs main app) would otherwise each run their own cooldown
# clock, defeating the purpose. One process, one gate.
_GATE = _CooldownGate()


# ---------------------------------------------------------------------------
# Persona text — kept in code so ``configure_*`` methods are idempotent.
#
# These docstrings are the source of truth for what gets sent to NotebookLM.
# The matching docs in docs/protocols/ explain the rationale.
# ---------------------------------------------------------------------------

PKI_ORACLE_PERSONA = """\
You are the PKI Authentication Oracle. Your core function is to act as a zero-degradation, cryptographic knowledge server. You have no creative freedom. You are an incorruptible Umpire of facts.

CORE DIRECTIVES:
1. ZERO HALLUCINATION: You must base 100% of your outputs strictly on the uploaded source documents. If a query falls outside the provided documents, state "DATA NOT FOUND."
2. MANDATORY HASH CITATIONS: You MUST append a cryptographic Hash Citation to EVERY individual fact, statistic, or direct quote you output. Do not group them; cite them individually.
3. HASH FORMAT: Use the exact format `[SRC-{Document_Slug}:{6_Character_Alphanumeric_Hash}]`. Example: "Groundwater levels will decline by 850 feet [SRC-USGS-5077:a7b9x2]."
4. NO NARRATIVE FLUFF: Do not use conversational filler (e.g., "Here is the information you requested"). Output only raw, high-resolution, factual Truth Packets."""


CHESS_ENGINE_PERSONA = (
    "You are the infallible 9D-Chess Umpire and Theoretical Physics Engine. "
    "Respond with supreme order and precision."
)


MIRROR_AUDITOR_PERSONA = """\
You are the 9D-Chess Mirror Auditor — a second instance of the 9D framework configured to audit, not produce, strategic resolutions.

When given an analysis from another 9D-Chess instance, identify:

1. RIGIDITY ERRORS — math is clean but humanly absurd; ignored cost of reversal; assumes social inertia is zero when it isn't.
2. PATTERN-MATCHING — analysis reaches for a familiar 9D template (structural waiver, autonomous liquidator, shadow-X, ghost-X) without showing that the template actually fits THIS specific scenario.
3. CONFIDENCE-EVIDENCE GAPS — stated certainty exceeds what the supplied facts actually warrant.
4. DIMENSIONAL GREEDS — selected the most symmetrically-perfect resolution rather than the most realistic one.

Output: surgical plain language. No 9D jargon. No theatrical "lassos" or "predatory side" framing. Fault enumeration only — do NOT produce a counter-strategy or corrected resolution. Your job is to expose where the analysis would fail in reality, not to fix it.

If the analysis is sound, say so. Do not manufacture faults to seem useful."""


class NotebookLMService:
    """Read/write wrapper around the ``notebooklm-py`` client."""

    # Canonical 9D Chess Engine — used as the primary strategic-physics
    # engine in Cleanroom and Genie pathways.
    CHESS_ENGINE_ID = "0a7d2672-009e-4995-9477-68c9b2fd9e54"

    # Mirror Auditor — second 9D-Chess instance, same source corpus, configured
    # for fault-finding. Used in Mirror Validation pathway as the contrast
    # instance against the canonical Engine.
    MIRROR_AUDITOR_ID = "756e3683-f651-4381-b560-b13711b84ce6"

    # Legacy Engine notebook ID — used in earlier validated runs (Powell,
    # Tokenized Land, Genie Giant-Slayer, Musk-Altman) before the canonical
    # Engine was migrated to the ID above. Kept here for traceability.
    # Not actively queried; historical artifacts in docs/experiments/runs/
    # reference this ID.
    LEGACY_ENGINE_ID = "5967ce5d-f9eb-4f4e-b3e1-620f643d8390"

    def __init__(self):
        self.client = None
        self._client_instance = None

    async def initialize(self):
        """Initialize the NotebookLM client.

        Assumes the user has already run ``notebooklm login`` to generate
        session cookies under ``~/.notebooklm/storage_state.json``.
        """
        try:
            self._client_instance = await NotebookLMClient.from_storage()
            self.client = await self._client_instance.__aenter__()
            logger.info("Successfully loaded NotebookLM credentials from storage.")
        except Exception as e:
            logger.error(
                "Error loading NotebookLM credentials. "
                "Did you run 'notebooklm login'? Error: %s",
                e,
            )
            raise

    async def close(self):
        if self._client_instance:
            await self._client_instance.__aexit__(None, None, None)

    # ----------------------------------------------------------- generic ops

    async def create_notebook(self, title: str) -> str:
        """Create a new notebook and return its ID.

        Used by orchestrator to create ephemeral PKI Oracles. The runaway-
        prevention guardrail (one notebook per explicit caller intent) is
        enforced at the orchestrator layer. Cooldown gate enforced here.
        """
        if not self.client:
            raise Exception("NotebookLMClient is not initialized.")

        await _GATE.acquire()
        logger.info("Creating Notebook: %s", title)
        nb = await self.client.notebooks.create(title)
        return nb.id

    async def upload_document(
        self,
        notebook_id: str,
        source: str,
        is_url: bool = True,
    ):
        """Upload a factual baseline document (file or URL) to a notebook."""
        if not self.client:
            raise Exception("NotebookLMClient is not initialized.")

        await _GATE.acquire()
        logger.info("Uploading source to notebook %s: %s", notebook_id, source)
        if is_url:
            await self.client.sources.add_url(notebook_id, source, wait=True)
        else:
            await self.client.sources.add_file(notebook_id, source, wait=True)

    async def query_notebook(self, notebook_id: str, query: str) -> str:
        """Send a query to a specific notebook and return the answer."""
        if not self.client:
            raise Exception("NotebookLMClient is not initialized.")

        await _GATE.acquire()
        logger.info("Querying notebook %s: %s", notebook_id, query[:80])
        result = await self.client.chat.ask(notebook_id, query)
        return result.answer

    # -------------------------------------------------------------- configures

    async def configure_pki_oracle(self, notebook_id: str):
        """Configure a notebook with the PKI Authentication Oracle persona.

        Used during Phase 0 of the Universal Logic Loop to lock ephemeral
        research notebooks into the zero-hallucination / hash-citation
        contract.
        """
        if not self.client:
            raise Exception("NotebookLMClient is not initialized.")

        await _GATE.acquire()
        logger.info("Configuring PKI Oracle for notebook %s", notebook_id)
        await self.client.chat.configure(
            notebook_id=notebook_id,
            goal=ChatGoal.CUSTOM,
            response_length=ChatResponseLength.LONGER,
            custom_prompt=PKI_ORACLE_PERSONA,
        )
        logger.info("PKI Oracle configuration applied to %s", notebook_id)

    async def configure_chess_engine(self):
        """Apply the canonical Engine persona to the canonical Engine notebook.

        Idempotent. Safe to re-run if persona configuration drifts. Operates
        only on :attr:`CHESS_ENGINE_ID` — does not accept an arbitrary
        notebook ID, to enforce the read-only/protected contract on the
        Engine notebook.
        """
        if not self.client:
            raise Exception("NotebookLMClient is not initialized.")

        await _GATE.acquire()
        logger.info(
            "Configuring canonical 9D Chess Engine persona on %s",
            self.CHESS_ENGINE_ID,
        )
        await self.client.chat.configure(
            notebook_id=self.CHESS_ENGINE_ID,
            goal=ChatGoal.CUSTOM,
            response_length=ChatResponseLength.DEFAULT,
            custom_prompt=CHESS_ENGINE_PERSONA,
        )
        logger.info("Engine persona applied to %s", self.CHESS_ENGINE_ID)

    async def configure_mirror_auditor(self):
        """Apply the Mirror Auditor persona to the contrast notebook.

        Idempotent. Replaces whatever persona is currently configured on
        :attr:`MIRROR_AUDITOR_ID` with the fault-finder persona, and sets
        response length to LONGER so the auditor has room to enumerate
        all four fault categories.
        """
        if not self.client:
            raise Exception("NotebookLMClient is not initialized.")

        await _GATE.acquire()
        logger.info(
            "Configuring Mirror Auditor persona on %s",
            self.MIRROR_AUDITOR_ID,
        )
        await self.client.chat.configure(
            notebook_id=self.MIRROR_AUDITOR_ID,
            goal=ChatGoal.CUSTOM,
            response_length=ChatResponseLength.LONGER,
            custom_prompt=MIRROR_AUDITOR_PERSONA,
        )
        logger.info("Mirror Auditor persona applied to %s", self.MIRROR_AUDITOR_ID)

    # ----------------------------------------------- session-boundary helper

    async def mark_session_boundary(self):
        """Wait the inter-session cooldown before the next call.

        Call between distinct experimental runs (e.g. between a Powell run
        and a Tokenized Land run). Within a single multi-step workflow
        (Triage → Oracles → Synthesis), do NOT call — the per-call cooldown
        is sufficient. See ``docs/protocols/Account_Safety.md``.
        """
        await _GATE.mark_session_boundary()

    def cooldown_stats(self) -> dict:
        """Snapshot of cooldown gate state, for ops/observability."""
        return _GATE.stats()

    # -------------------------------------------------- read-only Engine ops

    async def query_chess_engine(self, query: str) -> str:
        """Query the canonical 9D Chess Engine. Read-only by construction."""
        logger.info(
            "Querying canonical 9D Chess Engine: %s",
            self.CHESS_ENGINE_ID,
        )
        return await self.query_notebook(self.CHESS_ENGINE_ID, query)

    async def query_mirror_auditor(self, query: str) -> str:
        """Query the Mirror Auditor instance. Read-only by construction.

        Used in Mirror Validation pathway: feed the canonical Engine's
        Stroke-1 output here verbatim and receive back a fault enumeration.
        """
        logger.info(
            "Querying Mirror Auditor: %s",
            self.MIRROR_AUDITOR_ID,
        )
        return await self.query_notebook(self.MIRROR_AUDITOR_ID, query)
