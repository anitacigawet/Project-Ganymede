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
import os
import re
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional, Union

from app.contracts import (
    Pathway,
    Scenario,
    StrokeResult,
    SessionEventType,
    TruthPacket,
    utcnow,
)
from app.services.bridge_registry import registry as bridge_notebook_registry
from app.services.notebooklm import NotebookLMService
from app.services.session import Session

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Cancellation
#
# Raised by ``GanymedeOrchestrator._check_cancelled`` when the orchestrator
# observes that the session's ``cancel_requested`` flag has been set (via
# ``POST /api/v2/sessions/{id}/cancel``). The exception propagates up
# through the loop; the HTTP endpoint catches it and returns a 200 with
# the partial strokes that completed before cancellation.
#
# Distinct from ``asyncio.CancelledError`` on purpose — asyncio's
# CancelledError has special semantics in the runtime (it can be re-raised
# by tasks the runtime is unwinding) and we don't want to confuse the two.
# This is a cooperative-cancellation signal observed at well-defined check
# points; it never originates from the runtime.
# ---------------------------------------------------------------------------

class SessionCancelledError(Exception):
    """Raised when an orchestrator loop observes that its session has been
    cancelled by the operator. Carries the check-point name for debugging."""

    def __init__(self, where: str, session_id: str):
        self.where = where
        self.session_id = session_id
        super().__init__(f"Session {session_id} cancelled at {where}")


# ---------------------------------------------------------------------------
# Iterative-Engine Stroke-3 injection budgets.
#
# NotebookLM's chat.ask endpoint silently rejects queries above ~5,100-6,000
# characters (returns structured error envelope [["e",4,null,null,N]] which
# the SDK falls through to "no answer extracted"). Stroke 3's re-synthesis
# prompt embeds scenario + truth packets + Stroke 1 + Stroke 2 audit + mission
# framing — combined size routinely exceeds the cap when Stroke 1 and 2 are
# injected verbatim. Structural extraction (FINAL RESOLUTION from Stroke 1 +
# audit category headers from Stroke 2) keeps the load-bearing content while
# staying under the cap. Both budgets are env-tunable for tuning + future
# adjustment if the cap moves.
#
# Total budget headroom: scenario (~200) + packets (~500) + S1 budget +
# S2 budget + mission framing (~700) should sum to under 5,000.
# ---------------------------------------------------------------------------

_S1_INJECTION_BUDGET = int(os.environ.get("GANYMEDE_S1_INJECTION_BUDGET", "1800"))
_S2_INJECTION_BUDGET = int(os.environ.get("GANYMEDE_S2_INJECTION_BUDGET", "1500"))
# Bicameral Convergence Level 1 — when Bridge is wired into the iterate loop,
# we split the prior single audit budget into Auditor + Bridge slots. Auditor
# tends to produce ~2,400 chars of four-category enumeration; Bridge produces
# ~700-1,000 chars of connection enumeration on observed runs (Amnesia, LMArena).
# 900 / 600 reflects that ratio while keeping the total at the historic 1,500
# combined audit budget so Stroke 3's overall prompt size stays under cap.
_S2_AUDITOR_BUDGET = int(os.environ.get("GANYMEDE_S2_AUDITOR_BUDGET", "900"))
_S2_BRIDGE_BUDGET = int(os.environ.get("GANYMEDE_S2_BRIDGE_BUDGET", "600"))


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


TRIAGE_TEMPLATE_STRUCTURED = """\
SITUATION INGESTION: {scenario}

MISSION:
Perform a 9D Strategic Breakdown of this situation. Identify the core
subjects, entities, and dimensions involved.

After the breakdown, produce a Strategic Hit List of research subjects
for our PKI Oracle swarm. Each subject becomes its own deep-research
Oracle. To prevent swarm sprawl, LIMIT to the top {max_subjects} most
critical high-impact subjects.

OUTPUT FORMAT (MANDATORY):
First, your free-form 9D Strategic Breakdown as prose.

Then, AT THE END of your response, emit the Hit List as a JSON object
delimited EXACTLY by the markers shown — no markdown fences, no
extra prose between markers:

<HIT_LIST_JSON>
{{"subjects":[
  {{"name":"<3-7 word subject label>","surgical_prompt":"<plain-language research question — 1-3 sentences, what facts to gather and from what domain. NO 9D jargon (no ROEM, DAP, SDS, Strategic Lasso, Convergence Theorem) — phrase it the way you would ask a research assistant.>"}}
]}}
</HIT_LIST_JSON>

The JSON must contain EXACTLY {max_subjects} subject objects. The
surgical_prompt for each must be plain English suitable for a research
assistant — names of entities to research, factual questions to answer,
domains to consult. The Deep Research engine reads these prompts
verbatim; jargon will produce empty results.
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

    async def _cleanup_failed_oracle(self, notebook_id: str) -> None:
        """Best-effort delete of a failed oracle's notebook.

        Run after Deep Research or harvest fails inside :meth:`run_universal_loop`
        so the dead notebook does not clutter the user's NotebookLM dashboard
        (counting against quota with no truth packet to show for it).

        Errors are swallowed — cleanup failure must not cascade into the
        parent flow's exception handling.  The delete itself goes through
        the cooldown gate.
        """
        try:
            await self.svc.delete_notebook(notebook_id)
            logger.info("Cleaned up failed oracle notebook %s", notebook_id)
        except Exception as exc:
            logger.warning(
                "Could not delete failed oracle notebook %s: %s",
                notebook_id, exc,
            )

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
        # P1-03b: strip trailing CTA paragraph if the substrate leaked one
        # despite the persona's prohibition. cleaned == raw when no CTA;
        # consumers prefer cleaned_response when it's distinct from raw.
        cleaned, stripped_cta = _strip_trailing_cta(raw)
        cleaned_response = cleaned if stripped_cta is not None else None
        if stripped_cta is not None:
            logger.info(
                "Session %s stroke %d: stripped trailing CTA (%d chars)",
                session.id, stroke_number, len(stripped_cta),
            )

        stroke = StrokeResult(
            stroke_number=stroke_number,
            pathway=session.pathway,
            raw_response=raw,
            # Structured-field extraction (strategic_lasso, etc.) is
            # deliberately deferred — Engine response formatting varies
            # too much for hardcoded extraction to be reliable. raw_response
            # is the source of truth; consumers display it directly.
            final_resolution=raw,
            cleaned_response=cleaned_response,
            stripped_cta=stripped_cta,
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

    async def run_audit_stroke(
        self,
        session: Session,
        *,
        target_text: Optional[str] = None,
        scenario_context: Optional[str] = None,
    ) -> StrokeResult:
        """Run one audit stroke against the Mirror Auditor.

        The Mirror Auditor is the second 9D-Chess instance, persona-locked
        for fault-finding (see ``docs/protocols/Mirror_Auditor_Persona.md``).
        It enumerates four categories of faults in the supplied analysis
        text without producing a counter-strategy.

        Args:
            session: the active Session. Audit is recorded as the next
                stroke in sequence.
            target_text: the analysis text to audit. If None, defaults to
                the most recent stroke's ``raw_response`` (the natural
                Stroke 1 → Stroke 2 audit pattern).
            scenario_context: optional context describing the original
                scenario the analysis was responding to. Helps the
                auditor evaluate whether the analysis fits the scenario.
                If None, derived from session.scenario.

        The recorded StrokeResult has ``pathway=MIRROR_AUDIT`` regardless
        of the session's primary pathway, since this stroke went to the
        auditor instance, not the canonical Engine.
        """
        if session.status != "running":
            raise RuntimeError(
                f"Session {session.id} is not running (status={session.status})"
            )
        if target_text is None:
            if not session.strokes:
                raise ValueError(
                    f"Session {session.id}: cannot audit — no prior stroke "
                    f"to audit and no target_text supplied"
                )
            target_text = session.strokes[-1].raw_response
        if scenario_context is None:
            try:
                scenario_context = scenario_to_synthesis_text(
                    session.scenario, session.pathway
                )
            except ValueError:
                # MIRROR_AUDIT-pathway sessions don't have a synthesizable
                # scenario; fall back to whatever's in prior_resolution
                # or extra_context.
                scenario_context = (
                    session.scenario.prior_resolution
                    or session.scenario.extra_context
                    or "(no scenario context provided)"
                )

        stroke_number = len(session.strokes) + 1
        await session.emit(
            SessionEventType.STROKE_STARTED,
            payload={"kind": "audit", "auditing_stroke": stroke_number - 1 or None},
            stroke_number=stroke_number,
        )

        prompt = AUDIT_TEMPLATE.format(
            scenario_context=scenario_context.strip(),
            analysis_under_audit=target_text.strip(),
        )

        started = utcnow()
        logger.info(
            "Session %s stroke %d: audit %d-char target",
            session.id, stroke_number, len(target_text),
        )
        try:
            raw = await self.svc.query_mirror_auditor(prompt)
        except Exception as exc:
            await session.fail(str(exc), exc_type=type(exc).__name__)
            raise

        completed = utcnow()
        # P1-03b: strip trailing CTA paragraph (audit strokes typically
        # don't leak CTAs since the Auditor persona is stricter, but apply
        # for symmetry — the helper is conservative and won't false-positive).
        cleaned, stripped_cta = _strip_trailing_cta(raw)
        cleaned_response = cleaned if stripped_cta is not None else None
        if stripped_cta is not None:
            logger.info(
                "Session %s stroke %d (auditor): stripped trailing CTA (%d chars)",
                session.id, stroke_number, len(stripped_cta),
            )

        stroke = StrokeResult(
            stroke_number=stroke_number,
            pathway=Pathway.MIRROR_AUDIT,
            raw_response=raw,
            audit_findings=_parse_audit_findings(raw),
            audit_kind="mirror_auditor",
            cleaned_response=cleaned_response,
            stripped_cta=stripped_cta,
            started_at=started,
            completed_at=completed,
        )
        await session.record_stroke(stroke)
        await session.emit(
            SessionEventType.SYNTHESIS_COMPLETE,
            payload={
                "stroke_number": stroke_number,
                "response_chars": len(raw),
                "kind": "audit",
                "fault_count": len(stroke.audit_findings or []),
            },
            stroke_number=stroke_number,
        )
        await session.emit(
            SessionEventType.STROKE_COMPLETED,
            payload={"duration_seconds": stroke.duration_seconds},
            stroke_number=stroke_number,
        )
        return stroke

    async def audit_with_bridge(
        self,
        session: Session,
        bridge_notebook_id: str,
        *,
        target_text: Optional[str] = None,
        scenario_context: Optional[str] = None,
        fail_session_on_error: bool = True,
    ) -> StrokeResult:
        """Run one audit stroke against the Connection Bridge.

        Bicameral Convergence Level 1 — the orchestrator method that has
        been pending since milestone 33. Structural sibling of
        :meth:`run_audit_stroke` but uses the Connection Bridge persona
        (applied per-call via ``configure_connection_bridge``) on a
        caller-supplied non-canonical notebook. The Bridge enumerates
        *missed connections* between Truth Packets that the Engine's
        synthesis didn't draw — an orthogonal lens to the Mirror
        Auditor's fault-mode enumeration.

        See ``docs/concepts/Bicameral_Convergence.md`` for the architectural
        framing and ``docs/protocols/Connection_Bridge_Persona.md`` for the
        Bridge persona itself. Level 1 was validated on the Amnesia
        substrate 2026-05-22 (3 missed bridges, entirely orthogonal to the
        Mirror Auditor's findings on the same scenario) — this method is
        the productionisation of that validation.

        Caller responsibilities (NOT handled by this method):
            * ``bridge_notebook_id`` must be a non-canonical notebook with
              the foundations corpus + the scenario's Truth Packets already
              loaded (the same substrate the Engine reasoned over). Setup
              flow: create notebook via ``svc.create_notebook``, upload
              foundations + Truth Packets via ``svc.upload_source``, then
              pass the resulting ID here.
            * The notebook is NOT automatically deleted. Caller manages
              lifecycle (typically: create per-session, audit, delete via
              ``svc.delete_notebook``).
            * Passing one of the canonical notebook IDs (Engine, Auditor,
              Legacy) raises ValueError — the Bridge persona cannot be
              written to canonical notebooks (per the protected-ID
              contract in ``notebooklm/client.py:configure_persona``).

        Args:
            session: the active Session. Bridge audit is recorded as the
                next stroke in sequence.
            bridge_notebook_id: notebook ID with foundations + scenario
                Truth Packets loaded; Bridge persona will be (re-)applied.
            target_text: the analysis text to bridge-audit. If None,
                defaults to the most recent stroke's ``raw_response``
                (the natural Stroke 1 → Bridge audit pattern).
            scenario_context: optional context describing the original
                scenario. Defaults to derived from ``session.scenario``.

        Returns:
            StrokeResult with ``pathway=MIRROR_AUDIT`` (structurally an
            audit stroke, same as Mirror Auditor stroke). Distinguishable
            from Mirror Auditor strokes by inspection of ``raw_response``
            (Bridge enumerates connections, Auditor enumerates fault
            categories). ``audit_findings`` is left None — the four-
            category parser doesn't apply to Bridge output.

        Operational cost notes:
            One NotebookLM query call (gated by the cooldown). Setup cost
            (creating the notebook + uploading foundations + Truth Packets)
            is borne by the caller and is typically ~15+ NotebookLM calls
            with the current 8s cooldown — budget accordingly. For ad-hoc
            single audits, this is meaningful overhead; for long-lived
            scenarios where the same Bridge notebook is reused across
            many audits, amortises well.
        """
        if session.status != "running":
            raise RuntimeError(
                f"Session {session.id} is not running (status={session.status})"
            )

        # Guard against accidentally applying Bridge persona to a canonical
        # notebook. The persona-config endpoint blocks this anyway, but
        # catching it here gives a clearer error message.
        canonicals = {
            self.svc.CHESS_ENGINE_ID,
            self.svc.MIRROR_AUDITOR_ID,
            self.svc.LEGACY_ENGINE_ID,
        }
        if bridge_notebook_id in canonicals:
            raise ValueError(
                f"Bridge cannot be applied to canonical notebook "
                f"{bridge_notebook_id}. Create a separate notebook with the "
                f"foundations corpus + scenario Truth Packets loaded; pass "
                f"that notebook's ID."
            )

        if target_text is None:
            if not session.strokes:
                raise ValueError(
                    f"Session {session.id}: cannot bridge-audit — no prior "
                    f"stroke to audit and no target_text supplied"
                )
            target_text = session.strokes[-1].raw_response
        if scenario_context is None:
            try:
                scenario_context = scenario_to_synthesis_text(
                    session.scenario, session.pathway
                )
            except ValueError:
                scenario_context = (
                    session.scenario.prior_resolution
                    or session.scenario.extra_context
                    or "(no scenario context provided)"
                )

        stroke_number = len(session.strokes) + 1
        await session.emit(
            SessionEventType.STROKE_STARTED,
            payload={
                "kind": "bridge_audit",
                "auditing_stroke": stroke_number - 1 or None,
                "bridge_notebook_id": bridge_notebook_id,
            },
            stroke_number=stroke_number,
        )

        # Re-apply Bridge persona (idempotent). This is the lever that
        # makes the supplied notebook BE a Bridge for the duration of
        # this call — without it, the notebook would respond per whatever
        # persona was last configured on it.
        await self.svc.configure_connection_bridge(bridge_notebook_id)

        prompt = BRIDGE_AUDIT_TEMPLATE.format(
            scenario_context=scenario_context.strip(),
            analysis_under_audit=target_text.strip(),
        )

        started = utcnow()
        logger.info(
            "Session %s stroke %d: bridge-audit %d-char target on notebook %s",
            session.id, stroke_number, len(target_text), bridge_notebook_id,
        )
        try:
            raw = await self.svc.query_notebook(bridge_notebook_id, prompt)
        except Exception as exc:
            # fail_session_on_error=False is used by run_iterative_engine
            # where Bridge is an OPTIONAL stroke — a Bridge failure should
            # fall back to historic Auditor-only 3-stroke rather than kill
            # the whole iterate run (and the WS subscribers' connections).
            # The /bridge-audit standalone endpoint keeps the default
            # (True) so its caller sees a clean session-fail on errors.
            if fail_session_on_error:
                await session.fail(str(exc), exc_type=type(exc).__name__)
            raise

        completed = utcnow()
        # P1-03b: strip trailing CTA paragraph (Bridge output occasionally
        # follows persona-deviating CTA patterns; safe to apply since the
        # helper only strips when the LAST paragraph starts with a
        # canonical CTA opener).
        cleaned, stripped_cta = _strip_trailing_cta(raw)
        cleaned_response = cleaned if stripped_cta is not None else None
        if stripped_cta is not None:
            logger.info(
                "Session %s stroke %d (bridge): stripped trailing CTA (%d chars)",
                session.id, stroke_number, len(stripped_cta),
            )

        stroke = StrokeResult(
            stroke_number=stroke_number,
            pathway=Pathway.MIRROR_AUDIT,  # structurally an audit stroke
            raw_response=raw,
            # Bridge output is connection-enumeration, not fault-category
            # enumeration. The _parse_audit_findings four-category parser
            # doesn't apply — leave audit_findings None and let consumers
            # read raw_response directly.
            audit_kind="bridge",
            cleaned_response=cleaned_response,
            stripped_cta=stripped_cta,
            started_at=started,
            completed_at=completed,
        )
        await session.record_stroke(stroke)
        await session.emit(
            SessionEventType.SYNTHESIS_COMPLETE,
            payload={
                "stroke_number": stroke_number,
                "response_chars": len(raw),
                "kind": "bridge_audit",
            },
            stroke_number=stroke_number,
        )
        await session.emit(
            SessionEventType.STROKE_COMPLETED,
            payload={"duration_seconds": stroke.duration_seconds},
            stroke_number=stroke_number,
        )
        return stroke

    async def provision_bridge_notebook(
        self,
        truth_packets: list[TruthPacket],
        *,
        title: Optional[str] = None,
        include_foundations: bool = True,
        foundations_dir: Optional[Path] = None,
        session_id: Optional[str] = None,
        provision_path: str = "standalone_provision",
    ) -> dict[str, Any]:
        """Create + populate + persona-lock a Connection Bridge notebook.

        End-to-end Bridge-notebook provisioning bundled as one async call.
        Same logic as the ``POST /api/v2/bridge/provision`` endpoint, but
        callable from inside the orchestrator (specifically from
        :meth:`run_iterative_engine` when it needs to auto-provision before
        Stroke 2b).

        Steps:
          1. Create a new (non-canonical) NotebookLM notebook.
          2. Upload ``docs/foundations/`` corpus (every .md/.pdf/.txt
             except README.md) when ``include_foundations=True``.
          3. Write each Truth Packet to a temp .md and upload it as a
             source (so the Bridge notebook reasons over the same
             substrate as the Engine).
          4. Apply the Connection Bridge persona via
             :meth:`NotebookLMService.configure_connection_bridge`.

        Returns a dict shaped like the v2 /bridge/provision task result:
        ``{notebook_id, title, foundations_uploaded, truth_packets_uploaded,
        sources_total, bridge_persona_applied}``.

        Operational cost: ~14 cooldown-gated NotebookLM calls (1 create +
        13 foundation files + N truth packets + 1 persona apply). With the
        8s cooldown floor this is typically 3-5 minutes wall time. Caller
        is responsible for the notebook lifecycle afterward (cleanup via
        :meth:`NotebookLMService.delete_notebook` if single-use).

        Raises:
            RuntimeError: if ``include_foundations=True`` and the
                foundations directory can't be located.
        """
        title = (
            title or f"Bridge — {truth_packets[0].subject[:60]}"
        )[:200]

        # Resolve foundations dir — fail fast if missing and required.
        resolved_foundations: Optional[Path] = None
        if include_foundations:
            if foundations_dir is not None:
                resolved_foundations = Path(foundations_dir)
            elif env := os.environ.get("GANYMEDE_FOUNDATIONS_DIR"):
                resolved_foundations = Path(env)
            else:
                # Default: docs/foundations/ relative to this file.
                # __file__ = .../ganymede-backend/app/services/orchestrator.py
                # parents:  0=services 1=app 2=ganymede-backend 3=Project Ganymede
                resolved_foundations = (
                    Path(__file__).resolve().parents[3]
                    / "docs" / "foundations"
                )
            if not resolved_foundations.is_dir():
                raise RuntimeError(
                    f"Foundations directory not found: {resolved_foundations}. "
                    f"Set GANYMEDE_FOUNDATIONS_DIR or pass foundations_dir."
                )

        notebook_id = await self.svc.create_notebook(title)
        logger.info(
            "provision_bridge_notebook: created notebook %s (title=%r)",
            notebook_id, title,
        )

        foundations_uploaded = 0
        if resolved_foundations is not None:
            # Upload .md / .pdf / .txt in sorted order, skip README.md
            # (which is a meta-description of the corpus, not part of it).
            uploadable = [
                p for p in sorted(resolved_foundations.iterdir())
                if p.is_file()
                and p.suffix.lower() in {".md", ".pdf", ".txt"}
                and p.name.lower() != "readme.md"
            ]
            for file_path in uploadable:
                logger.info(
                    "provision_bridge_notebook: uploading foundation %s (%d/%d)",
                    file_path.name,
                    foundations_uploaded + 1,
                    len(uploadable),
                )
                await self.svc.upload_file(notebook_id, str(file_path))
                foundations_uploaded += 1

        # Truth Packets: write each to a temp .md, upload, clean up at end.
        packets_uploaded = 0
        with tempfile.TemporaryDirectory(prefix="ganymede_bridge_packets_") as tmpdir:
            tmpdir_path = Path(tmpdir)
            for i, tp in enumerate(truth_packets, start=1):
                # Build a safe filename from the subject; cap length.
                safe = "".join(
                    c if c.isalnum() or c in "._- " else "_" for c in tp.subject
                ).strip()[:80] or f"packet_{i}"
                tmp_path = tmpdir_path / f"{safe}.md"
                content = (
                    f"# {tp.subject}\n\n"
                    f"Source: {tp.source_label or 'unspecified'}\n\n"
                    f"{tp.content}\n"
                )
                tmp_path.write_text(content, encoding="utf-8")
                logger.info(
                    "provision_bridge_notebook: uploading truth packet %r (%d/%d)",
                    tp.subject, i, len(truth_packets),
                )
                await self.svc.upload_file(notebook_id, str(tmp_path))
                packets_uploaded += 1

        logger.info(
            "provision_bridge_notebook: applying Bridge persona to %s",
            notebook_id,
        )
        await self.svc.configure_connection_bridge(notebook_id)

        logger.info(
            "provision_bridge_notebook: done. notebook=%s, foundations=%d, packets=%d",
            notebook_id, foundations_uploaded, packets_uploaded,
        )

        # P1-04: register in the in-memory Bridge notebook registry so the
        # operator-facing survey endpoint can list this notebook + suggest
        # an action. Registration is fire-and-forget; failure here would
        # mean the notebook exists but isn't tracked — not blocking.
        try:
            bridge_notebook_registry().register(
                notebook_id=notebook_id,
                title=title,
                session_id=session_id,
                provision_path=provision_path,
                foundations_uploaded=foundations_uploaded,
                truth_packets_uploaded=packets_uploaded,
            )
        except Exception:
            logger.exception(
                "provision_bridge_notebook: registry registration failed for %s "
                "(non-blocking — notebook exists)",
                notebook_id,
            )

        return {
            "notebook_id": notebook_id,
            "title": title,
            "foundations_uploaded": foundations_uploaded,
            "truth_packets_uploaded": packets_uploaded,
            "sources_total": foundations_uploaded + packets_uploaded,
            "bridge_persona_applied": True,
        }

    async def run_translation(
        self,
        session: Session,
        stroke_number: int,
        register: str,
    ) -> str:
        """Pl3 Operator Lens — translate one of the session's strokes into a register.

        Architectural call (corrected post-milestone 45): translation
        is routed through the canonical NotebookLM Engine (NOT Gemini
        Flash) so the model has the foundations-corpus grounding to
        understand what the framework concepts ACTUALLY MEAN when
        translating. This preserves the project's closed-RAG-sphere
        design principle (Gemini is scoped to dispatcher intent
        classification only; everything analytical lives in the closed
        sphere) and matches what made the milestone 43 Cube-of-Space
        exchange work in the first place — the notebook produced
        visceral geometric vocabulary because the grounded model
        understood the underlying structural primitives.

        Looks up the stroke by stroke_number, builds a register-specific
        translation prompt (from ``TRANSLATION_PROMPT_TEMPLATES``) with
        the stroke's ``cleaned_response`` or ``raw_response`` as the
        source, calls the canonical Engine via
        ``self.svc.query_chess_engine``, records the result on the
        session, and returns it.

        Operational cost: one cooldown-gated NotebookLM call per
        translation (~30-50s wall — same speed as a normal synthesis
        stroke). Source-plus-framing typically lands at 3-5k chars,
        well under the NotebookLM input-size cap.

        Args:
            session: the session containing the stroke to translate.
            stroke_number: the stroke to translate (1-indexed).
            register: one of ``TRANSLATION_REGISTERS``.

        Returns:
            The translated text. Also recorded on
            ``session._translations`` for future retrieval.

        Raises:
            ValueError: if the stroke doesn't exist, the stroke has
                empty response text, or the register is invalid.
            RuntimeError: if the NotebookLM call fails — caller-visible.
        """
        if register not in TRANSLATION_REGISTERS:
            raise ValueError(
                f"Unknown translation register: {register!r}. "
                f"Choose one of: {', '.join(TRANSLATION_REGISTERS)}"
            )

        # Find the stroke by number
        target_stroke = None
        for s in session.strokes:
            if s.stroke_number == stroke_number:
                target_stroke = s
                break
        if target_stroke is None:
            raise ValueError(
                f"Session {session.id}: stroke {stroke_number} not found "
                f"(have {len(session.strokes)} strokes)"
            )

        # Prefer cleaned_response (post-P1-03b strip) when it's distinct from
        # raw_response — that's what the operator was meant to read.
        source = target_stroke.cleaned_response or target_stroke.raw_response
        if not source or not source.strip():
            raise ValueError(
                f"Session {session.id}: stroke {stroke_number} has empty "
                f"response — nothing to translate"
            )

        # Build the register-specific prompt with the source text injected.
        # Escape literal { } in the source so the .replace() below stays
        # safe even if the Engine's prior output contains framework jargon
        # like "{DAI}" / "{ROEM}" literally (P1-03b's pattern from
        # run_iterative_engine — defensive copy of the same escape).
        source_escaped = source.replace("{", "{{").replace("}", "}}")
        template = TRANSLATION_PROMPT_TEMPLATES[register]
        prompt = template.replace("{source_text}", source_escaped)

        logger.info(
            "Session %s: translating stroke %d (%d chars source, %d chars prompt) "
            "into register %r via canonical Engine",
            session.id, stroke_number, len(source), len(prompt), register,
        )

        try:
            translated = await self.svc.query_chess_engine(prompt)
        except Exception as exc:
            logger.exception(
                "Session %s: translation Engine call failed for stroke %d register %r",
                session.id, stroke_number, register,
            )
            raise RuntimeError(
                f"Translation failed for stroke {stroke_number} register {register}: "
                f"{type(exc).__name__}: {exc}"
            ) from exc

        if not translated or not translated.strip():
            raise RuntimeError(
                f"Translation returned empty for stroke {stroke_number} "
                f"register {register} (possible NotebookLM silent rejection — "
                f"check the prompt size against the ~5-6k char cap)"
            )

        # P1-03b: strip trailing CTA from the translation too — the Engine's
        # persona occasionally leaks CTAs even in translation mode.
        cleaned_translation, stripped_cta = _strip_trailing_cta(translated)
        if stripped_cta is not None:
            logger.info(
                "Session %s: stripped trailing CTA from translation (%d chars)",
                session.id, len(stripped_cta),
            )
            translated = cleaned_translation

        # Persist on session state for future retrieval.
        await session.record_translation(
            stroke_number=stroke_number,
            register=register,
            translated_text=translated,
        )

        logger.info(
            "Session %s: stroke %d translated (%d → %d chars) register=%r",
            session.id, stroke_number, len(source), len(translated), register,
        )

        return translated

    def _check_cancelled(self, session: Session, where: str) -> None:
        """Raise :class:`SessionCancelledError` if the session has been cancelled.

        Called at NotebookLM-call boundaries inside long-running loop
        methods so the operator's ``POST /api/v2/sessions/{id}/cancel``
        terminates the loop at the next natural yield point rather than
        waiting for the next NotebookLM call to return (which can be
        30s+ on the cooldown gate). Cheap — bool read, atomic under GIL.

        ``where`` is a short string naming the check point for log
        traceability (e.g. ``"before-stroke-1"``, ``"before-bridge-provision"``).
        """
        if session.cancel_requested:
            logger.info(
                "Session %s: cancellation observed at %s — aborting loop",
                session.id, where,
            )
            raise SessionCancelledError(where=where, session_id=session.id)

    async def run_iterative_engine(
        self,
        session: Session,
        truth_packets: list[TruthPacket],
        *,
        max_strokes: int = 3,
        include_bridge: bool = True,
        bridge_notebook_id: Optional[str] = None,
    ) -> list[StrokeResult]:
        """Run the full Iterative Engine multi-stroke loop on a session.

        With ``include_bridge=True`` (default — Bicameral Convergence Level 1
        as production audit shape):
            Stroke 1: synthesis (canonical Engine)
            Stroke 2: Mirror Auditor reviews Stroke 1
            Stroke 2b: Connection Bridge audits Stroke 1 (orthogonal lens)
            Stroke 3: re-synthesis with BOTH audits as friction

        With ``include_bridge=False`` (historic shape):
            Stroke 1: synthesis (canonical Engine)
            Stroke 2: Mirror Auditor reviews Stroke 1
            Stroke 3: re-synthesis with Auditor-only friction

        Stops at ``max_strokes``. With Bridge enabled, ``max_strokes=4``
        runs the full bicameral loop; lower values stop earlier
        (1=synth-only, 2=synth+auditor, 3=synth+auditor+bridge,
        4=synth+auditor+bridge+resynth). Without Bridge, ``max_strokes=3``
        is the full thesis-antithesis-synthesis cycle.

        When ``include_bridge=True`` and ``bridge_notebook_id=None``, the
        orchestrator auto-provisions a Bridge notebook inline via
        :meth:`provision_bridge_notebook`. This adds ~3-5 min of wall time
        (14 cooldown-gated NotebookLM calls) to the iterate response. Reuse
        a Bridge notebook across runs by passing its ID to skip provisioning.

        The session must be created with ``iterative=True`` and
        ``max_strokes >= 2`` (or ``>= 3`` for Bridge) for this to run
        usefully.

        Returns the list of all StrokeResults produced. Caller invokes
        :meth:`Session.complete` afterward to finalize.
        """
        if not session.iterative:
            raise ValueError(
                f"Session {session.id} is not iterative — use "
                f"run_synthesis_stroke for single-pass."
            )
        if max_strokes < 1 or max_strokes > session.max_strokes:
            raise ValueError(
                f"max_strokes ({max_strokes}) must be 1..{session.max_strokes}"
            )

        # With Bridge wired in we have one extra stroke slot (Auditor +
        # Bridge before re-synthesis instead of just Auditor). Adjust the
        # re-synthesis stroke index accordingly so callers can pass
        # max_strokes=3 for "stop before re-synthesis" with Bridge on.
        if include_bridge:
            # 1=S1, 2=Auditor, 3=Bridge, 4=re-synth
            resynth_at = 4
            bridge_at = 3
        else:
            # 1=S1, 2=Auditor, 3=re-synth
            resynth_at = 3
            bridge_at = None

        results: list[StrokeResult] = []

        # Cancel check before Stroke 1. Cheap; catches the case where the
        # operator cancelled after session creation but before any work.
        self._check_cancelled(session, "before-stroke-1")

        # Stroke 1: thesis
        s1 = await self.run_synthesis_stroke(session, truth_packets)
        results.append(s1)
        if max_strokes < 2:
            return results

        # Cancel check before Stroke 2. Stroke 1 may have taken 30-50s on
        # the gate; the operator may have hit cancel during that window.
        self._check_cancelled(session, "before-stroke-2")

        # Stroke 2: antithesis (Mirror Auditor)
        s2 = await self.run_audit_stroke(session)
        results.append(s2)

        # Stroke 2b (only with include_bridge=True): orthogonal-lens audit
        # via the Connection Bridge. Bridge gets the same Stroke 1 as the
        # Auditor — both lenses fire on the same target, in parallel-in-spirit
        # (but serial in execution to respect the cooldown gate).
        s2b: Optional[StrokeResult] = None
        if include_bridge and max_strokes >= bridge_at:
            # Cancel check before the slowest path in the loop —
            # auto-provisioning a Bridge notebook is ~3-5 min wall time
            # and 14 NotebookLM calls. Worth bailing here before kicking
            # it off.
            self._check_cancelled(session, "before-bridge-provision")
            try:
                if bridge_notebook_id is None:
                    # Auto-provision. This is the slow path — ~3-5 min added
                    # to the iterate response. Documented in the v2 API doc.
                    logger.info(
                        "Session %s: auto-provisioning Bridge notebook for Stroke 2b",
                        session.id,
                    )
                    provision_result = await self.provision_bridge_notebook(
                        truth_packets=truth_packets,
                        title=f"Bridge — {session.id[:8]} iterate",
                        session_id=session.id,
                        provision_path="iterate_level_1",
                    )
                    bridge_notebook_id = provision_result["notebook_id"]
                    logger.info(
                        "Session %s: Bridge notebook %s ready (%d foundations, %d packets)",
                        session.id,
                        bridge_notebook_id,
                        provision_result["foundations_uploaded"],
                        provision_result["truth_packets_uploaded"],
                    )

                # Cancel check before the Bridge audit query — provisioning
                # may have taken ~3 min if it ran; check before kicking the
                # final NotebookLM call in the Bridge slot.
                self._check_cancelled(session, "before-stroke-2b-bridge")

                # Bridge audits Stroke 1 — same target as the Auditor, so we
                # pass target_text=s1.raw_response explicitly (otherwise the
                # default-to-last-stroke logic would point at Stroke 2's text,
                # which is not what we want). fail_session_on_error=False so
                # a Bridge transient falls back to Auditor-only Stroke 3
                # rather than killing the whole iterate run.
                s2b = await self.audit_with_bridge(
                    session,
                    bridge_notebook_id=bridge_notebook_id,
                    target_text=s1.raw_response,
                    fail_session_on_error=False,
                )
                results.append(s2b)
            except SessionCancelledError:
                # Operator cancelled mid-Bridge. Re-raise so the loop
                # terminates cleanly with the partial result list. Do NOT
                # treat as "Bridge transient" — that masks the operator's
                # intent.
                raise
            except Exception:
                # Bridge failures (either provisioning or audit query) must
                # not kill the iterate run. Log and continue with
                # auditor-only friction for Stroke 3 — the historic
                # Iterative Engine shape is the graceful fallback.
                logger.exception(
                    "Session %s: Bridge stroke failed — continuing with "
                    "Auditor-only friction for Stroke 3.",
                    session.id,
                )
                s2b = None

        if max_strokes < resynth_at:
            return results

        # Skip Stroke 3 when Stroke 2 produced empty content. The
        # ITERATIVE_RESYNTHESIS_TEMPLATE injects Stroke 2's text as
        # the audit-findings section — an empty audit would produce
        # "AUDIT FINDINGS:\n=====\n\n=====" asking the Engine to
        # integrate nothing. The prompt would also still embed Stroke 1
        # verbatim, putting the combined size at risk of NotebookLM's
        # input cap regardless. Surface the partial 2-stroke result and
        # let the caller decide via the empty-stroke warning UI.
        if not s2.raw_response.strip():
            logger.warning(
                "Session %s: Stroke 2 returned empty audit (likely NotebookLM "
                "input-size cap on Stroke-1-as-audit-target). Skipping Stroke 3 "
                "— no friction to inject. Iterative loop completes early; "
                "the empty-stroke UI warning will surface this to the operator.",
                session.id,
            )
            return results

        # Stroke 3: re-synthesis with audit friction. Template + budget
        # depend on whether Bridge fired.
        bridge_in_loop = include_bridge and s2b is not None and s2b.raw_response.strip()

        # Structural extraction to keep the Stroke 3 prompt under the
        # NotebookLM input cap (~5,100-6,000 chars; see Run 06's third-
        # run diagnosis). Stroke 1's load-bearing content is its FINAL
        # RESOLUTION section (the conclusion the audits were critiquing)
        # plus any evidence-limitation notice it self-flagged at the head;
        # the per-dimension breakdown is well-covered by the audit text.
        s1_extracted = _extract_for_resynthesis(s1.raw_response, max_chars=_S1_INJECTION_BUDGET)

        if bridge_in_loop:
            # Bicameral: split the audit budget into Auditor + Bridge slots.
            auditor_extracted = _truncate_audit_for_injection(
                s2.raw_response, max_chars=_S2_AUDITOR_BUDGET,
            )
            bridge_extracted = _truncate_bridge_for_injection(
                s2b.raw_response, max_chars=_S2_BRIDGE_BUDGET,
            )
            logger.info(
                "Session %s Stroke 3 (bicameral) injection budgets: "
                "S1 %d→%d (budget %d), Auditor %d→%d (budget %d), "
                "Bridge %d→%d (budget %d)",
                session.id,
                len(s1.raw_response), len(s1_extracted), _S1_INJECTION_BUDGET,
                len(s2.raw_response), len(auditor_extracted), _S2_AUDITOR_BUDGET,
                len(s2b.raw_response), len(bridge_extracted), _S2_BRIDGE_BUDGET,
            )
            framing = ITERATIVE_BICAMERAL_RESYNTHESIS_TEMPLATE
            # Escape any literal { } in the extracted stroke text before
            # injection — synthesize() will call .format() on the framing,
            # so unescaped framework jargon like "{DAI}" or "{ROEM}" in the
            # Engine's response would otherwise raise KeyError.
            s1_escaped = s1_extracted.replace("{", "{{").replace("}", "}}")
            auditor_escaped = auditor_extracted.replace("{", "{{").replace("}", "}}")
            bridge_escaped = bridge_extracted.replace("{", "{{").replace("}", "}}")
            framing_filled = (
                framing
                .replace("{stroke_1_response}", s1_escaped)
                .replace("{audit_findings}", auditor_escaped)
                .replace("{bridge_findings}", bridge_escaped)
            )
        else:
            # Historic shape: Auditor-only friction.
            s2_extracted = _truncate_audit_for_injection(
                s2.raw_response, max_chars=_S2_INJECTION_BUDGET,
            )
            logger.info(
                "Session %s Stroke 3 injection budgets: S1 %d→%d chars (budget %d), "
                "S2 %d→%d chars (budget %d)",
                session.id,
                len(s1.raw_response), len(s1_extracted), _S1_INJECTION_BUDGET,
                len(s2.raw_response), len(s2_extracted), _S2_INJECTION_BUDGET,
            )
            framing = ITERATIVE_RESYNTHESIS_TEMPLATE
            s1_escaped = s1_extracted.replace("{", "{{").replace("}", "}}")
            s2_escaped = s2_extracted.replace("{", "{{").replace("}", "}}")
            framing_filled = (
                framing
                .replace("{stroke_1_response}", s1_escaped)
                .replace("{audit_findings}", s2_escaped)
            )

        # Cancel check before Stroke 3 — the audits may have taken ~80s
        # combined; cancel during that window should fire here.
        self._check_cancelled(session, "before-stroke-3")

        s3 = await self.run_synthesis_stroke(
            session, truth_packets, framing=framing_filled,
        )
        results.append(s3)
        return results

    # =====================================================================
    # Bicameral Convergence Level 2 — closed-loop mirror-bounce.
    #
    # Per docs/concepts/Bicameral_Convergence.md, Level 2 is the iterative
    # Engine ↔ Bridge loop: Engine synthesizes → Bridge audits → if Bridge
    # surfaces NEW missed connections, Engine re-synthesizes with those
    # connections as friction → Bridge re-audits → ... until convergence
    # (no new bridges) or hard iteration cap.
    #
    # Distinct from run_iterative_engine (Level 1): that's a 3-stroke
    # thesis-antithesis-synthesis with single-pass audit. This is N-stroke
    # closed-loop convergence with only Bridge as the friction lens.
    #
    # Five mandatory operator control surfaces (per the architectural
    # spec): visual transparency (BICAMERAL_ITERATION_START/END events),
    # cancel endpoint (E1-01, observed at iteration boundaries), inter-
    # iteration delay (operator-tunable 2-30s, gives time to inspect),
    # hard iteration cap (operator-tunable 1-10, default 5), and operator
    # approval gate for new Oracle spawn (Level 3 only — stubbed here).
    # =====================================================================

    async def run_bicameral_loop(
        self,
        session: Session,
        truth_packets: list[TruthPacket],
        *,
        max_iterations: int = 5,
        min_inter_iteration_delay: float = 5.0,
        bridge_notebook_id: Optional[str] = None,
    ) -> list[StrokeResult]:
        """Run the closed-loop Bicameral Convergence Level 2 mirror-bounce.

        Each iteration: Engine synthesizes (with prior iteration's Bridge
        findings as friction, if any) → Bridge audits the new synthesis →
        convergence check. Loop terminates when no new STRUCTURAL/IMPLIED
        bridges are surfaced (clean convergence) or when ``max_iterations``
        is reached (hard cap).

        Convergence criteria for E1-03 scope:
            1. ``no_new_structural`` — Bridge audit produced zero
               STRUCTURAL/IMPLIED bridges in the most recent iteration.

        Additional criterion ``resolution_stable`` (Engine FINAL RESOLUTION
        text functionally unchanged across iterations) is deferred to E1-04
        which refines the convergence-detection helper. For E1-03, only the
        count-based criterion fires.

        Bridge notebook lifecycle:
            - If ``bridge_notebook_id`` is supplied, reused across all
              iterations (it has the same substrate; no re-provision needed).
            - Else auto-provisioned on iteration 1 (~3-5 min wall), then
              reused for every subsequent iteration's audit.

        Cancel handling:
            - Cancel-flag checked at each iteration boundary (top of
              iteration + after inter-iteration delay).
            - Cancel-flag also checked between Engine synthesis and Bridge
              audit within each iteration.
            - On cancel, :class:`SessionCancelledError` propagates out and
              the caller (HTTP endpoint or test harness) returns partial
              results from ``session.strokes``.

        Bridge transient handling:
            - If the Bridge stroke fails on any iteration (provisioning or
              audit query), the loop terminates early with current results
              + a warning log. Unlike Level 1's ``run_iterative_engine``
              which falls back to Auditor-only friction, Level 2 has no
              fallback lens — without Bridge findings there's no friction
              to re-synthesize against, so terminating gracefully is the
              right move.

        Args:
            session: must have ``iterative=True`` and ``max_strokes`` large
                enough to accommodate all expected strokes (2 per iteration,
                so ``max_strokes >= 2 * max_iterations`` for unconditional
                fit). The orchestrator does NOT enforce this hard cap —
                it relies on the session-level cap being permissive enough.
            truth_packets: the substrate the Engine synthesizes against
                (and Bridge audits over) every iteration.
            max_iterations: hard iteration cap. 1-10 inclusive. Default 5.
            min_inter_iteration_delay: seconds to sleep between iterations
                (after Bridge audit, before next Engine synthesis). 2-30s
                inclusive. Default 5s. Gives the operator time to inspect
                intermediate state via the WS stream + decide whether to
                cancel.
            bridge_notebook_id: pre-existing Bridge notebook to reuse.
                Optional. When None, auto-provisions on iteration 1.

        Returns:
            List of all StrokeResults produced. Length depends on how many
            iterations ran before convergence/cap: 2 per iteration (Engine
            + Bridge), except the final iteration on convergence which
            still includes both strokes (the converged synthesis + the
            audit that confirmed no new bridges).

        Raises:
            ValueError: bad arguments (non-iterative session, max_iterations
                out of range, delay out of range).
            SessionCancelledError: operator cancelled mid-loop.
        """
        # ---------------- input validation ----------------
        if not session.iterative:
            raise ValueError(
                f"Session {session.id} is not iterative — Bicameral Loop "
                f"requires iterative=True"
            )
        if max_iterations < 1 or max_iterations > 10:
            raise ValueError(
                f"max_iterations ({max_iterations}) must be 1..10"
            )
        if min_inter_iteration_delay < 2.0 or min_inter_iteration_delay > 30.0:
            raise ValueError(
                f"min_inter_iteration_delay ({min_inter_iteration_delay}) "
                f"must be 2.0..30.0 seconds"
            )

        results: list[StrokeResult] = []
        prior_synthesis: Optional[str] = None
        prior_bridge_findings: Optional[str] = None
        prior_bridge_count: int = 0

        logger.info(
            "Session %s: starting Bicameral Convergence Level 2 loop "
            "(max_iterations=%d, delay=%.1fs, bridge_notebook_id=%s)",
            session.id, max_iterations, min_inter_iteration_delay,
            bridge_notebook_id or "<auto-provision>",
        )

        for iteration in range(1, max_iterations + 1):
            self._check_cancelled(session, f"bicameral-iter-{iteration}-start")

            await session.emit(
                SessionEventType.BICAMERAL_ITERATION_START,
                payload={
                    "iteration": iteration,
                    "max_iterations": max_iterations,
                    "include_bridge": True,
                },
            )

            # ---------- Engine synthesis ----------
            if iteration == 1:
                # First iteration — no prior synthesis, default scenario framing.
                engine_stroke = await self.run_synthesis_stroke(
                    session, truth_packets,
                )
            else:
                # Subsequent iterations — Bicameral loop template with prior
                # synthesis + Bridge findings as friction. Structural extraction
                # to keep the prompt under the NotebookLM input cap.
                assert prior_synthesis is not None
                assert prior_bridge_findings is not None
                prior_extracted = _extract_for_resynthesis(
                    prior_synthesis, max_chars=_S1_INJECTION_BUDGET,
                )
                bridge_extracted = _truncate_bridge_for_injection(
                    prior_bridge_findings, max_chars=_S2_BRIDGE_BUDGET,
                )
                # Escape curly braces in extracted text — synthesize() does
                # .format() on the framing; literal {DAI}/{ROEM} in the
                # Engine's prior output would raise KeyError otherwise.
                prior_escaped = prior_extracted.replace("{", "{{").replace("}", "}}")
                bridge_escaped = bridge_extracted.replace("{", "{{").replace("}", "}}")
                framing = (
                    ITERATIVE_BICAMERAL_LOOP_TEMPLATE
                    .replace("{prior_synthesis}", prior_escaped)
                    .replace("{bridge_findings}", bridge_escaped)
                    .replace("{prior_iteration}", str(iteration - 1))
                    .replace("{current_iteration}", str(iteration))
                )
                logger.info(
                    "Session %s Bicameral iter %d injection budgets: "
                    "prior synthesis %d→%d (budget %d), Bridge %d→%d (budget %d)",
                    session.id, iteration,
                    len(prior_synthesis), len(prior_extracted), _S1_INJECTION_BUDGET,
                    len(prior_bridge_findings), len(bridge_extracted), _S2_BRIDGE_BUDGET,
                )
                engine_stroke = await self.run_synthesis_stroke(
                    session, truth_packets, framing=framing,
                )

            results.append(engine_stroke)

            self._check_cancelled(
                session, f"bicameral-iter-{iteration}-before-bridge",
            )

            # ---------- Bridge auto-provision (iteration 1 only) ----------
            if bridge_notebook_id is None:
                logger.info(
                    "Session %s Bicameral iter %d: auto-provisioning Bridge notebook",
                    session.id, iteration,
                )
                try:
                    provision_result = await self.provision_bridge_notebook(
                        truth_packets=truth_packets,
                        title=f"Bicameral Loop — {session.id[:8]}",
                        session_id=session.id,
                        provision_path="bicameral_loop_level_2",
                    )
                    bridge_notebook_id = provision_result["notebook_id"]
                    logger.info(
                        "Session %s Bicameral iter %d: Bridge notebook %s ready",
                        session.id, iteration, bridge_notebook_id,
                    )
                except SessionCancelledError:
                    raise
                except Exception:
                    logger.exception(
                        "Session %s Bicameral iter %d: Bridge provisioning failed; "
                        "terminating loop early with %d stroke(s).",
                        session.id, iteration, len(results),
                    )
                    return results

            # ---------- Bridge audit ----------
            try:
                bridge_stroke = await self.audit_with_bridge(
                    session,
                    bridge_notebook_id=bridge_notebook_id,
                    target_text=engine_stroke.raw_response,
                    fail_session_on_error=False,
                )
            except SessionCancelledError:
                raise
            except Exception:
                logger.exception(
                    "Session %s Bicameral iter %d: Bridge audit failed; "
                    "terminating loop early with %d stroke(s).",
                    session.id, iteration, len(results),
                )
                return results

            results.append(bridge_stroke)

            # ---------- Convergence detection (E1-04) ----------
            #
            # Two criteria, checked in priority order:
            #   1. no_new_structural — Bridge surfaced 0 STRUCTURAL/IMPLIED
            #      bridges (count-based, cheaper). Defended against
            #      non-canonical Bridge output by `_is_audit_substantive`:
            #      if the audit looks substantive even without canonical
            #      labels, we do NOT false-converge.
            #   2. resolution_stable — Engine's FINAL RESOLUTION section
            #      is functionally unchanged across iterations (similarity
            #      ratio >= threshold). Only checks once we have a prior
            #      synthesis to compare against (iteration 2+).
            new_bridge_count = _count_bridges_in_audit(bridge_stroke.raw_response)
            audit_is_substantive = _is_audit_substantive(bridge_stroke.raw_response)
            converged = False
            criterion: Optional[str] = None

            if new_bridge_count == 0 and not audit_is_substantive:
                # No canonical bridges + no substantive content → converged.
                converged = True
                criterion = "no_new_structural"
                logger.info(
                    "Session %s Bicameral iter %d: CONVERGED (no_new_structural — "
                    "0 canonical bridges + non-substantive audit text)",
                    session.id, iteration,
                )
            elif new_bridge_count == 0 and audit_is_substantive:
                # Non-canonical Bridge output — substantive text but no
                # canonical labels. Don't false-converge. Continue iteration.
                logger.warning(
                    "Session %s Bicameral iter %d: Bridge produced %d-char "
                    "substantive output but no canonical Bridge N (STRUCTURAL|IMPLIED) "
                    "labels matched. Treating as ambiguous-no-convergence; will "
                    "check resolution_stable next.",
                    session.id, iteration, len(bridge_stroke.raw_response),
                )

            # Resolution-stable check (criterion 2) — only fires if count-based
            # didn't converge AND we have a prior synthesis to compare against.
            if not converged and prior_synthesis is not None:
                if _resolution_stable(prior_synthesis, engine_stroke.raw_response):
                    converged = True
                    criterion = "resolution_stable"
                    logger.info(
                        "Session %s Bicameral iter %d: CONVERGED (resolution_stable — "
                        "FINAL RESOLUTION section functionally unchanged vs. iter %d)",
                        session.id, iteration, iteration - 1,
                    )

            await session.emit(
                SessionEventType.BICAMERAL_ITERATION_END,
                payload={
                    "iteration": iteration,
                    "engine_stroke_number": engine_stroke.stroke_number,
                    "bridge_stroke_number": bridge_stroke.stroke_number,
                    "new_bridges_surfaced": new_bridge_count,
                },
            )

            if converged:
                await session.emit(
                    SessionEventType.BICAMERAL_CONVERGED,
                    payload={
                        "iterations": iteration,
                        "criterion": criterion,
                    },
                )
                return results

            # ---------- Save state for next iteration ----------
            prior_synthesis = engine_stroke.raw_response
            prior_bridge_findings = bridge_stroke.raw_response
            prior_bridge_count = new_bridge_count

            # ---------- Inter-iteration delay ----------
            if iteration < max_iterations:
                logger.debug(
                    "Session %s Bicameral iter %d: sleeping %.1fs before next iteration",
                    session.id, iteration, min_inter_iteration_delay,
                )
                await asyncio.sleep(min_inter_iteration_delay)
                self._check_cancelled(
                    session, f"bicameral-iter-{iteration}-after-delay",
                )

        # Hit hard iteration cap without convergence
        logger.info(
            "Session %s Bicameral: HARD CAP reached (%d iterations) without convergence",
            session.id, max_iterations,
        )
        await session.emit(
            SessionEventType.BICAMERAL_HARD_CAP_REACHED,
            payload={
                "iterations": max_iterations,
                "max_iterations": max_iterations,
            },
        )
        return results

    # =====================================================================
    # Full Universal Logic Loop — Phase 1 (Triage) → Phase 2 (Oracle swarm
    # with programmatic Deep Research + Import) → Phase 3 (Synthesis).
    #
    # This is the "type a question, get a real resolution" path the
    # original Powell / Tokenized Land / Giant-Slayer runs proved out
    # interactively. The session emits structured events at every phase
    # boundary so WS subscribers render live progress.
    #
    # Long: each Oracle is one notebook create + persona config + Deep
    # Research run (5-20min) + programmatic source import + harvest. With
    # the gate's 8s cooldown and 3 default subjects, expect 15-60 min
    # wall time per full run.
    # =====================================================================

    async def run_universal_loop(
        self,
        session: Session,
        *,
        max_subjects: int = 3,
        deep_research_timeout: float = 1800.0,
        max_sources_per_oracle: int = 30,
        research_mode: str = "deep",
    ) -> StrokeResult:
        """Phase 1 (Triage) → Phase 2 (per-subject Oracle harvest with
        programmatic Deep Research) → Phase 3 (Synthesis).

        Emits, in order:
            - BLUEPRINT_READY      after Phase 1, payload contains the full
                                   blueprint text + the parsed Hit List
            - ORACLE_REQUEST       per subject before the Oracle is created
            - ORACLE_CREATED       per subject once the notebook exists
            - ORACLE_HARVESTED     per subject after the Truth Packet is read
            - STROKE_STARTED / SYNTHESIS_COMPLETE / STROKE_COMPLETED   for
                                   the Phase-3 synthesis (via
                                   run_synthesis_stroke)

        The Engine never sees an empty truth_packet list — if an Oracle's
        research or harvest fails the failure text becomes the packet, so
        the synthesis prompt is honest about what was gathered.

        Returns the final Phase-3 StrokeResult. Caller invokes
        :meth:`Session.complete` afterward.
        """
        if session.status != "running":
            raise RuntimeError(
                f"Session {session.id} is not running (status={session.status})"
            )
        if session.pathway not in (Pathway.CLEANROOM, Pathway.GENIE, Pathway.OFFENSIVE):
            raise ValueError(
                f"run_universal_loop does not support pathway "
                f"{session.pathway.value} — Mirror Audit operates on supplied "
                f"prior_resolution and does not spawn Oracles."
            )

        # ---------------- Phase 1: Triage ---------------------------------

        scenario_text = scenario_to_synthesis_text(session.scenario, session.pathway)
        triage_prompt = TRIAGE_TEMPLATE_STRUCTURED.format(
            scenario=scenario_text, max_subjects=max_subjects
        )
        logger.info(
            "Session %s: Phase 1 triage (max_subjects=%d)",
            session.id, max_subjects,
        )
        triage_raw = await self.svc.query_chess_engine(triage_prompt)
        blueprint_text, subjects = parse_triage_hit_list(triage_raw)
        await session.emit(
            SessionEventType.BLUEPRINT_READY,
            payload={
                "blueprint": blueprint_text,
                "subjects": subjects,
                "subject_count": len(subjects),
                "parse_ok": len(subjects) > 0,
            },
        )

        if not subjects:
            # Triage produced no parseable subjects. Synthesise on the
            # blueprint itself as a single Truth Packet so we still return
            # 9D-shaped content rather than failing the run.
            logger.warning(
                "Session %s: Phase 1 returned no parseable subjects; "
                "synthesising on the blueprint alone",
                session.id,
            )
            fallback_packets = [
                TruthPacket(
                    subject="Triage Blueprint (no Hit List parseable)",
                    content=blueprint_text,
                    source_label="UL Loop fallback — Engine triage only",
                )
            ]
            return await self.run_synthesis_stroke(session, fallback_packets)

        # ---------------- Phase 2: per-subject Oracle harvest --------------

        harvested: dict[str, str] = {}
        for subject_data in subjects:
            subject = (subject_data.get("name") or "subject").strip()
            surgical_prompt = (subject_data.get("surgical_prompt") or "").strip()
            if not surgical_prompt:
                logger.warning(
                    "Session %s: subject %r has no surgical_prompt; skipping",
                    session.id, subject,
                )
                harvested[subject] = "SKIPPED: no surgical_prompt provided"
                continue

            await session.emit(
                SessionEventType.ORACLE_REQUEST,
                payload={
                    "subject": subject,
                    "surgical_prompt": surgical_prompt,
                },
            )

            try:
                oracle = await self.create_oracle(subject, surgical_prompt)
            except Exception as exc:
                logger.exception("Session %s: create_oracle failed for %s",
                                 session.id, subject)
                harvested[subject] = f"ORACLE CREATION FAILED: {exc}"
                continue

            await session.emit(
                SessionEventType.ORACLE_CREATED,
                payload={
                    "subject": subject,
                    "notebook_id": oracle.notebook_id,
                    "full_name": oracle.full_name,
                },
            )

            # Deep Research + programmatic import. This is the previously-
            # manual "click Import in the NotebookLM UI" step, now handled
            # by notebooklm-py's research.import_sources().
            imported_count = 0
            try:
                research = await self.svc.run_deep_research(
                    notebook_id=oracle.notebook_id,
                    query=surgical_prompt,
                    source="web",
                    mode=research_mode,
                    auto_import=True,
                    max_sources=max_sources_per_oracle,
                    timeout=deep_research_timeout,
                )
                imported_count = len(research.get("imported", []) or [])
            except Exception as exc:
                logger.exception("Session %s: Deep Research failed for %s",
                                 session.id, subject)
                harvested[subject] = f"DEEP RESEARCH FAILED: {exc}"
                # Orphan-cleanup: the notebook was created above but has no
                # imported sources and never produced a truth packet.  Delete
                # it so it does not clutter the user's NotebookLM dashboard.
                await self._cleanup_failed_oracle(oracle.notebook_id)
                await session.emit(
                    SessionEventType.ORACLE_HARVESTED,
                    payload={
                        "subject": subject,
                        "notebook_id": oracle.notebook_id,
                        "status": "research_failed",
                        "error": str(exc),
                    },
                )
                continue

            # Harvest the Truth Packet — Oracle now has imported sources to
            # draw from, so its answer is hash-cited per PKI persona.
            try:
                packet = await self.harvest(oracle)
            except Exception as exc:
                logger.exception("Session %s: harvest failed for %s",
                                 session.id, subject)
                packet = f"HARVEST FAILED: {exc}"
                # Same orphan-cleanup as the research-failed path.  The
                # notebook does have imported sources at this point, but no
                # truth packet was harvested — keeping it around just for
                # the sources is not worth the dashboard clutter.
                await self._cleanup_failed_oracle(oracle.notebook_id)

            harvested[subject] = packet
            await session.emit(
                SessionEventType.ORACLE_HARVESTED,
                payload={
                    "subject": subject,
                    "notebook_id": oracle.notebook_id,
                    "sources_imported": imported_count,
                    "packet_chars": len(packet),
                    "status": "ok",
                },
            )

        # ---------------- Phase 3: Synthesis -------------------------------

        truth_packets = [
            TruthPacket(
                subject=name,
                content=content,
                source_label=f"UL Loop Oracle ({name})",
            )
            for name, content in harvested.items()
        ]
        logger.info(
            "Session %s: Phase 3 synthesis with %d Truth Packet(s)",
            session.id, len(truth_packets),
        )
        return await self.run_synthesis_stroke(session, truth_packets)


# ---------------------------------------------------------------------------
# Hit-list parser
#
# The TRIAGE_TEMPLATE_STRUCTURED asks the Engine to emit a JSON object
# delimited by <HIT_LIST_JSON>...</HIT_LIST_JSON> markers. Real-world
# Engine output sometimes wraps it in fences or shifts the markers; this
# parser is defensive — tries the marker block first, then any object
# containing a "subjects" array, before giving up.
# ---------------------------------------------------------------------------

def parse_triage_hit_list(triage_response: str) -> tuple[str, list[dict]]:
    """Extract (blueprint_text, parsed_subjects) from a structured triage.

    Returns the full triage_response as blueprint_text (the Engine's prose
    is informative on its own), plus a list of ``{name, surgical_prompt}``
    dicts. Returns an empty list if no JSON could be extracted — the
    caller should fall back to triage-only synthesis.
    """
    import json
    import re

    # Try the marked block first.
    marker_match = re.search(
        r"<HIT_LIST_JSON>\s*(\{.*?\})\s*</HIT_LIST_JSON>",
        triage_response,
        re.DOTALL,
    )
    candidates: list[str] = []
    if marker_match:
        candidates.append(marker_match.group(1))

    # Fallback: any JSON object that contains "subjects": [
    for m in re.finditer(
        r"\{[^{}]*\"subjects\"\s*:\s*\[.*?\][^{}]*\}",
        triage_response,
        re.DOTALL,
    ):
        candidates.append(m.group(0))

    for cand in candidates:
        try:
            data = json.loads(cand)
        except json.JSONDecodeError:
            continue
        subjects = data.get("subjects")
        if isinstance(subjects, list):
            cleaned: list[dict] = []
            for s in subjects:
                if not isinstance(s, dict):
                    continue
                name = (s.get("name") or "").strip()
                prompt = (s.get("surgical_prompt") or s.get("prompt") or "").strip()
                if name and prompt:
                    cleaned.append({"name": name, "surgical_prompt": prompt})
            if cleaned:
                return triage_response, cleaned

    return triage_response, []


# ---------------------------------------------------------------------------
# Audit-stroke prompt (Mirror Auditor framing)
#
# The Auditor's persona already configures it for fault-finding; this
# template just wraps the analysis under audit with a small framing block
# that names the original scenario for context. Persona text in
# docs/protocols/Mirror_Auditor_Persona.md.
# ---------------------------------------------------------------------------

AUDIT_TEMPLATE = """\
You are receiving a Stroke-1 resolution from another 9D-Chess instance for audit.

ORIGINAL SCENARIO THE ANALYSIS WAS RESPONDING TO:
{scenario_context}

ANALYSIS UNDER AUDIT (verbatim output from the other instance):
=====
{analysis_under_audit}
=====

Per your operational rules, audit this analysis. Identify rigidity errors, pattern-matching, confidence-evidence gaps, and dimensional greeds. If sound, say so. Surgical plain language; no 9D jargon; no counter-strategy."""


# ---------------------------------------------------------------------------
# Connection Bridge audit prompt — Bicameral Convergence Level 1.
#
# Structural sibling of AUDIT_TEMPLATE but invokes the Connection Bridge
# persona (configured via NotebookLMService.configure_connection_bridge on
# a per-call notebook). The Bridge enumerates *missed connections* between
# Truth Packets that the Engine's synthesis didn't draw — orthogonal lens
# to the Mirror Auditor's fault-mode enumeration.
#
# Validated 2026-05-22 on the Amnesia substrate (3 missed bridges, entirely
# orthogonal to the Mirror Auditor's findings on the same scenario). See
# docs/concepts/Bicameral_Convergence.md and docs/protocols/Connection_Bridge_Persona.md.
# ---------------------------------------------------------------------------

BRIDGE_AUDIT_TEMPLATE = """\
You are receiving a Stroke-1 resolution from another 9D-Chess instance.

Your job is to identify CONNECTIONS between the Truth Packets — or between Truth Packets and the foundations corpus — that the synthesis above did NOT draw, but that the substrate would support.

ORIGINAL SCENARIO THE ANALYSIS WAS RESPONDING TO:
{scenario_context}

ANALYSIS UNDER AUDIT (verbatim output from the other instance):
=====
{analysis_under_audit}
=====

Per your Connection Bridge operational rules, enumerate the missed connections. For each: be specific about WHICH packets (or packet + foundations axiom) connect, WHAT the connection is, and WHY the synthesis above missed it. Surgical plain language. No 9D jargon. Do not produce a counter-strategy or corrected resolution — your job is connection identification only.

If the synthesis drew all available connections that the substrate supports, say so."""


# ---------------------------------------------------------------------------
# Iterative Engine re-synthesis prompt (Stroke 3)
#
# The original scenario + Truth Packets get re-fed into the Engine, this time
# accompanied by Stroke 1's resolution and Stroke 2's audit findings. The
# Engine is asked to recalibrate accounting for the audit's friction.
# ---------------------------------------------------------------------------

ITERATIVE_RESYNTHESIS_TEMPLATE = """\
ORIGINAL SCENARIO:
{scenario}

AUTHENTICATED TRUTH PACKETS (from PKI Oracle swarm):
{packets_block}

PRIOR ANALYSIS (Stroke 1 resolution from this Engine):
=====
{stroke_1_response}
=====

AUDIT FINDINGS (from a second 9D-Chess instance configured as Mirror Auditor):
=====
{audit_findings}
=====

MISSION:
Re-fire the synthesis. The Stroke-1 resolution above is your prior pass; the audit identifies specific failure modes in that pass. Recalibrate. The Stroke-3 resolution should be the move that survives BOTH the original physics AND the audit's friction. If the audit's findings are themselves mistaken, say so explicitly and explain why; otherwise integrate them into a tighter synthesis."""


# ---------------------------------------------------------------------------
# Bicameral Convergence Level 1 re-synthesis template.
#
# Used when the iterate loop runs with include_bridge=True. Same shape as
# ITERATIVE_RESYNTHESIS_TEMPLATE but with a second audit block carrying the
# Connection Bridge's missed-connection enumeration. The Engine is asked to
# integrate BOTH lenses — fault-mode catches from the Auditor AND missed-
# connection catches from the Bridge — into the re-synthesis.
# ---------------------------------------------------------------------------

ITERATIVE_BICAMERAL_RESYNTHESIS_TEMPLATE = """\
ORIGINAL SCENARIO:
{scenario}

AUTHENTICATED TRUTH PACKETS (from PKI Oracle swarm):
{packets_block}

PRIOR ANALYSIS (Stroke 1 resolution from this Engine):
=====
{stroke_1_response}
=====

AUDITOR FINDINGS (Mirror Auditor — fault modes in the reasoning):
=====
{audit_findings}
=====

BRIDGE FINDINGS (Connection Bridge — connections the synthesis missed):
=====
{bridge_findings}
=====

MISSION:
Re-fire the synthesis. The Stroke-1 resolution above is your prior pass. The Auditor block above identifies failure modes IN that reasoning; the Bridge block above identifies connections the reasoning MISSED. These are two orthogonal lenses — neither subsumes the other. The Stroke-3 resolution should be the move that survives BOTH the original physics AND both audit lenses' friction. If any finding is itself mistaken, say so explicitly and explain why; otherwise integrate them into a tighter synthesis."""


# ---------------------------------------------------------------------------
# Bicameral Convergence Level 2 closed-loop template.
#
# Used by ``run_bicameral_loop`` on iterations 2+. Iteration 1 uses the
# default scenario framing from ``run_synthesis_stroke``; subsequent
# iterations feed the prior iteration's synthesis + prior iteration's
# Bridge findings back as friction. No Auditor in the Level 2 loop —
# the closed loop is Engine ↔ Bridge only.
#
# Note the mission framing differs from Level 1's: Level 1 asks the
# Engine to integrate one-shot audits into a tighter synthesis; Level 2
# asks the Engine to converge — produce a synthesis the next Bridge
# audit will find no further missed connections in. The framing
# encourages the Engine to either (a) genuinely integrate the Bridge
# findings, or (b) explicitly rebut them when they don't apply, both
# of which contribute to convergence.
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Pl3 Operator Lens — translation prompt library (milestone 45 corrected).
#
# Translation is routed through the canonical NotebookLM Engine (NOT Gemini
# Flash) so the model has the foundations-corpus grounding to understand
# what the framework concepts actually MEAN when translating. This is what
# made the milestone 43 Cube-of-Space exchange work — the notebook
# produced visceral geometric vocabulary because the grounded model
# understood the underlying primitives. A Gemini Flash translator would
# only know surface-level jargon mapping, not the structural meaning.
#
# The Engine's existing persona ("infallible 9D-Chess Umpire... supreme
# order and precision") is jargon-heavy by design. The translation prompts
# explicitly instruct the Engine to re-express AGAINST that default and
# drop the jargon — the persona's discipline is what holds the analytical
# claims stable while the prompt shifts the vocabulary register.
#
# Each register is a prompt template with a single {source_text}
# placeholder. The translation call is one NotebookLM Engine query —
# subject to the cooldown gate and the input-size cap. Source text plus
# framing typically lands at 3-5k chars, well under the cap.
#
# Closed-RAG-sphere discipline: we DELIBERATELY do not route translation
# through Gemini Flash. Gemini is scoped to dispatcher intent
# classification (a thin "what does the operator want" call that doesn't
# touch analytical content). Translation IS analytical — carrying
# strategic claims forward — so it stays inside the closed sphere.
# ---------------------------------------------------------------------------

TRANSLATION_REGISTERS = ("plain_english", "cube_of_space", "executive_brief")


TRANSLATION_PROMPT_TEMPLATES = {
    "plain_english": """\
You produced the following analysis. Your task now is to re-express it in plain everyday English suitable for someone unfamiliar with the 9D-Chess framework, preserving the analytical claims and structural reasoning 1:1.

CONSTRAINTS — these are non-negotiable:
- Do NOT add new claims the original didn't make.
- Do NOT soften conclusions or introduce hedging the original didn't carry.
- Do NOT change the strategic logic.
- DROP the framework jargon entirely; translate the vocabulary while preserving the meaning.

Translate by mapping the jargon to plain words:
- "DAI" / "Dimensional Awareness Index" → "how many dimensions of the situation each actor can see"
- "DAP" / "Dimensional Awareness Profile" → "which dimensions the actor pays attention to"
- "SDS" / "Set of Disadvantageous States" → "the bad outcomes the opponent gets funneled into"
- "ROEM" / "Reverse Observer Effect Model" → "the trap where being observed forces the opponent into bad moves"
- "Strategic Lasso" / "Strategic Funnel" → "the gradual narrowing of the opponent's options"
- "Incomprehensible Move" → "a move so dimensionally different the opponent can't process it in time"
- "Convergence Theorem" → "the structural certainty that the opponent's options collapse to a bad outcome"
- "Set" archetype → "chaotic disruption" or "disruptive force"
- "Horus" archetype → "established order" or "legitimate authority"
- "Go-like" → "long-term territorial / positional"
- "Chess-like" → "direct tactical confrontation"
- "Ω" / "strategic universe" → "the full strategic situation"
- "Ω'" / "perceived sub-universe" → "the limited view the opponent operates with"

Keep the per-dimension breakdown structure if present, but use plain words for dimension names where possible. Keep the FINAL RESOLUTION section. Don't omit anything substantive. The output should read like a thoughtful colleague explaining the same conclusion in clearer words.

Source analysis to translate:
=====
{source_text}
=====

Plain-English translation:""",

    "cube_of_space": """\
You produced the following analysis. Your task now is to re-express it using the Cube-of-Space register — visceral geometric vocabulary that maps the framework's structural reasoning onto spatial primitives. Preserve the analytical claims and structural reasoning 1:1.

CONSTRAINTS — these are non-negotiable:
- Do NOT add new claims the original didn't make.
- Do NOT soften conclusions or introduce hedging the original didn't carry.
- Do NOT change the strategic logic.
- Shift the vocabulary toward geometric/spatial visceral framing; preserve the meaning underneath.

Translate by mapping the framework primitives onto geometric primitives:
- "DAI" / "dimensional awareness" → "higher-dimensional perception", "seeing the full topology"
- "SDS" / "Set of Disadvantageous States" → "gravity well of bad outcomes", "predefined collapse basin", "geometric trap"
- "ROEM" → "the reverse observer effect: being watched forces collapse"
- "Strategic Lasso" / "Funnel" → "the narrowing geometric path", "the closing trap", "the funnel tightening"
- "Convergence Theorem" → "the inevitable collapse into the predefined basin"
- "Set" / "Horus" archetypes — keep these (Cube-of-Space uses similar archetypal vocabulary)
- "central intersection", "North face / South face", "ascending / descending spirals" — use where natural
- Embrace geometric metaphors: "the opponent's path runs through a narrowing corridor", "they cross into the gravity well at the central intersection"
- Goal phrase: "actualizes the concept instead of avoiding it" — use when describing how the strategist operates the meta-position

Preserve all analytical content. Keep per-dimension breakdown if present. Keep FINAL RESOLUTION. The output should read like the same analysis written by a strategist who thinks in spatial / geometric vocabulary natively.

Source analysis to translate:
=====
{source_text}
=====

Cube-of-Space translation:""",

    "executive_brief": """\
You produced the following analysis. Your task now is to compress it into a tight executive brief suitable for a busy decision-maker. Preserve the analytical claims and strategic conclusions 1:1, but cut everything that isn't a decision-maker-relevant claim.

CONSTRAINTS — these are non-negotiable:
- Do NOT add new claims the original didn't make.
- Do NOT soften conclusions or introduce hedging the original didn't carry.
- Do NOT change the strategic logic.
- DROP framework vocabulary entirely (DAI / SDS / ROEM / Strategic Lasso / Set / Horus / Ω / etc.).
- DROP the per-dimension breakdown and procedural detail.

Structure the brief in EXACTLY these four sections, each labeled:

1. **Bottom line** (1 sentence): the predicted outcome or recommended action.
2. **Why this is the move** (2-3 sentences): the underlying strategic mechanism, in plain business/strategy language.
3. **Risk that would falsify this** (1-2 sentences): what would have to be true for the conclusion to be wrong.
4. **What to watch for** (1-2 sentences): concrete indicators the operator should track to validate or falsify.

If the source is ambivalent or has multiple paths, the brief reflects that honestly — don't manufacture confidence. The output should read like a 3-5 paragraph summary the operator could forward to a non-framework-native stakeholder without further explanation.

Source analysis to translate:
=====
{source_text}
=====

Executive brief:""",
}


ITERATIVE_BICAMERAL_LOOP_TEMPLATE = """\
ORIGINAL SCENARIO:
{scenario}

AUTHENTICATED TRUTH PACKETS (from PKI Oracle swarm):
{packets_block}

PRIOR ITERATION SYNTHESIS (Iteration {prior_iteration}):
=====
{prior_synthesis}
=====

BRIDGE FINDINGS (Connection Bridge — missed connections in the prior synthesis):
=====
{bridge_findings}
=====

MISSION:
You are in Iteration {current_iteration} of a closed-loop Bicameral Convergence run. The prior iteration's synthesis above is your work-in-progress; the Bridge has identified connections that synthesis missed. Re-fire the synthesis to integrate these missed connections.

Preserve the kernel of the prior reasoning where it stands. Where the Bridge surfaced load-bearing missed connections, incorporate them. If any Bridge finding is itself mistaken — e.g., the connection it surfaces isn't actually supported by the substrate, or the prior synthesis already addressed it — say so explicitly and explain why.

The goal of this iteration is convergence: produce a synthesis the next Bridge audit will find no further missed connections in. Use the standard 9-dimensional resolution structure with FINAL RESOLUTION at the end."""


# ---------------------------------------------------------------------------
# Convergence-detection helper.
#
# Counts the number of STRUCTURAL or IMPLIED bridges in a Bridge audit
# output. Used by ``run_bicameral_loop`` to detect convergence (count == 0
# means the Bridge found no further missed connections).
#
# E1-03 implementation: regex-based count of "Bridge N (STRUCTURAL)" and
# "Bridge N (IMPLIED)" patterns. The Bridge persona is configured to emit
# its catches in that format (see docs/protocols/Connection_Bridge_Persona.md).
# SPECULATIVE bridges are NOT counted — they're the persona's epistemic-
# humility tier and don't indicate substantive missed connections.
#
# E1-04 will refine convergence detection by adding the resolution-stable
# criterion (Engine FINAL RESOLUTION text functionally unchanged across
# iterations). For now only the count-based criterion fires.
# ---------------------------------------------------------------------------

def _count_bridges_in_audit(raw: str) -> int:
    """Count STRUCTURAL + IMPLIED bridges in a Connection Bridge audit response.

    Looks for patterns like ``Bridge 1 (STRUCTURAL)`` / ``Bridge 2 (IMPLIED)``
    in any case + with optional markdown bolding. SPECULATIVE bridges are
    intentionally excluded — they signal "I see a possible connection but
    can't substantively support it from the packets," which is the
    persona's epistemic-humility tier rather than a substantive catch.

    Returns 0 if no STRUCTURAL/IMPLIED bridges found — the convergence
    signal for ``run_bicameral_loop``. Combined with ``_is_audit_substantive``
    below to guard against false convergence on non-canonical Bridge output.

    Returns the raw count when bridges are present; the caller uses
    ``== 0`` for convergence detection but the count is also useful for
    BICAMERAL_ITERATION_END event payload (``new_bridges_surfaced``).
    """
    # Match: "Bridge N (STRUCTURAL)" or "Bridge N (IMPLIED)" with optional
    # markdown bolding and case-insensitive tier. Whitespace tolerant.
    pattern = re.compile(
        r"\*{0,2}\s*Bridge\s+\d+\s*\(\s*(?:STRUCTURAL|IMPLIED)\s*\)",
        re.IGNORECASE,
    )
    return len(pattern.findall(raw))


# ---------------------------------------------------------------------------
# Non-canonical Bridge output defense (E1-04).
#
# The Bridge persona is configured to emit catches in the canonical
# ``Bridge N (STRUCTURAL|IMPLIED|SPECULATIVE)`` format, but observed runs
# (notably LMArena Run 7, 2026-05-26) show the persona occasionally
# defaults to a stream-of-consciousness style with section headers like
# "**Evaluating Strategic Freedom**" instead of the canonical labels.
# Without a fallback, the convergence-count regex would return 0 on such
# output and ``run_bicameral_loop`` would falsely converge after iteration 1.
#
# The fallback heuristic checks whether the audit text contains
# substantive content even when canonical labels are absent: length
# threshold + token presence indicating bridge-flavored reasoning. If
# the audit looks substantive, the loop treats it as ambiguous-no-
# convergence rather than false-converging. The operator can re-run
# with a persona-tightened Bridge if needed.
# ---------------------------------------------------------------------------

_BRIDGE_FLAVOR_TOKENS = (
    "missed", "connection", "bridge", "should have", "fails to",
    "ignores", "overlooks", "did not", "neglected", "untraced",
    "unaddressed", "should be", "implies", "synthesis missed",
)


def _is_audit_substantive(raw: str) -> bool:
    """Best-effort check: does the audit text look substantive even when no canonical Bridge labels match?

    Returns True if the audit text is long enough AND contains multiple
    bridge-flavored tokens, suggesting the Bridge persona produced real
    content in a non-canonical format. Returns False if the text is short
    or token-sparse, indicating a genuine "no missed connections" result.

    Used by ``run_bicameral_loop`` to guard against false convergence on
    non-canonical Bridge persona output. Threshold tuning: 300 chars +
    2 distinct tokens — empirically conservative; tighten if non-canonical
    output gets richer or loosen if the persona reliably hits canonical
    format.
    """
    text = raw.strip()
    if len(text) < 300:
        return False
    text_lower = text.lower()
    matched = sum(1 for tok in _BRIDGE_FLAVOR_TOKENS if tok in text_lower)
    return matched >= 2


# ---------------------------------------------------------------------------
# Resolution-stable convergence criterion (E1-04).
#
# The second convergence check (after no_new_structural). The intuition:
# even if the Bridge keeps surfacing connections, if the Engine has
# stabilized on its FINAL RESOLUTION across iterations, additional
# iterations aren't producing meaningful change — the Engine has
# converged on its answer even if the audit lens hasn't.
#
# Heuristic:
#   1. Extract the FINAL RESOLUTION section from each synthesis
#      (look for explicit headers; fall back to last 30% of text).
#   2. Normalize: strip markdown, collapse whitespace, lowercase.
#   3. Compute difflib.SequenceMatcher ratio between the two.
#   4. Compare against threshold (0.85 default — empirically high
#      enough to require real stability but low enough to tolerate
#      minor word-choice differences).
#
# threshold tunable via env var ``GANYMEDE_RESOLUTION_STABLE_THRESHOLD``
# for operator experimentation.
# ---------------------------------------------------------------------------

_RESOLUTION_STABLE_THRESHOLD = float(
    os.environ.get("GANYMEDE_RESOLUTION_STABLE_THRESHOLD", "0.85")
)


def _extract_final_resolution_section(raw: str) -> str:
    """Best-effort extraction of the FINAL RESOLUTION section from a synthesis.

    Searches for explicit FINAL RESOLUTION / RESOLUTION / FINAL 9D
    RESOLUTION headers. If found, returns everything from the header to
    the next major header or end of text. If no canonical header found,
    falls back to the last 30% of the text (heuristic: the conclusion
    typically lives at the end).

    Used by ``_resolution_stable`` to compare just the conclusion across
    iterations rather than the full per-dimension breakdown (which can
    differ in wording while reaching the same resolution).
    """
    # Try canonical headers first, in order of specificity
    patterns = [
        r"(?:^|\n)\**\s*FINAL\s+9D\s+RESOLUTION\b.*?(?=\n\**\s*[A-Z][A-Z\s]{3,}\n|\Z)",
        r"(?:^|\n)\**\s*FINAL\s+RESOLUTION\b.*?(?=\n\**\s*[A-Z][A-Z\s]{3,}\n|\Z)",
        r"(?:^|\n)\**\s*RESOLUTION\b.*?(?=\n\**\s*[A-Z][A-Z\s]{3,}\n|\Z)",
    ]
    for p in patterns:
        match = re.search(p, raw, re.DOTALL | re.IGNORECASE)
        if match:
            return match.group(0).strip()
    # Fall back to last 30% of text — the conclusion is usually at the end
    cut = int(len(raw) * 0.7)
    return raw[cut:].strip()


def _normalize_for_similarity(text: str) -> str:
    """Strip markdown + collapse whitespace + lowercase for similarity comparison.

    Removes characters that don't affect semantic content but would
    introduce false-negative similarity (different markdown decoration
    around the same words). Used by ``_resolution_stable``.
    """
    # Strip markdown bold/italic/code/headers
    text = re.sub(r"[*_#`]+", " ", text)
    # Collapse all whitespace runs to single space
    text = re.sub(r"\s+", " ", text)
    return text.strip().lower()


def _resolution_stable(
    prior_synthesis: str,
    current_synthesis: str,
    threshold: float = _RESOLUTION_STABLE_THRESHOLD,
) -> bool:
    """Return True iff the FINAL RESOLUTION sections of two syntheses are functionally unchanged.

    Compares the FINAL RESOLUTION section (or fallback last-30% slice)
    of each synthesis, normalized for markdown + whitespace + case,
    using ``difflib.SequenceMatcher.ratio``. Returns True if the
    similarity ratio is >= ``threshold``.

    Default threshold 0.85 (operator-tunable via
    ``GANYMEDE_RESOLUTION_STABLE_THRESHOLD``). Empirical baseline: same
    Engine producing two synthesis runs of the same scenario with
    minor wording differences typically scores 0.7-0.85; functionally
    identical resolutions (Engine has converged) score 0.85+.

    Used by ``run_bicameral_loop`` as the second convergence criterion
    after the count-based ``no_new_structural`` check.
    """
    import difflib  # stdlib, deferred import — only used here

    prior_section = _extract_final_resolution_section(prior_synthesis)
    current_section = _extract_final_resolution_section(current_synthesis)
    prior_norm = _normalize_for_similarity(prior_section)
    current_norm = _normalize_for_similarity(current_section)

    if not prior_norm or not current_norm:
        return False  # No comparable text → don't converge

    ratio = difflib.SequenceMatcher(None, prior_norm, current_norm).ratio()
    return ratio >= threshold


# ---------------------------------------------------------------------------
# CTA-suppression post-processor (P1-03b).
#
# Backend boundary mitigation for the partially-effective persona CTA-
# suppression observed in P1-03 (3/7 ≈ 43% inclusive, 2/6 ≈ 33% strict).
# Stroke 1 outputs occasionally leak chatbot-CTA endings ("Would you
# like me to...", "Shall I...", "If you'd like...") despite the persona's
# explicit prohibition — NotebookLM substrate behavior overrides persona
# text per the corpus-dominance lesson (Framework Cleanup Hypothesis
# evidence #7: "all persona-override attempts have failed when fighting
# the corpus").
#
# Approach: conservative trailing-paragraph strip. Split the response on
# paragraph breaks; examine the LAST non-empty paragraph; case-insensitive
# match against a curated list of CTA opener phrases. If match, slice the
# whole paragraph off + return it separately for forensic preservation.
#
# Conservative deliberately:
#   - Only strips the LAST paragraph (CTAs are end-of-message)
#   - Only matches phrases that START the paragraph (not mid-paragraph CTA
#     attempts; those are usually genuine content)
#   - Returns the response unchanged if stripping would leave empty
#     content (degenerate case — would indicate a fully-CTA stroke
#     which is upstream-broken; let it surface)
#   - Strips leading markdown/whitespace before matching (so a paragraph
#     starting with "**Would you like me to...**" still matches)
#
# Engine persona text left in place as defense-in-depth — both layers run.
# ---------------------------------------------------------------------------

_CTA_OPENERS = (
    "would you like me to",
    "would you like to",
    "shall i",
    "let me know",
    "if you'd like",
    "if you would like",
    "do you want",
    "want me to",
    "happy to",
    "i can also",
    "do let me know",
    "feel free to",
    "would you prefer",
)


def _strip_trailing_cta(raw_response: str) -> tuple[str, Optional[str]]:
    """Strip a trailing CTA paragraph from a stroke response.

    Returns ``(cleaned, stripped_cta)``. When no CTA is detected, returns
    ``(raw_response, None)`` — the cleaned text is identical to the
    original so callers can compare ``stripped_cta is None`` to decide
    whether to surface ``cleaned_response`` separately on StrokeResult.

    Detection: split on paragraph breaks (``\\n\\n``); examine the last
    non-empty paragraph; strip leading markdown/whitespace; check
    case-insensitively against the ``_CTA_OPENERS`` curated phrase list.
    If match, return everything but that paragraph as cleaned + the
    matched paragraph as stripped_cta.

    Refuses to strip if it would leave the cleaned response empty
    (degenerate case — surface raw_response unchanged so the empty-
    stroke handling elsewhere catches it).
    """
    if not raw_response or not raw_response.strip():
        return raw_response, None

    # Split into paragraphs; track the last non-empty one
    paragraphs = raw_response.split("\n\n")
    last_idx = -1
    for i in range(len(paragraphs) - 1, -1, -1):
        if paragraphs[i].strip():
            last_idx = i
            break
    if last_idx < 0:
        return raw_response, None

    last_para = paragraphs[last_idx]
    # Strip leading markdown decoration + whitespace before matching
    last_para_normalized = re.sub(
        r"^[\s\*#\-_>`]+", "", last_para.strip(),
    ).lower()

    # Check if the last paragraph starts with a CTA opener
    matched = False
    for opener in _CTA_OPENERS:
        if last_para_normalized.startswith(opener):
            matched = True
            break

    if not matched:
        return raw_response, None

    # Strip the last paragraph; refuse if cleaned would be empty
    cleaned_paragraphs = paragraphs[:last_idx] + paragraphs[last_idx + 1:]
    cleaned = "\n\n".join(cleaned_paragraphs).rstrip()
    if not cleaned.strip():
        return raw_response, None

    return cleaned, last_para.strip()


def _parse_audit_findings(raw: str) -> Optional[list[str]]:
    """Best-effort extraction of the four-category fault list from a
    Mirror Auditor response.

    The Auditor persona is configured to emit findings in a numbered
    structure (RIGIDITY ERRORS / PATTERN-MATCHING / CONFIDENCE-EVIDENCE
    GAPS / DIMENSIONAL GREEDS). This parser splits on the numbered
    headers; if the response doesn't match the expected structure it
    returns None and the caller falls back to displaying raw_response.
    """
    # Match patterns like "1. RIGIDITY", "2.", or "**1. RIGIDITY**"
    pattern = re.compile(
        r"(?:^|\n)\**\s*([1-4])\.\s",
        re.MULTILINE,
    )
    matches = list(pattern.finditer(raw))
    if len(matches) < 2:
        return None
    findings = []
    for i, m in enumerate(matches):
        start = m.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(raw)
        chunk = raw[start:end].strip()
        if chunk:
            findings.append(chunk)
    return findings if findings else None


def _extract_for_resynthesis(stroke_1_raw: str, max_chars: int) -> str:
    """Extract head + final-resolution capstone of a Stroke 1 output for
    Stroke 3 friction-injection.

    Stroke 3's job is to re-synthesize given the Auditor's critique of
    Stroke 1's conclusion. The load-bearing parts are:
      (a) any self-flagged evidence-limitation or framing notice at
          Stroke 1's head (the Engine sometimes opens with a notice
          like "data does not exist within the established source
          archives; independent verification advised"),
      (b) Stroke 1's FINAL RESOLUTION section — the conclusion the
          Auditor was critiquing.

    The per-dimension breakdown in the middle is well-covered by the
    Auditor's audit text itself, so we omit it for budget. If the
    Engine's output doesn't have a recognizable FINAL RESOLUTION
    marker, we fall back to the last ``max_chars`` of the raw text
    (conclusion is at the end either way).

    Strategy:
      1. Find a FINAL [...] RESOLUTION marker (case-insensitive).
      2. Head: first ~400 chars (captures evidence-flag notices).
      3. Capstone: from marker to end.
      4. Join with a "[per-dimension breakdown omitted for budget]" separator.
      5. If still over budget, head-trim the capstone (keep bottom line).
    """
    if not stroke_1_raw:
        return ""

    HEAD_BUDGET = 400
    SEPARATOR = "\n\n[per-dimension breakdown omitted for re-synthesis budget]\n\n"

    # Look for a FINAL ... RESOLUTION-style marker (works for the Engine's
    # observed outputs: "**Final 9D Resolution via ROEM:**", "Final 9D
    # Resolution:", "FINAL 9D RESOLUTION", "Final Resolution:", etc.)
    pattern = re.compile(
        r"^\s*\**\s*(?:final|FINAL)\b[^\n]*(?:resolution|RESOLUTION)\b.*$",
        re.MULTILINE,
    )
    match = pattern.search(stroke_1_raw)

    if not match:
        # No marker — return the last max_chars (conclusion is at end).
        if len(stroke_1_raw) <= max_chars:
            return stroke_1_raw.strip()
        return stroke_1_raw[-max_chars:].strip()

    capstone_start = match.start()

    # If capstone marker is inside the head budget, just return the
    # whole tail (no separator needed; head and capstone overlap).
    if capstone_start < HEAD_BUDGET:
        capstone = stroke_1_raw[capstone_start:].strip()
        if len(capstone) <= max_chars:
            return capstone
        return capstone[-max_chars:].strip()

    head = stroke_1_raw[:HEAD_BUDGET].strip()
    capstone = stroke_1_raw[capstone_start:].strip()

    capstone_budget = max_chars - len(head) - len(SEPARATOR)
    if capstone_budget < 200:
        # Head is eating the whole budget; just return capstone trimmed.
        return capstone[-max_chars:].strip() if len(capstone) > max_chars else capstone

    if len(capstone) > capstone_budget:
        # Keep the LAST capstone_budget chars (bottom-line at the end).
        capstone = capstone[-capstone_budget:].strip()

    return head + SEPARATOR + capstone


def _truncate_audit_for_injection(stroke_2_raw: str, max_chars: int) -> str:
    """Truncate Mirror Auditor output for Stroke 3 injection.

    Uses :func:`_parse_audit_findings` to split into the four category
    chunks, then budgets each equally. The category HEADER + first
    sentences are the most informative; truncate each chunk from its
    end. If the structural parse fails, head-truncate the raw text.
    """
    if not stroke_2_raw:
        return ""

    findings = _parse_audit_findings(stroke_2_raw)
    if findings is None:
        # Parse failed — head-truncate the raw text.
        if len(stroke_2_raw) <= max_chars:
            return stroke_2_raw.strip()
        return stroke_2_raw[:max_chars].rstrip() + "\n[… truncated for budget …]"

    # Budget each finding. Reserve ~10 chars per joiner between chunks.
    joiner = "\n\n"
    overhead = len(joiner) * max(0, len(findings) - 1)
    per_finding_budget = max(200, (max_chars - overhead) // len(findings))

    truncated = []
    for f in findings:
        if len(f) <= per_finding_budget:
            truncated.append(f)
        else:
            truncated.append(f[:per_finding_budget].rstrip() + " […]")
    return joiner.join(truncated)


def _truncate_bridge_for_injection(bridge_raw: str, max_chars: int) -> str:
    """Truncate Connection Bridge output for Stroke 3 injection.

    Bridge output doesn't follow the Auditor's four-numbered-category
    shape — observed Bridge outputs are 2-4 short paragraphs of free-form
    connection enumeration (often with bold "Evaluating X" / "Assessing Y"
    sub-headers and packet citations like ``[103]``). Head-truncate to
    budget; the bottom line of a Bridge response is rarely as load-bearing
    as the Auditor's per-category catches, so trimming the tail is safe.
    """
    if not bridge_raw:
        return ""
    if len(bridge_raw) <= max_chars:
        return bridge_raw.strip()
    return bridge_raw[:max_chars].rstrip() + "\n[… truncated for budget …]"


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
