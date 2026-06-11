"""NotebookLM Deep Research methods — start / poll / import sources.

Mixin into :class:`~app.services.notebooklm.client.NotebookLMService`.
Wraps ``client.research.start``, ``client.research.poll``, and
``client.research.import_sources`` from ``notebooklm-py``, with cooldown
discipline applied to each call.

This unblocks the Realist 10-notebook substrate build (see
``docs/concepts/Realist_Notebook_Build.md``), which needs programmatic
Deep Research to seed each specialist notebook. It also unblocks any future
consumer that wants to expand a notebook's source corpus from a research
query rather than uploading pre-harvested documents.

Important API note: the upstream method is named ``import_sources`` (not
``import_`` as some older docs suggest). The wrapper here matches the
upstream naming.

Poll behavior: ``client.research.poll`` does NOT block until completion —
it's a single status snapshot. The :meth:`run_deep_research` convenience
method below loops on poll with an explicit interval, since polling at the
cooldown floor (8s) for 30 min would burn 225 calls against the soft caps.
"""

from __future__ import annotations

import asyncio
import logging
import os
import time

from notebooklm.exceptions import RPCTimeoutError

from .cooldown import _GATE

logger = logging.getLogger(__name__)


# Default polling cadence. The gate floor is 8s; this is longer because
# Deep Research can take many minutes and we don't want to burn the hourly
# soft cap on status polls.
_RESEARCH_POLL_INTERVAL_SEC = float(
    os.environ.get("GANYMEDE_NOTEBOOKLM_RESEARCH_POLL_INTERVAL", "60")
)
_RESEARCH_TIMEOUT_SEC = float(
    os.environ.get("GANYMEDE_NOTEBOOKLM_RESEARCH_TIMEOUT", "1800")
)
# IMPORT_RESEARCH retry layer. Even with the bumped httpx timeout in
# client.initialize() (300s), large source reports can still trip the
# limit, and transient network slowness should not kill a 25-min run.
# Retries with exponential backoff give the server a chance to settle
# between attempts. Tracked + fixed 2026-06-10 milestone 50.
_IMPORT_RETRIES = int(os.environ.get("GANYMEDE_NOTEBOOKLM_IMPORT_RETRIES", "3"))
_IMPORT_BACKOFF_BASE = float(
    os.environ.get("GANYMEDE_NOTEBOOKLM_IMPORT_BACKOFF_BASE", "30")
)


class ResearchTimeout(RuntimeError):
    """Deep Research did not reach status='completed' within the timeout."""


class _ResearchMixin:
    """Deep Research methods. Mixed into ``NotebookLMService``.

    Requires the host class to expose ``self.client`` (the underlying
    ``notebooklm-py`` client, populated by ``initialize()``).
    """

    async def start_research(
        self,
        notebook_id: str,
        query: str,
        source: str = "web",
        mode: str = "deep",
    ) -> dict | None:
        """Kick off a research session against a notebook.

        :param query: The research query text.
        :param source: ``"web"`` (default) or ``"drive"``.
        :param mode: ``"deep"`` (default) or ``"fast"``. Deep is web-only;
            ``mode="deep", source="drive"`` raises ``ValidationError`` upstream.

        Returns the upstream dict ``{task_id, report_id, notebook_id, query, mode}``
        or None on failure. ``task_id`` is what feeds the subsequent ``poll``
        and ``import_research_sources`` calls.
        """
        if not self.client:
            raise Exception("NotebookLMClient is not initialized.")

        await _GATE.acquire()
        logger.info(
            "Starting %s research on notebook %s: %s",
            mode, notebook_id, query[:80],
        )
        return await self.client.research.start(
            notebook_id=notebook_id,
            query=query,
            source=source,
            mode=mode,
        )

    async def poll_research(self, notebook_id: str) -> dict:
        """One status snapshot of the latest research task on a notebook.

        Does NOT block until completion — returns whatever state the
        upstream reports right now. Use :meth:`run_deep_research` for the
        wait-until-done flow.

        Returns the upstream dict with at minimum: ``task_id``, ``status``
        (``"in_progress"`` / ``"completed"`` / ``"no_research"``),
        ``query``, ``sources``, ``summary``, ``report``, and ``tasks``.
        """
        if not self.client:
            raise Exception("NotebookLMClient is not initialized.")

        await _GATE.acquire()
        logger.debug("Polling research status for notebook %s", notebook_id)
        return await self.client.research.poll(notebook_id)

    async def import_research_sources(
        self,
        notebook_id: str,
        task_id: str,
        sources: list[dict],
    ) -> list[dict]:
        """Import selected research sources into the notebook.

        :param task_id: The research task ID (from ``start_research``'s return
            value, or from any entry in ``poll_research``'s ``sources``).
        :param sources: A list of source dicts from ``poll_research``'s
            ``sources`` field. Each must have ``url`` (for web entries) or
            ``report_markdown`` + ``title`` + ``result_type=5`` (for the deep-
            research report entry).

        Returns the list of imported source records as the upstream reports
        them. The upstream response can be incomplete — to reliably verify
        imports, list the notebook's sources after this call.
        """
        if not self.client:
            raise Exception("NotebookLMClient is not initialized.")

        last_exc: Exception | None = None
        for attempt in range(1, _IMPORT_RETRIES + 1):
            await _GATE.acquire()
            logger.info(
                "Importing %d research sources into notebook %s (task %s) — attempt %d/%d",
                len(sources), notebook_id, task_id, attempt, _IMPORT_RETRIES,
            )
            try:
                return await self.client.research.import_sources(
                    notebook_id=notebook_id,
                    task_id=task_id,
                    sources=sources,
                )
            except RPCTimeoutError as exc:
                last_exc = exc
                if attempt >= _IMPORT_RETRIES:
                    logger.error(
                        "IMPORT_RESEARCH timed out on notebook %s after %d attempts; giving up.",
                        notebook_id, attempt,
                    )
                    raise
                backoff = _IMPORT_BACKOFF_BASE * (2 ** (attempt - 1))
                logger.warning(
                    "IMPORT_RESEARCH timed out on notebook %s (attempt %d/%d): %s. "
                    "Retrying in %.0fs — the prior import may have partially landed; "
                    "this attempt re-issues the request with a fresh httpx connection.",
                    notebook_id, attempt, _IMPORT_RETRIES, exc, backoff,
                )
                await asyncio.sleep(backoff)
        # Unreachable: we either return or raise inside the loop, but keep
        # this for the type checker.
        assert last_exc is not None
        raise last_exc

    # ----------------------------------------------------------- convenience

    async def run_deep_research(
        self,
        notebook_id: str,
        query: str,
        source: str = "web",
        mode: str = "deep",
        poll_interval: float | None = None,
        timeout: float | None = None,
        auto_import: bool = False,
        max_sources: int | None = None,
    ) -> dict:
        """Start a research session, wait for completion, optionally import sources.

        This is the convenience flow that the Realist build script uses for
        each of the 10 specialist notebooks: kick off Deep Research, wait for
        the report to land, optionally import all sources back into the
        notebook so the notebook's chat has the full corpus to draw on.

        :param poll_interval: Seconds between poll calls. Defaults to
            ``GANYMEDE_NOTEBOOKLM_RESEARCH_POLL_INTERVAL`` (60s). The cooldown
            gate's 8s floor still applies on top.
        :param timeout: Total seconds to wait for completion. Defaults to
            ``GANYMEDE_NOTEBOOKLM_RESEARCH_TIMEOUT`` (1800s / 30 min). Raises
            :class:`ResearchTimeout` if the research is still in_progress
            when the timeout expires.
        :param auto_import: If True, import all sources from the completed
            task back into the notebook. Default False — most callers want
            to inspect the source list first before deciding what to keep.
        :param max_sources: When ``auto_import=True``, cap the number of
            imported sources at this count. None = import all.

        Returns ``{ task_id, status, query, sources, summary, report,
        imported }`` where ``imported`` is the list returned by
        ``import_research_sources`` (empty list if ``auto_import=False``).
        """
        interval = poll_interval if poll_interval is not None else _RESEARCH_POLL_INTERVAL_SEC
        deadline_sec = timeout if timeout is not None else _RESEARCH_TIMEOUT_SEC

        started = await self.start_research(
            notebook_id=notebook_id,
            query=query,
            source=source,
            mode=mode,
        )
        if started is None:
            raise RuntimeError(
                f"Deep Research start returned None for notebook {notebook_id}"
            )

        task_id = started.get("task_id")
        logger.info(
            "Deep Research started on %s (task %s); polling every %.0fs (timeout %.0fs)",
            notebook_id, task_id, interval, deadline_sec,
        )

        deadline = time.monotonic() + deadline_sec
        latest: dict = {"status": "in_progress"}
        while True:
            latest = await self.poll_research(notebook_id)
            status = latest.get("status")
            if status == "completed":
                logger.info(
                    "Deep Research completed on %s (task %s); %d sources",
                    notebook_id, task_id, len(latest.get("sources", [])),
                )
                break
            if status == "no_research":
                raise RuntimeError(
                    f"Deep Research poll returned 'no_research' for notebook "
                    f"{notebook_id} (task {task_id}). Did start_research succeed?"
                )

            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise ResearchTimeout(
                    f"Deep Research did not complete within {deadline_sec:.0f}s "
                    f"(notebook {notebook_id}, task {task_id})"
                )
            sleep_for = min(interval, remaining)
            logger.debug(
                "Deep Research still in_progress on %s; sleeping %.0fs",
                notebook_id, sleep_for,
            )
            await asyncio.sleep(sleep_for)

        imported: list[dict] = []
        if auto_import:
            sources = latest.get("sources", []) or []
            if max_sources is not None:
                sources = sources[:max_sources]
            if sources:
                imported = await self.import_research_sources(
                    notebook_id=notebook_id,
                    task_id=task_id,
                    sources=sources,
                )
                logger.info(
                    "Auto-imported %d/%d sources into %s",
                    len(imported), len(sources), notebook_id,
                )

        return {
            "task_id": task_id,
            "status": latest.get("status", "completed"),
            "query": latest.get("query", query),
            "sources": latest.get("sources", []),
            "summary": latest.get("summary", ""),
            "report": latest.get("report", ""),
            "imported": imported,
        }
