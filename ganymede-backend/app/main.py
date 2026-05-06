"""Project Ganymede backend — HTTP API.

Exposes the Universal Logic Loop primitives as discrete endpoints. There is
no monolithic "run the whole loop" endpoint on purpose: the runaway-
prevention guardrail requires explicit per-step caller intent, especially
around oracle creation.

See:
    - ``docs/protocols/Universal_Logic_Loop_Protocol.md``
    - ``docs/protocols/Master_Operational_Workflow.md``
    - ``docs/protocols/PKI_Oracle_Persona.md``
"""

from __future__ import annotations

import logging
from typing import Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from app.services.notebooklm_service import NotebookLMService
from app.services.orchestrator import GanymedeOrchestrator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Project Ganymede Backend",
    description=(
        "Universal Logic Loop primitives over the 9D Chess Engine and the "
        "PKI Authentication Oracle swarm. See the docs/ tree for protocol."
    ),
)

notebooklm_svc = NotebookLMService()
orchestrator = GanymedeOrchestrator(notebooklm_svc)


# ---------------------------------------------------------------------------
# Lifecycle
# ---------------------------------------------------------------------------

@app.on_event("startup")
async def startup_event() -> None:
    try:
        await notebooklm_svc.initialize()
        logger.info("NotebookLM client initialized.")
    except Exception as exc:
        logger.error("Failed to initialize NotebookLM client: %s", exc)


@app.on_event("shutdown")
async def shutdown_event() -> None:
    await notebooklm_svc.close()


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------

@app.get("/api/health")
async def health_check() -> dict[str, str]:
    return {"status": "healthy"}


# ---------------------------------------------------------------------------
# Phase 1 — Triage
# ---------------------------------------------------------------------------

class TriageRequest(BaseModel):
    scenario: str
    max_subjects: int = Field(3, ge=1, le=10)
    prompt: Optional[str] = None


class TriageResponse(BaseModel):
    hit_list_raw: str  # raw Umpire output; caller parses


@app.post("/api/triage", response_model=TriageResponse)
async def triage(req: TriageRequest) -> TriageResponse:
    """Phase 1. Submit a scenario, receive a Strategic Hit List."""
    try:
        raw = await orchestrator.triage(
            req.scenario,
            max_subjects=req.max_subjects,
            prompt=req.prompt,
        )
        return TriageResponse(hit_list_raw=raw)
    except Exception as exc:
        logger.exception("triage failed")
        raise HTTPException(status_code=500, detail=str(exc))


# ---------------------------------------------------------------------------
# Phase 2 — Swarm
# ---------------------------------------------------------------------------

class OracleCreateRequest(BaseModel):
    subject: str
    surgical_prompt: str


class OracleCreateResponse(BaseModel):
    subject: str
    full_name: str
    notebook_id: str
    hash_suffix: str


@app.post("/api/oracle", response_model=OracleCreateResponse)
async def create_oracle(req: OracleCreateRequest) -> OracleCreateResponse:
    """Phase 2 step 1. Create exactly one persona-locked PKI Oracle.

    Each call creates ONE notebook. To create a swarm of N, call this
    endpoint N times — each call requires explicit caller intent.
    """
    try:
        h = await orchestrator.create_oracle(req.subject, req.surgical_prompt)
        return OracleCreateResponse(
            subject=h.subject,
            full_name=h.full_name,
            notebook_id=h.notebook_id,
            hash_suffix=h.hash_suffix,
        )
    except Exception as exc:
        logger.exception("create_oracle failed")
        raise HTTPException(status_code=500, detail=str(exc))


class GoSignalRequest(BaseModel):
    prompt: Optional[str] = None


@app.post("/api/oracle/{oracle_id}/go")
async def oracle_go(oracle_id: str, req: GoSignalRequest) -> dict:
    """Phase 2 step 2. Trigger the Deep Research web scour."""
    try:
        result = await orchestrator.send_go(oracle_id, req.prompt)
        return {"oracle_id": oracle_id, "response": result}
    except Exception as exc:
        logger.exception("oracle_go failed")
        raise HTTPException(status_code=500, detail=str(exc))


class HarvestRequest(BaseModel):
    prompt: Optional[str] = None


@app.post("/api/oracle/{oracle_id}/harvest")
async def oracle_harvest(oracle_id: str, req: HarvestRequest) -> dict:
    """Phase 2 step 3. Extract the Truth Packet (post-Import in the UI)."""
    try:
        packet = await orchestrator.harvest(oracle_id, req.prompt)
        return {"oracle_id": oracle_id, "truth_packet": packet}
    except Exception as exc:
        logger.exception("harvest failed")
        raise HTTPException(status_code=500, detail=str(exc))


class HarvestSwarmRequest(BaseModel):
    oracles: dict[str, str]  # subject -> notebook_id
    prompt: Optional[str] = None


@app.post("/api/swarm/harvest")
async def swarm_harvest(req: HarvestSwarmRequest) -> dict:
    """Convenience: parallel-harvest a whole swarm."""
    try:
        packets = await orchestrator.harvest_swarm(req.oracles, req.prompt)
        return {"truth_packets": packets}
    except Exception as exc:
        logger.exception("swarm_harvest failed")
        raise HTTPException(status_code=500, detail=str(exc))


# ---------------------------------------------------------------------------
# Phase 3 — Synthesis
# ---------------------------------------------------------------------------

class SynthesizeRequest(BaseModel):
    scenario: str
    truth_packets: dict[str, str]  # subject -> packet
    framing: Optional[str] = None


@app.post("/api/synthesize")
async def synthesize(req: SynthesizeRequest) -> dict:
    """Phase 3. Holistic re-analysis with authenticated Truth Packets."""
    try:
        resolution = await orchestrator.synthesize(
            req.scenario,
            req.truth_packets,
            framing=req.framing,
        )
        return {"resolution": resolution}
    except Exception as exc:
        logger.exception("synthesize failed")
        raise HTTPException(status_code=500, detail=str(exc))


# ---------------------------------------------------------------------------
# Phase 4 — Recursive Dialogue
# ---------------------------------------------------------------------------

@app.post("/api/resolution-check")
async def resolution_check_endpoint(req: HarvestRequest) -> dict:
    """Phase 4. Ask the Umpire if it has enough resolution."""
    try:
        result = await orchestrator.resolution_check(req.prompt)
        return {"response": result}
    except Exception as exc:
        logger.exception("resolution_check failed")
        raise HTTPException(status_code=500, detail=str(exc))


# ---------------------------------------------------------------------------
# Backward-compatibility: legacy /api/orchestrate endpoint
#
# Preserved so the existing frontend Cortex Clipboard flow keeps working
# unchanged. New work should prefer the granular phase endpoints above.
# ---------------------------------------------------------------------------

class OrchestrateRequest(BaseModel):
    query: str
    notebook_id: str


class OrchestrateResponse(BaseModel):
    status: str
    structured_prompt: str


@app.post("/api/orchestrate", response_model=OrchestrateResponse)
async def orchestrate(req: OrchestrateRequest) -> OrchestrateResponse:
    """Legacy single-shot endpoint.

    Queries an arbitrary notebook (typically the Umpire) for the canonical
    Phase-1 composite query (factual analysis + visualization strategy)
    and returns a Gemini-Compiler-ready structured prompt block. Used by
    the frontend Cortex Clipboard.
    """
    try:
        composite_query = """
        1. Perform a 9D Strategic Analysis on this scenario.
        2. Based on this analysis, what is the best way to visualize this scenario in a 3D topological simulation?
           Describe the 'Gravity Well' (SDS), the tension between nodes, and how the grid should warp to accurately represent the point of system failure.
        """
        composite_analysis = await notebooklm_svc.query_notebook(
            req.notebook_id, composite_query
        )

        structured_prompt = f"""
# SYSTEM DIRECTIVE
You are the Ganymede Compiler. Your task is to visualize and model the strategic landscape based on the following factual 9D analysis and the suggested visualization parameters from the Umpire.

# UMPIRE COMPOSITE DATA (Analysis & Strategy)
{composite_analysis.strip()}

# OUTPUT INSTRUCTION
Based on the specific strategy above, provide the final simulation parameters in our standardized JSON format for the Ganymede frontend:
```json
{{
  "stress": <number 0-100>,
  "blindness": <number 0-100>,
  "description": "<detailed summary of how the topology is warping based on the Umpire's strategy>"
}}
```
"""
        return OrchestrateResponse(
            status="success",
            structured_prompt=structured_prompt.strip(),
        )
    except Exception as exc:
        logger.error("orchestrate failed: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))
