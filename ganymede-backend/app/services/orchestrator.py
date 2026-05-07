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

from app.contracts import (
    Pathway,
    Scenario,
    StrokeResult,
    SessionEventType,
    TruthPacket,
    utcnow,
)
from app.services.notebooklm_service import NotebookLMService
from app.services.session import Session

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

    # =====================================================================
    # Session-aware methods (pluggable module surface).
    #
    # The primitives above (triage, create_oracle, send_go, harvest,
    # synthesize, resolution_check) are the low-level building blocks. The
    # methods below wrap them with Session bookkeeping and return strongly-
    # typed contracts (StrokeResult, etc.) suitable for module consumers.
    #
    # Phase 2 implements the pre-harvested-Truth-Packet synthesis path —
    # the simplest end-to-end path through the module. Subsequent phases
    # add session-aware oracle creation, audit strokes, and the multi-
    # stroke Iterative Engine loop.
    # =====================================================================

    async def run_synthesis_stroke(
        self,
        session: Session,
        truth_packets: list[TruthPacket],
        *,
        framing: Optional[str] = None,
    ) -> StrokeResult:
        """Run one synthesis stroke against the canonical Engine using
        pre-harvested Truth Packets.

        This is the path consumers use when they have their own grounded
        RAG layer (e.g. PrisonBreak's NotebookLM analysis findings) and
        want Ganymede to synthesize directly without spinning up new
        Oracles. Skips Phase-1 triage and Phase-2 oracle creation
        entirely; goes straight to Phase-3 synthesis.

        The method:
            1. Determines stroke_number from session.strokes
            2. Emits STROKE_STARTED on the session
            3. Builds the synthesis prompt from the session's Scenario
               and the consumer's TruthPackets
            4. Invokes the Engine via :meth:`synthesize`
            5. Constructs a StrokeResult and records it on the session
            6. Emits SYNTHESIS_COMPLETE and STROKE_COMPLETED
            7. Returns the StrokeResult

        For iterative multi-stroke runs, the caller invokes this
        repeatedly (with appropriate friction injection between calls).
        For single-pass runs, one call is sufficient and the caller then
        invokes :meth:`Session.complete`.

        Raises if the session is not in 'running' state, or if the
        scenario fields don't match the session's pathway.
        """
        if session.status != "running":
            raise RuntimeError(
                f"Session {session.id} is not running (status={session.status})"
            )
        if session.pathway not in (Pathway.CLEANROOM, Pathway.GENIE, Pathway.OFFENSIVE):
            raise ValueError(
                f"run_synthesis_stroke does not support pathway "
                f"{session.pathway.value} — use run_audit_stroke for "
                f"MIRROR_AUDIT (Phase 5)."
            )

        stroke_number = len(session.strokes) + 1
        await session.emit(
            SessionEventType.STROKE_STARTED,
            payload={"pathway": session.pathway.value, "kind": "synthesis"},
            stroke_number=stroke_number,
        )

        # Build the synthesis input. Scenario fields used depend on pathway.
        scenario_text = scenario_to_synthesis_text(session.scenario, session.pathway)
        packets_dict = {tp.subject: tp.content for tp in truth_packets}

        started = utcnow()
        logger.info(
            "Session %s stroke %d: synthesize against %s with %d packet(s)",
            session.id, stroke_number, session.pathway.value, len(truth_packets),
        )

        try:
            raw = await self.synthesize(
                scenario_text, packets_dict, framing=framing
            )
        except Exception as exc:
            await session.fail(str(exc), exc_type=type(exc).__name__)
            raise

        completed = utcnow()
        stroke = StrokeResult(
            stroke_number=stroke_number,
            pathway=session.pathway,
            raw_response=raw,
            # Structured-field extraction (strategic_lasso, etc.) is
            # deliberately deferred — Engine response formatting varies
            # too much for hardcoded extraction to be reliable. raw_response
            # is the source of truth; consumers display it directly.
            final_resolution=raw,
            started_at=started,
            completed_at=completed,
        )
        await session.record_stroke(stroke)
        await session.emit(
            SessionEventType.SYNTHESIS_COMPLETE,
            payload={"stroke_number": stroke_number, "response_chars": len(raw)},
            stroke_number=stroke_number,
        )
        await session.emit(
            SessionEventType.STROKE_COMPLETED,
            payload={"duration_seconds": stroke.duration_seconds},
            stroke_number=stroke_number,
        )
        return stroke


# ---------------------------------------------------------------------------
# Scenario → synthesis-prompt-text helper
#
# Different pathways pack their scenario text differently. This is the single
# source of truth for that mapping; both run_synthesis_stroke and (eventually)
# the multi-stroke loop use it.
# ---------------------------------------------------------------------------

def scenario_to_synthesis_text(scenario: Scenario, pathway: Pathway) -> str:
    """Render the consumer-facing Scenario into the text that gets
    interpolated as ``{scenario}`` in :data:`SYNTHESIS_TEMPLATE`.

    Pathway-specific:
        CLEANROOM → ``scenario.question`` (plus extra_context if present)
        GENIE     → ``current_state`` and ``wished_for_state`` formatted
        OFFENSIVE → ``target`` and ``objective_state`` formatted

    Raises ``ValueError`` if the pathway's required scenario fields are
    not populated.
    """
    extra = (
        f"\n\nADDITIONAL CONTEXT:\n{scenario.extra_context.strip()}"
        if scenario.extra_context
        else ""
    )

    if pathway is Pathway.CLEANROOM:
        if not scenario.question:
            raise ValueError(
                "CLEANROOM pathway requires Scenario.question to be set"
            )
        return scenario.question.strip() + extra

    if pathway is Pathway.GENIE:
        if not (scenario.current_state and scenario.wished_for_state):
            raise ValueError(
                "GENIE pathway requires Scenario.current_state and "
                "Scenario.wished_for_state to be set"
            )
        return (
            f"CURRENT STATE: {scenario.current_state.strip()}\n\n"
            f"WISHED-FOR STATE: {scenario.wished_for_state.strip()}"
            + extra
        )

    if pathway is Pathway.OFFENSIVE:
        if not (scenario.target and scenario.objective_state):
            raise ValueError(
                "OFFENSIVE pathway requires Scenario.target and "
                "Scenario.objective_state to be set"
            )
        return (
            f"TARGET: {scenario.target.strip()}\n\n"
            f"OBJECTIVE: {scenario.objective_state.strip()}"
            + extra
        )

    raise ValueError(
        f"scenario_to_synthesis_text: unsupported pathway {pathway.value}"
    )
