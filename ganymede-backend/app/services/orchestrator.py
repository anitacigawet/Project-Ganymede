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
from app.services.notebooklm import NotebookLMService
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
        stroke = StrokeResult(
            stroke_number=stroke_number,
            pathway=Pathway.MIRROR_AUDIT,
            raw_response=raw,
            audit_findings=_parse_audit_findings(raw),
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

    async def run_iterative_engine(
        self,
        session: Session,
        truth_packets: list[TruthPacket],
        *,
        max_strokes: int = 3,
    ) -> list[StrokeResult]:
        """Run the full Iterative Engine multi-stroke loop on a session.

        Stroke 1: synthesis (canonical Engine)
        Stroke 2: audit (Mirror Auditor reviews Stroke 1)
        Stroke 3: re-synthesis (canonical Engine, friction-injected with
                  audit findings)

        Stops at ``max_strokes`` (default 3 for a full thesis-antithesis-
        synthesis cycle). For ``max_strokes=1`` this degrades to a single
        synthesis stroke (same as ``run_synthesis_stroke`` directly).
        For ``max_strokes=2`` it does synthesis + audit but no
        re-synthesis.

        The session must be created with ``iterative=True`` and
        ``max_strokes >= 2`` for this to run usefully.

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

        results: list[StrokeResult] = []

        # Stroke 1: thesis
        s1 = await self.run_synthesis_stroke(session, truth_packets)
        results.append(s1)
        if max_strokes < 2:
            return results

        # Stroke 2: antithesis (audit)
        s2 = await self.run_audit_stroke(session)
        results.append(s2)
        if max_strokes < 3:
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
                "— no friction to inject. Iterative loop completes with 2 strokes; "
                "the empty-stroke UI warning will surface this to the operator.",
                session.id,
            )
            return results

        # Stroke 3: synthesis (re-fire with audit as friction)
        framing = ITERATIVE_RESYNTHESIS_TEMPLATE
        # The re-synthesis prompt embeds Stroke 1's text + the audit
        # findings. Built into the framing template; the truth_packets
        # passed here are the same originals (the Engine still needs
        # them for context, even on the re-fire).
        #
        # Escape any literal { } characters in the stroke outputs before
        # injection — synthesize() will call .format(scenario=..., packets_block=...)
        # on this framing string, so unescaped framework jargon like
        # "{DAI}" or "{ROEM}" in the Engine's response would otherwise
        # raise KeyError when .format() tries to substitute them.
        s1_escaped = s1.raw_response.replace("{", "{{").replace("}", "}}")
        s2_escaped = s2.raw_response.replace("{", "{{").replace("}", "}}")
        framing_with_audit = framing.replace(
            "{stroke_1_response}", s1_escaped
        ).replace(
            "{audit_findings}",
            s2_escaped,
        )
        s3 = await self.run_synthesis_stroke(
            session, truth_packets, framing=framing_with_audit
        )
        results.append(s3)
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


def _parse_audit_findings(raw: str) -> Optional[list[str]]:
    """Best-effort extraction of the four-category fault list from a
    Mirror Auditor response.

    The Auditor persona is configured to emit findings in a numbered
    structure (RIGIDITY ERRORS / PATTERN-MATCHING / CONFIDENCE-EVIDENCE
    GAPS / DIMENSIONAL GREEDS). This parser splits on the numbered
    headers; if the response doesn't match the expected structure it
    returns None and the caller falls back to displaying raw_response.
    """
    import re
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
