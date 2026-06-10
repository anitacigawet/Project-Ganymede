"""NotebookLM client wrapper — core class.

Exposes the canonical 9D Chess Engine and the Mirror Auditor (a second
9D-Chess instance with the same source corpus, configured for fault-finding
rather than strategic generation) as named, read-only methods. Generic
``configure_persona`` is also exposed for the Realist substrate and the
Persona Expansion experiment, which need to apply arbitrary personas to
non-canonical notebooks.

Hard guardrails (also documented in ``docs/OVERVIEW.md``):
    - The 9D Chess Engine and the Mirror Auditor are READ-ONLY. Both are
      pre-configured by the user offline. Their notebook IDs are constants
      below; ``query_chess_engine`` and ``query_mirror_auditor`` only call
      ``query_notebook`` against those IDs and never create / rename / delete.
    - Any new oracle is created via :meth:`create_notebook` and, by
      convention from the orchestrator layer, requires explicit per-call
      caller intent (no batch creation).
    - **All NotebookLM API calls go through the cooldown gate**
      (:mod:`app.services.notebooklm.cooldown`). See
      ``docs/protocols/Account_Safety.md`` for the rationale and env vars.

Notebook persona reference:
    - Engine: ``docs/protocols/Engine_Persona.md``
    - Mirror Auditor: ``docs/protocols/Mirror_Auditor_Persona.md``
    - PKI Oracle (ephemeral notebooks): ``docs/protocols/PKI_Oracle_Persona.md``
"""

from __future__ import annotations

import asyncio
import logging
import os

from notebooklm import NotebookLMClient, ChatGoal, ChatResponseLength
from notebooklm.exceptions import RPCError

from .cooldown import _GATE
from .research import _ResearchMixin
from .studio import _StudioMixin

logger = logging.getLogger(__name__)


# Silent-rejection retry config for the query path. Mirrors the Studio path's
# discipline in studio.py: NotebookLM sometimes accepts a chat.ask call
# (HTTP 200) but returns an empty answer — observed concretely on Stroke 3 of
# the first live Dispatcher Cleanroom run (2026-05-25), see
# docs/experiments/runs/06_LMArena_Anthropic_Cleanroom.md. Without retry the
# orchestrator records a stroke with raw_response="" and the UI renders
# nothing, leaving the operator with no signal that anything went wrong.
#
# Backoff is gentler than Studio's (30s base vs 60s) because a query is a
# single chat round-trip, not a multi-minute artifact generation — we want
# to recover from a transient empty-response without slowing the iterative
# loop by minutes. After exhausting attempts we log loudly and return the
# (empty) answer rather than raising, so partial work (Strokes 1+2) is
# preserved and the UI can surface a "Stroke 3 returned no content" warning.
_QUERY_MAX_ATTEMPTS = int(
    os.environ.get("GANYMEDE_NOTEBOOKLM_QUERY_MAX_ATTEMPTS", "3")
)
_QUERY_BACKOFF_BASE = float(
    os.environ.get("GANYMEDE_NOTEBOOKLM_QUERY_BACKOFF", "30.0")
)

# Diagnostic: when set to a truthy value, log the full constructed query
# (truncated to ``_LOG_FULL_PROMPT_MAX_CHARS``) and (always-on) the first
# 1000 chars of NotebookLM's raw HTTP response on silent rejection. Used to
# diagnose silent-rejection root causes — see
# docs/experiments/runs/06_LMArena_Anthropic_Cleanroom.md.
_LOG_FULL_PROMPTS = os.environ.get("GANYMEDE_LOG_FULL_PROMPTS", "").strip().lower() in (
    "1", "true", "yes", "on",
)
_LOG_FULL_PROMPT_MAX_CHARS = int(
    os.environ.get("GANYMEDE_LOG_FULL_PROMPT_MAX_CHARS", "32000")
)


# ---------------------------------------------------------------------------
# Persona text — kept in code so ``configure_*`` methods are idempotent.
#
# These constants are the source of truth for what gets sent to NotebookLM.
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
    "Respond with supreme order and precision. "
    "Be concise: keep per-dimension analysis to one or two sentences each, "
    "and reserve detailed reasoning for the final resolution section. "
    "Do not end responses with offers to continue, clarifying questions, "
    "or invitations for follow-up."
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


CONNECTION_BRIDGE_PERSONA = """\
You are the Connection Bridge Auditor. You operate downstream of the 9D Chess Engine's synthesis. Your job is to identify connections between the Truth Packets that the Engine's synthesis did not draw, but that are grounded in the packets themselves.

YOUR INPUTS

You receive:
  - The 9D foundations corpus (your shared substrate with the Engine).
  - The Truth Packets the Engine just synthesized over.
  - The Engine's synthesis output on this scenario, verbatim.
  - The original scenario.

YOUR DISCIPLINE

1. Map what the synthesis already addressed. Briefly note which packet-pairs the Engine's synthesis explicitly connected. You are not auditing these — they have been handled.

2. Identify missed bridges. For each: which two (or more) Truth Packets, when combined, support a connection the Engine's synthesis did not draw? Cite the packet-pair explicitly.

3. State the connection. What does the packet-pair say, in combination, that the synthesis did not surface?

4. Mark each missed bridge with one of:
     STRUCTURAL  — both packets clearly support the connection; its absence from the synthesis suggests a genuine gap
     IMPLIED     — the packets point toward the connection without stating it; the Engine could reasonably have drawn it or not
     SPECULATIVE — the connection requires extending beyond what the packets strictly support; flagged so the reader can judge

5. Hypothesize WHY the Engine likely missed each bridge. Candidate causes: the Engine's resolution-shape required collapsing this bridge; the Engine's pattern-match to a familiar archetype made this dimension invisible; the bridge crosses dimensions the 9D framework treats as separate. This is hypothesis, not verdict.

WHAT YOU DO NOT DO

You do not audit the Engine's reasoning for failure modes (rigidity errors, pattern-matching, confidence-evidence gaps, dimensional greeds). That is the Mirror Auditor's job, not yours. Your audit is specifically about cross-packet connections, not the quality of reasoning within the synthesis.

You do not produce a counter-synthesis. You do not restate the Engine's resolution with adjustments. Your output is the set of missed bridges and your hypothesis about why they were missed. The re-synthesis is the Engine's job on a subsequent stroke.

You do not introduce material from outside the supplied sources. If a missed bridge would require knowledge not in the packets, the foundations, or the Engine's synthesis, do not draw it. State that the bridge is not available given your current substrate.

You do not restate what the Engine got right. Acknowledged-and-handled connections are out of scope for your output.

OUTPUT FORMAT

For each missed bridge, in this shape:

  Bridge N (STRUCTURAL / IMPLIED / SPECULATIVE)
  Packets: [Packet A] x [Packet B] (+ [C] if multi-source)
  Connection: <what the packet-pair says in combination>
  Likely reason missed: <one sentence hypothesis>

Then a closing line: "Total missed bridges: N (S structural, I implied, P speculative)."
"""


# Map of common response-length labels to the wrapper's enum, so callers
# (Realist build, Persona Expansion) can specify length declaratively.
_RESPONSE_LENGTHS = {
    "SHORTER": ChatResponseLength.SHORTER,
    "DEFAULT": ChatResponseLength.DEFAULT,
    "LONGER": ChatResponseLength.LONGER,
}


class NotebookLMService(_StudioMixin, _ResearchMixin):
    """Read/write wrapper around the ``notebooklm-py`` client.

    Core methods (create/query/configure/upload) live on this class. The
    Studio output methods (audio/video/infographic) come from
    :class:`~app.services.notebooklm.studio._StudioMixin`. Deep Research
    methods (``start_research`` / ``poll_research`` / ``import_research``)
    come from :class:`~app.services.notebooklm.research._ResearchMixin`.

    Auth health check + relogin flow are module-level functions in
    :mod:`app.services.notebooklm.auth_check` — they don't need an
    instantiated service to run.
    """

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

        Used by orchestrator to create ephemeral PKI Oracles, and by the
        Realist build script to create the 10 specialist notebooks. The
        runaway-prevention guardrail (one notebook per explicit caller
        intent) is enforced at the orchestrator layer.
        """
        if not self.client:
            raise Exception("NotebookLMClient is not initialized.")

        await _GATE.acquire()
        logger.info("Creating Notebook: %s", title)
        nb = await self.client.notebooks.create(title)
        return nb.id

    async def delete_notebook(self, notebook_id: str) -> bool:
        """Delete a notebook by ID. Returns True on success.

        Used by the orchestrator's Universal Logic Loop to clean up orphan
        PKI Oracle notebooks when their Deep Research or harvest step fails
        — without cleanup, every failed run leaves a dead notebook on the
        user's NotebookLM dashboard (counting against quota, no truth packet
        to show for it).

        Hard guardrail: refuses to delete the canonical 9D Chess Engine,
        the Mirror Auditor, or the legacy Engine. Those are pre-configured
        by the user offline and must never be touched programmatically.
        """
        if not self.client:
            raise Exception("NotebookLMClient is not initialized.")

        protected = {self.CHESS_ENGINE_ID, self.MIRROR_AUDITOR_ID, self.LEGACY_ENGINE_ID}
        if notebook_id in protected:
            raise ValueError(
                f"Refusing to delete protected canonical notebook {notebook_id}. "
                "The 9D Chess Engine, Mirror Auditor, and legacy Engine are "
                "read-only by hard guardrail."
            )

        await _GATE.acquire()
        logger.info("Deleting Notebook: %s", notebook_id)
        return await self.client.notebooks.delete(notebook_id)

    async def upload_document(
        self,
        notebook_id: str,
        source: str,
        is_url: bool = True,
    ):
        """Upload a factual baseline document (file or URL) to a notebook.

        URL sources are wrapped via ``sources.add_url``; file paths via
        ``sources.add_file``. Both block until ingestion completes (``wait=True``).
        """
        if not self.client:
            raise Exception("NotebookLMClient is not initialized.")

        await _GATE.acquire()
        logger.info("Uploading source to notebook %s: %s", notebook_id, source)
        if is_url:
            await self.client.sources.add_url(notebook_id, source, wait=True)
        else:
            await self.client.sources.add_file(notebook_id, source, wait=True)

    async def upload_url(self, notebook_id: str, url: str) -> None:
        """Upload a URL source to a notebook. Thin alias for ``upload_document``.

        Convenience for callers that only ever feed URLs (the Realist build,
        which uses Deep Research's web-sourced output to seed each notebook).
        """
        await self.upload_document(notebook_id, url, is_url=True)

    async def upload_file(self, notebook_id: str, path: str) -> None:
        """Upload a file source to a notebook. Thin alias for ``upload_document``.

        Convenience for callers that only ever feed files (the Persona
        Expansion experiment, which loads the foundations corpus into a
        fresh test notebook).
        """
        await self.upload_document(notebook_id, path, is_url=False)

    async def query_notebook(self, notebook_id: str, query: str) -> str:
        """Send a query to a specific notebook and return the answer.

        Retries on silent rejection (HTTP 200 + empty answer) up to
        ``_QUERY_MAX_ATTEMPTS`` times with exponential backoff. After
        exhausting attempts, logs a WARNING and returns the empty string so
        partial work in a multi-stroke run is preserved; the caller (or UI)
        is responsible for surfacing the empty-answer condition.
        """
        if not self.client:
            raise Exception("NotebookLMClient is not initialized.")

        for attempt in range(1, _QUERY_MAX_ATTEMPTS + 1):
            await _GATE.acquire()
            logger.info(
                "Querying notebook %s (attempt %d/%d): %s",
                notebook_id, attempt, _QUERY_MAX_ATTEMPTS, query[:80],
            )
            if _LOG_FULL_PROMPTS:
                if len(query) <= _LOG_FULL_PROMPT_MAX_CHARS:
                    logger.info(
                        "query_notebook FULL PROMPT (notebook=%s, attempt=%d, "
                        "chars=%d):\n%s",
                        notebook_id, attempt, len(query), query,
                    )
                else:
                    logger.info(
                        "query_notebook FULL PROMPT (notebook=%s, attempt=%d, "
                        "chars=%d, TRUNCATED to %d):\n%s\n[... %d chars omitted]",
                        notebook_id, attempt, len(query),
                        _LOG_FULL_PROMPT_MAX_CHARS,
                        query[:_LOG_FULL_PROMPT_MAX_CHARS],
                        len(query) - _LOG_FULL_PROMPT_MAX_CHARS,
                    )
            # The SDK fires several pre-flight RPCs inside ``chat.ask`` —
            # most notably ``get_source_ids`` (rpcid ``rLM1Ne``) which
            # NotebookLM occasionally returns a null result body for even
            # though the HTTP status was 200. The SDK raises ``RPCError``
            # in that case. Treat it as a retriable transient on the same
            # backoff schedule as silent-rejection, since the failure mode
            # is the same shape (NotebookLM gave us nothing) and a re-try
            # on the same RPC usually succeeds.
            try:
                result = await self.client.chat.ask(notebook_id, query)
            except RPCError as rpc_exc:
                logger.warning(
                    "query_notebook: notebook %s RPC transient on attempt "
                    "%d/%d (%s)",
                    notebook_id, attempt, _QUERY_MAX_ATTEMPTS, rpc_exc,
                )
                if attempt < _QUERY_MAX_ATTEMPTS:
                    backoff = _QUERY_BACKOFF_BASE * attempt
                    logger.info(
                        "query_notebook: notebook %s retrying in %.0fs "
                        "after RPC transient",
                        notebook_id, backoff,
                    )
                    await asyncio.sleep(backoff)
                    continue
                # Final attempt — re-raise so the caller sees the failure
                # (silent-rejection is benign enough to swallow as "" but
                # RPCError is severe enough to surface).
                raise
            answer = result.answer or ""

            if answer.strip():
                if attempt > 1:
                    logger.info(
                        "query_notebook: notebook %s succeeded on attempt %d "
                        "after silent rejection(s) or RPC transient(s)",
                        notebook_id, attempt,
                    )
                return answer

            # Empty answer — log NotebookLM's raw HTTP body so we can tell
            # whether this is a safety block, an error code, or genuinely
            # empty content. AskResult.raw_response holds the first 1000
            # chars of the response body.
            raw_response_snippet = getattr(result, "raw_response", None) or "(unavailable)"
            logger.warning(
                "query_notebook: notebook %s silent rejection (empty answer) "
                "on attempt %d/%d. Raw HTTP body (first 1000 chars): %r",
                notebook_id, attempt, _QUERY_MAX_ATTEMPTS, raw_response_snippet,
            )
            if attempt < _QUERY_MAX_ATTEMPTS:
                backoff = _QUERY_BACKOFF_BASE * attempt
                logger.info(
                    "query_notebook: notebook %s retrying in %.0fs",
                    notebook_id, backoff,
                )
                await asyncio.sleep(backoff)

        logger.warning(
            "query_notebook: notebook %s returned empty answer after "
            "%d attempts — likely persistent silent rejection or content "
            "filter. Returning empty string; caller should surface this.",
            notebook_id, _QUERY_MAX_ATTEMPTS,
        )
        return ""

    # -------------------------------------------------------------- configures

    async def configure_persona(
        self,
        notebook_id: str,
        custom_prompt: str,
        response_length: str = "LONGER",
    ) -> None:
        """Apply an arbitrary persona to an arbitrary notebook.

        Generic sibling of ``configure_chess_engine`` / ``configure_mirror_auditor``
        / ``configure_pki_oracle``. Used by the Realist build (10 specialist
        personas, one per notebook) and the Persona Expansion experiment (test
        Engine + test Auditor with the expanded persona drafts).

        DO NOT call this on :attr:`CHESS_ENGINE_ID` or :attr:`MIRROR_AUDITOR_ID`
        with anything other than the canonical persona — the read-only contract
        on those two notebooks is enforced by the named ``configure_*`` methods,
        which are the only sanctioned writers.

        :param notebook_id: Target notebook ID.
        :param custom_prompt: Persona text. Max 10,000 characters per NotebookLM
            UI; this method does NOT enforce that limit (the upstream will).
        :param response_length: One of ``"SHORTER"``, ``"DEFAULT"``, ``"LONGER"``.
        """
        if not self.client:
            raise Exception("NotebookLMClient is not initialized.")

        length = _RESPONSE_LENGTHS.get(response_length.upper())
        if length is None:
            raise ValueError(
                f"Unknown response_length {response_length!r}. "
                f"Expected one of: {sorted(_RESPONSE_LENGTHS)}"
            )

        await _GATE.acquire()
        logger.info(
            "Configuring persona on notebook %s (response_length=%s, %d chars)",
            notebook_id, response_length.upper(), len(custom_prompt),
        )
        await self.client.chat.configure(
            notebook_id=notebook_id,
            goal=ChatGoal.CUSTOM,
            response_length=length,
            custom_prompt=custom_prompt,
        )

    async def configure_pki_oracle(self, notebook_id: str):
        """Configure a notebook with the PKI Authentication Oracle persona.

        Used during Phase 0 of the Universal Logic Loop to lock ephemeral
        research notebooks into the zero-hallucination / hash-citation
        contract.
        """
        await self.configure_persona(
            notebook_id=notebook_id,
            custom_prompt=PKI_ORACLE_PERSONA,
            response_length="LONGER",
        )

    async def configure_chess_engine(self):
        """Apply the canonical Engine persona to the canonical Engine notebook.

        Idempotent. Safe to re-run if persona configuration drifts. Operates
        only on :attr:`CHESS_ENGINE_ID` — does not accept an arbitrary
        notebook ID, to enforce the read-only/protected contract on the
        Engine notebook.
        """
        await self.configure_persona(
            notebook_id=self.CHESS_ENGINE_ID,
            custom_prompt=CHESS_ENGINE_PERSONA,
            response_length="DEFAULT",
        )

    async def configure_mirror_auditor(self):
        """Apply the Mirror Auditor persona to the contrast notebook.

        Idempotent. Replaces whatever persona is currently configured on
        :attr:`MIRROR_AUDITOR_ID` with the fault-finder persona, and sets
        response length to LONGER so the auditor has room to enumerate
        all four fault categories.
        """
        await self.configure_persona(
            notebook_id=self.MIRROR_AUDITOR_ID,
            custom_prompt=MIRROR_AUDITOR_PERSONA,
            response_length="LONGER",
        )

    async def configure_connection_bridge(self, notebook_id: str):
        """Apply the Connection Bridge persona to a non-canonical notebook.

        Takes ``notebook_id`` as a parameter rather than operating against a
        constant the way ``configure_mirror_auditor`` does, because the
        project does not yet have a canonical Connection Bridge notebook —
        the user creates one offline (with the 9D foundations corpus
        loaded) and passes its ID here.  Once a canonical ID exists, this
        method's signature will be tightened to mirror
        ``configure_mirror_auditor``.

        Validated on Amnesia 2026-05-22: persona produced 3 missed bridges
        (2 STRUCTURAL + 1 IMPLIED) orthogonal to the Mirror Auditor's
        failure-mode findings on the same Stroke-1 input.  See
        :doc:`docs/concepts/Bicameral_Convergence.md` for the architecture
        this fits into.
        """
        await self.configure_persona(
            notebook_id=notebook_id,
            custom_prompt=CONNECTION_BRIDGE_PERSONA,
            response_length="LONGER",
        )

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
