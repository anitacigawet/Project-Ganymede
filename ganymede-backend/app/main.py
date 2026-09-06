"""Project Ganymede local API.

The default runtime is deliberately local-first: FastAPI binds to loopback
through the supplied launcher, analytical work runs through the authenticated
Claude CLI, and external research grants the CLI only its built-in WebSearch
tool. Session state is stored under ``ganymede-backend/data`` by default.
"""

from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional

try:
    from dotenv import load_dotenv

    load_dotenv(Path(__file__).resolve().parents[1] / ".env")
except ImportError:
    pass

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from app.services.claude_runtime import ClaudeRuntimeService
from app.services.orchestrator import GanymedeOrchestrator
from app.services.session import registry as session_registry
from app.services.session_store import SessionStore, default_db_path

logging.basicConfig(
    level=os.environ.get("GANYMEDE_LOG_LEVEL", "INFO").upper(),
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

runtime = ClaudeRuntimeService()
orchestrator = GanymedeOrchestrator(runtime)


@asynccontextmanager
async def lifespan(_: FastAPI):
    if os.environ.get("GANYMEDE_DISABLE_SESSION_PERSISTENCE") != "1":
        db_path = os.environ.get("GANYMEDE_SESSION_DB", str(default_db_path()))
        try:
            store = SessionStore(db_path)
            session_registry().bind_store(store)
            count = await session_registry().rehydrate()
            logger.info("Session store ready at %s (%d restored)", db_path, count)
        except Exception:
            logger.exception("Session persistence unavailable; using memory only")
    await runtime.initialize()
    try:
        yield
    finally:
        # Stop owned drivers before clearing their runtime context.
        for session in session_registry().list_all():
            await session.request_cancel("Backend stopping")
        await runtime.close()


app = FastAPI(
    title="Project Ganymede",
    version="1.0.0",
    description=(
        "Local-first multi-stroke strategic analysis using the 9D foundation "
        "corpus, Claude CLI, and optional WebSearch harvesting."
    ),
    lifespan=lifespan,
)

default_origins = (
    "http://localhost:3000,http://127.0.0.1:3000,"
    "http://localhost:3001,http://127.0.0.1:3001"
)
origins = [
    origin.strip()
    for origin in os.environ.get("GANYMEDE_CORS_ORIGINS", default_origins).split(",")
    if origin.strip()
]
origin_regex = os.environ.get("GANYMEDE_CORS_ORIGIN_REGEX") or None
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_origin_regex=origin_regex,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

from app.v2_routes import router as v2_router  # noqa: E402

app.include_router(v2_router)


@app.get("/api/health")
async def health_check() -> dict[str, object]:
    provider = runtime.provider_status()
    return {
        "status": "healthy" if provider["available"] else "setup_required",
        "provider": provider,
    }


class TriageRequest(BaseModel):
    scenario: str = Field(min_length=1)
    max_subjects: int = Field(3, ge=1, le=10)
    prompt: Optional[str] = None


class TriageResponse(BaseModel):
    hit_list_raw: str


@app.post("/api/triage", response_model=TriageResponse)
async def triage(req: TriageRequest) -> TriageResponse:
    try:
        raw = await orchestrator.triage(
            req.scenario,
            max_subjects=req.max_subjects,
            prompt=req.prompt,
        )
        return TriageResponse(hit_list_raw=raw)
    except Exception as exc:
        logger.exception("Triage failed")
        raise HTTPException(status_code=500, detail=str(exc)) from exc


class DirectSynthesisRequest(BaseModel):
    scenario: str = Field(min_length=1)
    truth_packets: dict[str, str] = Field(min_length=1)
    framing: Optional[str] = None


@app.post("/api/synthesize")
async def synthesize(req: DirectSynthesisRequest) -> dict[str, str]:
    try:
        result = await orchestrator.synthesize(
            req.scenario,
            req.truth_packets,
            framing=req.framing,
        )
        return {"resolution": result}
    except Exception as exc:
        logger.exception("Synthesis failed")
        raise HTTPException(status_code=500, detail=str(exc)) from exc
