"""
Universal Logic Loop orchestration.

Composes :class:`NotebookLMService` into the four-phase workflow defined in
``docs/protocols/Universal_Logic_Loop_Protocol.md``. The loop is exposed as
explicit single-step primitives; there is no auto-run "do everything" call.

Runaway-prevention guardrail (Hard Guardrail #2 in ``docs/OVERVIEW.md``)
is enforced in code: :meth:`GanymedeOrchestrator.create_oracle` creates
*exactly one* notebook per call. There is no batch variant, on purpose.
The caller (a human, an HTTP request, or a higher-level driver) sequences
the loop.

The 9D Chess Engine is touched only via
:meth:`NotebookLMService.query_chess_engine`, which is read-only by
construction (Hard Guardrail #1).
"""

from __future__ import annotations

import asyncio
import hashlib
import logging
from dataclasses import dataclass
from typing import Optional, Union

from app.services.notebooklm_service import NotebookLMService

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Default prompt templates.
#
# These reflect the patterns refined across the experiments in
# docs/experiments/. Callers can override any of them when a scenario needs
# non-standard framing.
# ---------------------------------------------------------------------------

TRIAGE_TEMPLATE = """\
SITUATION INGESTION: {scenario}

MISSION:
Perform a 9D Strategic Breakdown of this situation. Identify the core
subjects, entities, and dimensions involved.

RESTRICTION:
Generate a 'Strategic Hit List' of research subjects for our PKI Oracle
swarm. To prevent system sprawl, LIMIT this list to the top {max_subjects}
most critical, high-impact subjects that require factual verification to
understand the cascading failure points.

Output the Breakdown and the Hit List clearly.
"""

DEFAULT_GO_SIGNAL = (
    "YES. PROCEED. Execute the deep research now and extract the Truth "
    "Packet. Output strictly raw, hash-cited facts. No conversational filler."
)

DEFAULT_EXTRACT_PROMPT = (
    "Provide the final Truth Packet for this research subject. Output only "
    "the high-resolution facts discovered via deep research. Cite each fact "
    "individually using the [SRC-{slug}:{hash}] format. No conversational "
    "filler."
)

SYNTHESIS_TEMPLATE = """\
ORIGINAL SCENARIO:
{scenario}

AUTHENTICATED TRUTH PACKETS (from PKI Oracle swarm):
{packets_block}

MISSION:
Re-analyze the original scenario holistically using the 9D Chess Engine.
The Truth Packets above are factual anchors — every claim is hash-cited
and sourced. Use them to resolve the scenario at maximum resolution
across all nine dimensions.

Do not pre-frame the analysis. Do not limit the output to 'SDS only.'
Let the engine apply its full physics. Output the final 9D resolution.
"""

RESOLUTION_CHECK = (
    "Resolution check: do you have enough authenticated detail to consider "
    "this simulation resolved at maximum 9D resolution? If you require "
    "additional detail, list specific follow-up questions targeted at the "
    "*existing* Oracle swarm only — do not request the creation of new "
    "Oracles. If the simulation is fully resolved, state 'RESOLUTION COMPLETE.'"
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class OracleHandle:
    """Reference to a created PKI Oracle."""

    subject: str
    full_name: str
    notebook_id: str
    hash_suffix: str


def oracle_name(subject: str) -> tuple[str, str]:
    """Generate the canonical ``(full_name, hash_suffix)`` for a subject.

    The suffix is a deterministic 8-char SHA-256 prefix so the same subject
    name produces the same suffix across runs. The canonical identifier of
    a notebook is the ``notebook_id`` returned from NotebookLM; the name is
    cosmetic (and helps human eyeballs find a notebook in the UI).
    """
    base = f"PKI_{subject.replace(' ', '_')}"
    suffix = hashlib.sha256(base.encode()).hexdigest()[:8]
    return f"{base}_{suffix}", suffix


def render_packets_block(packets: dict[str, str]) -> str:
    """Render ``{subject: truth_packet}`` into the synthesis context block.

    Insertion order is preserved (Python 3.7+ dict ordering).
    """
    parts: list[str] = []
    for subject, packet in packets.items():
        parts.append(f"--- TRUTH PACKET: {subject} ---")
        parts.append(packet.strip())
        parts.append("")
    return "\n".join(parts).strip()


# ---------------------------------------------------------------------------
# The orchestrator
# ---------------------------------------------------------------------------

class GanymedeOrchestrator:
    """Universal Logic Loop service.

    Each method is one step. The caller is responsible for sequencing.
    """

    def __init__(self, notebook_svc: NotebookLMService):
        self.svc = notebook_svc

    # -------------------------------------------------------- Phase 1: Triage

    async def triage(
        self,
        scenario: str,
        *,
        max_subjects: int = 3,
        prompt: Optional[str] = None,
    ) -> str:
        """Submit a scenario to the 9D Chess Engine and return the
        Strategic Hit List as raw text.

        The default prompt limits the hit list to ``max_subjects`` items
        to keep the swarm size manageable. Parsing the response into a
        structured list of subjects is the caller's job — the Umpire's
        formatting varies, so heuristic structured parsing is unreliable.
        """
        rendered = (prompt or TRIAGE_TEMPLATE).format(
            scenario=scenario, max_subjects=max_subjects
        )
        logger.info("Phase 1 triage: %s", scenario[:60])
        return await self.svc.query_chess_engine(rendered)

    # -------------------------------------------------------- Phase 2: Swarm

    async def create_oracle(
        self,
        subject: str,
        surgical_prompt: str,
    ) -> OracleHandle:
        """Create one PKI Oracle: new notebook → persona lock → surgical prompt.

        Returns the :class:`OracleHandle`.

        Each call creates exactly one notebook. There is no batch variant
        on purpose — the runaway-prevention guardrail is enforced here.

        ``surgical_prompt`` must be plain-language. Umpire jargon
        (D-numbers, ROEM, Horus, etc.) does not survive contact with the
        Deep Research engine — translate it before invoking this method.
        """
        full_name, suffix = oracle_name(subject)
        logger.info("Phase 2 create_oracle: %s", full_name)

        notebook_id = await self.svc.create_notebook(full_name)
        await self.svc.configure_pki_oracle(notebook_id)

        # Send the surgical prompt to invite the Deep Research session.
        # The Oracle typically responds with an offer to begin the multi-
        # minute web scour. The caller follows up with send_go() to start it.
        await self.svc.query_notebook(notebook_id, surgical_prompt)

        return OracleHandle(
            subject=subject,
            full_name=full_name,
            notebook_id=notebook_id,
            hash_suffix=suffix,
        )

    async def send_go(
        self,
        oracle: Union[OracleHandle, str],
        prompt: Optional[str] = None,
    ) -> str:
        """Send the GO signal to begin the Deep Research web scour.

        Returns the Oracle's confirmation. Note: Deep Research findings
        populate the NotebookLM Source Panel and require a manual UI
        ``Import`` click before they can be cited in a Truth Packet. This
        method does not handle that click — see
        ``docs/learnings/Iterative_Operational_Learnings.md`` for the
        end-to-end flow.
        """
        oracle_id = oracle.notebook_id if isinstance(oracle, OracleHandle) else oracle
        logger.info("Phase 2 send_go: %s", oracle_id)
        return await self.svc.query_notebook(oracle_id, prompt or DEFAULT_GO_SIGNAL)

    async def harvest(
        self,
        oracle: Union[OracleHandle, str],
        prompt: Optional[str] = None,
    ) -> str:
        """Extract the final hash-cited Truth Packet from a post-Import Oracle.

        Caller is responsible for ensuring the Source Panel data has been
        Imported in the UI before calling this — querying before Import
        returns an empty/uncertain notebook.
        """
        oracle_id = oracle.notebook_id if isinstance(oracle, OracleHandle) else oracle
        logger.info("Phase 2 harvest: %s", oracle_id)
        return await self.svc.query_notebook(
            oracle_id, prompt or DEFAULT_EXTRACT_PROMPT
        )

    async def harvest_swarm(
        self,
        oracles: dict[str, Union[OracleHandle, str]],
        prompt: Optional[str] = None,
    ) -> dict[str, str]:
        """Convenience: harvest multiple oracles in parallel.

        Returns ``{subject: truth_packet}``. Per-oracle failures surface
        as ``"EXTRACTION FAILED: <reason>"`` strings rather than raising,
        so a single bad notebook doesn't sink the whole swarm extraction.
        """

        async def _one(name: str, oracle: Union[OracleHandle, str]) -> tuple[str, str]:
            try:
                return name, await self.harvest(oracle, prompt)
            except Exception as exc:
                logger.exception("Harvest failed for %s", name)
                return name, f"EXTRACTION FAILED: {exc}"

        results = await asyncio.gather(
            *[_one(name, oracle) for name, oracle in oracles.items()]
        )
        return dict(results)

    # ---------------------------------------------------- Phase 3: Synthesis

    async def synthesize(
        self,
        scenario: str,
        truth_packets: dict[str, str],
        *,
        framing: Optional[str] = None,
    ) -> str:
        """Feed Truth Packets back to the 9D Chess Engine for holistic synthesis.

        The default framing is intentionally NOT 'find SDS' or 'find failure
        points' — it asks for unconstrained re-analysis. The Engine is a
        closed engine fed authenticated facts; we do not pre-frame it. See
        ``docs/protocols/Universal_Logic_Loop_Protocol.md`` for the
        rationale.
        """
        packets_block = render_packets_block(truth_packets)
        rendered = (framing or SYNTHESIS_TEMPLATE).format(
            scenario=scenario, packets_block=packets_block
        )
        logger.info(
            "Phase 3 synthesize: %d packet(s) on '%s'",
            len(truth_packets),
            scenario[:60],
        )
        return await self.svc.query_chess_engine(rendered)

    # ----------------------------------------- Phase 4: Recursive Dialogue

    async def resolution_check(self, prompt: Optional[str] = None) -> str:
        """Ask the Umpire whether it has enough resolution.

        If it requests follow-ups, route those queries back to the
        *existing* oracle swarm via :meth:`harvest` — never to new
        oracles, unless the human caller explicitly approves a new
        :meth:`create_oracle`. This is the runaway-prevention guardrail
        in protocol form.
        """
        logger.info("Phase 4 resolution_check")
        return await self.svc.query_chess_engine(prompt or RESOLUTION_CHECK)
