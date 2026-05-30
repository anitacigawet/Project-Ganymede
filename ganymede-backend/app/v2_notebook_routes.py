"""Notebook-aware HTTP API (v2) — notebook lifecycle + Studio + Deep Research.

Sibling to :mod:`app.v2_routes` (which is session-aware). Both routers mount
under ``/api/v2`` but cover orthogonal concerns:

  - ``v2_routes``        Sessions / strokes / iterative engine / auth pill
  - ``v2_notebook_routes`` (this file)
                         Notebook create / configure / upload / Studio /
                         Deep Research — all long-running ops run as
                         background tasks polled via ``/api/v2/tasks/{id}``

These endpoints exist so consumers like the Realist substrate build
script and the Persona Expansion experiment can drive notebook lifecycle
end-to-end via HTTP instead of importing ``NotebookLMService`` directly.

Endpoint set:

  Notebook lifecycle:
    POST /api/v2/notebooks                         Create a new notebook
    POST /api/v2/notebooks/{id}/configure-persona  Apply an arbitrary persona
    POST /api/v2/notebooks/{id}/sources/url        Upload a URL source

  Studio outputs (long-running, returns task_id):
    POST /api/v2/notebooks/{id}/studio/audio
    POST /api/v2/notebooks/{id}/studio/video
    POST /api/v2/notebooks/{id}/studio/infographic

  Deep Research (long-running, returns task_id):
    POST /api/v2/notebooks/{id}/research

  Bridge provisioning (long-running, returns task_id):
    POST /api/v2/bridge/provision                  Create + foundations + packets + persona

  Task lifecycle:
    GET    /api/v2/tasks/{task_id}                 Status / result / error
    DELETE /api/v2/tasks/{task_id}                 Cancel an in-flight task
    GET    /api/v2/tasks                           List recent tasks (debug)

Hard-coded notebook IDs (``CHESS_ENGINE_ID``, ``MIRROR_AUDITOR_ID``) are
read-only by guardrail. The notebook-write endpoints refuse to operate on
them — see :func:`_check_writable`.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, ConfigDict, Field

from app.contracts import TruthPacket
from app.services.background_tasks import BackgroundTask, registry as task_registry

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v2", tags=["v2-notebook"])


# Where to drop Studio output files. Each task gets a subdirectory keyed
# by its task_id, e.g. media/abc123.../audio.mp4. Tunable via env so
# tests / containerised deployments can redirect.
_MEDIA_DIR = Path(os.environ.get("GANYMEDE_MEDIA_DIR", "media")).resolve()


def _get_svc():
    """Pull the singleton NotebookLMService from main.py at request time.

    Lazy to avoid the circular import (main imports the router; the
    router needs the orchestrator the main module owns).
    """
    from app.main import notebooklm_svc
    return notebooklm_svc


def _check_writable(notebook_id: str) -> None:
    """Refuse writes to the two read-only canonical notebooks.

    The Engine and Mirror Auditor are protected by guardrail. The named
    ``configure_chess_engine`` / ``configure_mirror_auditor`` methods on
    :class:`NotebookLMService` are the only sanctioned writers, and they
    don't accept arbitrary persona text. Any HTTP path that would let a
    consumer apply a non-canonical persona to one of those notebooks is
    a guardrail violation; we 403 it.
    """
    svc = _get_svc()
    if notebook_id in (svc.CHESS_ENGINE_ID, svc.MIRROR_AUDITOR_ID, svc.LEGACY_ENGINE_ID):
        raise HTTPException(
            status_code=403,
            detail=(
                f"Notebook {notebook_id} is a read-only canonical notebook. "
                "Use the named configure_chess_engine / configure_mirror_auditor "
                "primitives via the orchestrator if you need to refresh its persona."
            ),
        )


def _media_path(task_id: str, filename: str) -> str:
    """Return the absolute path Studio output should be written to."""
    task_dir = _MEDIA_DIR / task_id
    task_dir.mkdir(parents=True, exist_ok=True)
    return str(task_dir / filename)


# ---------------------------------------------------------------------------
# Notebook lifecycle
# ---------------------------------------------------------------------------

class CreateNotebookRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    title: str = Field(min_length=1, max_length=200)


class CreateNotebookResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    notebook_id: str
    title: str


class ConfigurePersonaRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    custom_prompt: str = Field(min_length=1, max_length=10_000)
    """NotebookLM enforces a 10,000-char limit on the persona field;
    we hard-cap here so a too-long submission fails fast with 422."""
    response_length: str = Field(default="LONGER")
    """One of ``SHORTER``, ``DEFAULT``, ``LONGER``."""


class ConfigurePersonaResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    notebook_id: str
    response_length: str
    persona_char_count: int


class UploadUrlRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    url: str = Field(min_length=1)


class UploadUrlResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    notebook_id: str
    url: str
    status: str  # "uploaded"


class UploadFileRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    path: str = Field(min_length=1)
    """Absolute path on the backend host to the file to upload.  Only
    same-host consumers can use this endpoint meaningfully — file paths
    in JSON over HTTP cross hosts at no one's benefit."""


class UploadFileResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    notebook_id: str
    path: str
    status: str  # "uploaded"


class QueryNotebookRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    query: str = Field(min_length=1)


class QueryNotebookResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    notebook_id: str
    query: str
    answer: str
    answer_chars: int


class DeleteNotebookResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    notebook_id: str
    deleted: bool


@router.post(
    "/notebooks",
    response_model=CreateNotebookResponse,
    status_code=201,
)
async def create_notebook(req: CreateNotebookRequest) -> CreateNotebookResponse:
    """Create a new NotebookLM notebook.

    Blocks for one cooldown-gated upstream call (typically 1-3 seconds).
    Returns the notebook ID the consumer then uses for configure / upload /
    Studio / Research calls.
    """
    svc = _get_svc()
    try:
        notebook_id = await svc.create_notebook(req.title)
    except Exception as exc:
        logger.exception("create_notebook failed for title=%r", req.title)
        raise HTTPException(status_code=500, detail=str(exc))
    return CreateNotebookResponse(notebook_id=notebook_id, title=req.title)


@router.post(
    "/notebooks/{notebook_id}/configure-persona",
    response_model=ConfigurePersonaResponse,
)
async def configure_persona(
    notebook_id: str,
    req: ConfigurePersonaRequest,
) -> ConfigurePersonaResponse:
    """Apply a custom persona to a non-canonical notebook.

    Refuses to operate on ``CHESS_ENGINE_ID`` / ``MIRROR_AUDITOR_ID`` /
    ``LEGACY_ENGINE_ID`` — those are read-only by guardrail.
    """
    _check_writable(notebook_id)
    svc = _get_svc()
    try:
        await svc.configure_persona(
            notebook_id=notebook_id,
            custom_prompt=req.custom_prompt,
            response_length=req.response_length,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except Exception as exc:
        logger.exception("configure_persona failed for notebook %s", notebook_id)
        raise HTTPException(status_code=500, detail=str(exc))
    return ConfigurePersonaResponse(
        notebook_id=notebook_id,
        response_length=req.response_length.upper(),
        persona_char_count=len(req.custom_prompt),
    )


@router.post(
    "/notebooks/{notebook_id}/sources/url",
    response_model=UploadUrlResponse,
)
async def upload_url(notebook_id: str, req: UploadUrlRequest) -> UploadUrlResponse:
    """Upload a URL source to a notebook.

    Blocks until ingestion completes (``wait=True`` upstream). For long
    transcripts (e.g. YouTube videos with no existing transcript), this
    can take 30s+ — cooldown gate enforces only the per-call floor.
    """
    _check_writable(notebook_id)
    svc = _get_svc()
    try:
        await svc.upload_url(notebook_id, req.url)
    except Exception as exc:
        logger.exception("upload_url failed for notebook %s", notebook_id)
        raise HTTPException(status_code=500, detail=str(exc))
    return UploadUrlResponse(notebook_id=notebook_id, url=req.url, status="uploaded")


@router.post(
    "/notebooks/{notebook_id}/sources/file",
    response_model=UploadFileResponse,
)
async def upload_file(notebook_id: str, req: UploadFileRequest) -> UploadFileResponse:
    """Upload a local file source to a notebook.

    Counterpart to ``/sources/url`` — accepts an absolute file path on the
    backend host and ingests it.  Used by the Persona Expansion experiment
    to seed a test notebook with the same ``docs/foundations/`` corpus the
    canonical Engine carries.  Blocks until ingestion completes upstream.
    """
    _check_writable(notebook_id)
    if not os.path.isfile(req.path):
        raise HTTPException(
            status_code=422,
            detail=f"File not found on backend host: {req.path}",
        )
    svc = _get_svc()
    try:
        await svc.upload_file(notebook_id, req.path)
    except Exception as exc:
        logger.exception("upload_file failed for notebook %s: %s", notebook_id, req.path)
        raise HTTPException(status_code=500, detail=str(exc))
    return UploadFileResponse(notebook_id=notebook_id, path=req.path, status="uploaded")


@router.post(
    "/notebooks/{notebook_id}/query",
    response_model=QueryNotebookResponse,
)
async def query_notebook(notebook_id: str, req: QueryNotebookRequest) -> QueryNotebookResponse:
    """Send a query to a specific notebook and return the answer.

    Generic counterpart of the session-based ``/sessions/{id}/synthesize``
    flow.  Synchronous — blocks for the duration of the upstream NotebookLM
    call (single cooldown-gated query, typically 5-30 s depending on persona
    response length).  No CORS / canonical-ID restriction: queries are
    read-only against the notebook, so the canonical Engine / Auditor are
    queryable here.  (Writes are the thing the guardrail blocks.)
    """
    svc = _get_svc()
    try:
        answer = await svc.query_notebook(notebook_id, req.query)
    except Exception as exc:
        logger.exception("query_notebook failed for notebook %s", notebook_id)
        raise HTTPException(status_code=500, detail=str(exc))
    return QueryNotebookResponse(
        notebook_id=notebook_id,
        query=req.query,
        answer=answer,
        answer_chars=len(answer),
    )


@router.delete(
    "/notebooks/{notebook_id}",
    response_model=DeleteNotebookResponse,
)
async def delete_notebook(notebook_id: str) -> DeleteNotebookResponse:
    """Delete a notebook by ID.

    Backed by :meth:`NotebookLMService.delete_notebook`, which hard-refuses
    to delete the canonical Engine / Mirror Auditor / Legacy Engine IDs
    (raises ``ValueError``, surfaced here as ``403``).  Used by the
    orchestrator's failed-oracle cleanup path and by operators running
    Persona-Expansion-style throwaway experiments who want to garbage-
    collect test notebooks afterwards.
    """
    svc = _get_svc()
    try:
        ok = await svc.delete_notebook(notebook_id)
    except ValueError as exc:
        raise HTTPException(status_code=403, detail=str(exc))
    except Exception as exc:
        logger.exception("delete_notebook failed for notebook %s", notebook_id)
        raise HTTPException(status_code=500, detail=str(exc))
    return DeleteNotebookResponse(notebook_id=notebook_id, deleted=bool(ok))


# ---------------------------------------------------------------------------
# Studio outputs (long-running — submit as background tasks)
# ---------------------------------------------------------------------------

class StudioAudioRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    instructions: str = Field(min_length=1)
    audio_format: str = Field(default="DEEP_DIVE")
    audio_length: str = Field(default="LONG")
    language: str = Field(default="en")
    download: bool = Field(
        default=True,
        description=(
            "When true (default), the task polls until the audio downloads "
            "and records the local path in ``result.downloaded_path``. "
            "When false, the task completes as soon as the create call "
            "returns a task_id; the caller polls NotebookLM separately."
        ),
    )


class StudioVideoRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    instructions: str = Field(min_length=1)
    video_format: str = Field(default="EXPLAINER")
    video_style: str = Field(default="CLASSIC")
    language: str = Field(default="en")
    download: bool = Field(default=True)


class StudioInfographicRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    instructions: str = Field(min_length=1)
    orientation: str = Field(default="PORTRAIT")
    detail_level: str = Field(default="DETAILED")
    style: str = Field(default="PROFESSIONAL")
    language: str = Field(default="en")
    download: bool = Field(default=True)


class TaskSubmittedResponse(BaseModel):
    """Response shape for every background-task-spawning endpoint.

    Returns 202 Accepted with the task_id the caller polls.
    """
    model_config = ConfigDict(extra="forbid")
    task_id: str
    kind: str
    notebook_id: Optional[str] = None
    status: str  # "running"
    poll_url: str
    """The URL the caller should ``GET`` to poll task status."""


def _submitted_response(task: BackgroundTask) -> TaskSubmittedResponse:
    return TaskSubmittedResponse(
        task_id=task.id,
        kind=task.kind,
        notebook_id=task.notebook_id,
        status=task.status,
        poll_url=f"/api/v2/tasks/{task.id}",
    )


@router.post(
    "/notebooks/{notebook_id}/studio/audio",
    response_model=TaskSubmittedResponse,
    status_code=202,
)
async def studio_audio(
    notebook_id: str,
    req: StudioAudioRequest,
) -> TaskSubmittedResponse:
    """Start an Audio Overview generation. Returns 202 + task_id immediately.

    Poll ``GET /api/v2/tasks/{task_id}`` until ``status == 'completed'``
    or ``'error'``. On completion, ``result.downloaded_path`` is the
    local MP4 path (if ``download=True``) and ``result.task_id`` is the
    NotebookLM-side task ID.

    Audio Overviews typically take 5-25 minutes.
    """
    _check_writable(notebook_id)
    svc = _get_svc()

    output_path: Optional[str] = None
    task_context: dict[str, Any] = {
        "instructions_len": len(req.instructions),
        "audio_format": req.audio_format,
        "audio_length": req.audio_length,
        "language": req.language,
        "download": req.download,
    }
    if req.download:
        import uuid as _uuid
        run_id = _uuid.uuid4().hex
        output_path = _media_path(run_id, "audio.mp4")
        task_context["run_id"] = run_id
        task_context["output_path"] = output_path

    async def _run():
        return await svc.generate_audio_overview(
            notebook_id=notebook_id,
            instructions=req.instructions,
            audio_format=req.audio_format,
            audio_length=req.audio_length,
            language=req.language,
            output_path=output_path,
        )

    task = await task_registry().submit(
        kind="audio",
        coro_factory=_run,
        notebook_id=notebook_id,
        context=task_context,
    )
    return _submitted_response(task)


@router.post(
    "/notebooks/{notebook_id}/studio/video",
    response_model=TaskSubmittedResponse,
    status_code=202,
)
async def studio_video(
    notebook_id: str,
    req: StudioVideoRequest,
) -> TaskSubmittedResponse:
    """Start a Video Overview generation. Returns 202 + task_id.

    Video Overviews typically take 10-15 minutes. Veo-3 Cinematic mode
    is roughly 30-40 min and requires a Google AI Ultra subscription.
    """
    _check_writable(notebook_id)
    svc = _get_svc()

    output_path = None
    task_context: dict[str, Any] = {
        "instructions_len": len(req.instructions),
        "video_format": req.video_format,
        "video_style": req.video_style,
        "language": req.language,
        "download": req.download,
    }

    if req.download:
        import uuid as _uuid
        run_id = _uuid.uuid4().hex
        output_path = _media_path(run_id, "video.mp4")
        task_context["run_id"] = run_id
        task_context["output_path"] = output_path

    async def _run():
        return await svc.generate_video_overview(
            notebook_id=notebook_id,
            instructions=req.instructions,
            video_format=req.video_format,
            video_style=req.video_style,
            language=req.language,
            output_path=output_path,
        )

    task = await task_registry().submit(
        kind="video",
        coro_factory=_run,
        notebook_id=notebook_id,
        context=task_context,
    )
    return _submitted_response(task)


@router.post(
    "/notebooks/{notebook_id}/studio/infographic",
    response_model=TaskSubmittedResponse,
    status_code=202,
)
async def studio_infographic(
    notebook_id: str,
    req: StudioInfographicRequest,
) -> TaskSubmittedResponse:
    """Start an Infographic generation. Returns 202 + task_id.

    Infographics typically take 3-10 minutes.
    """
    _check_writable(notebook_id)
    svc = _get_svc()

    output_path = None
    task_context: dict[str, Any] = {
        "instructions_len": len(req.instructions),
        "orientation": req.orientation,
        "detail_level": req.detail_level,
        "style": req.style,
        "language": req.language,
        "download": req.download,
    }

    if req.download:
        import uuid as _uuid
        run_id = _uuid.uuid4().hex
        output_path = _media_path(run_id, "infographic.png")
        task_context["run_id"] = run_id
        task_context["output_path"] = output_path

    async def _run():
        return await svc.generate_infographic(
            notebook_id=notebook_id,
            instructions=req.instructions,
            orientation=req.orientation,
            detail_level=req.detail_level,
            style=req.style,
            language=req.language,
            output_path=output_path,
        )

    task = await task_registry().submit(
        kind="infographic",
        coro_factory=_run,
        notebook_id=notebook_id,
        context=task_context,
    )
    return _submitted_response(task)


# ---------------------------------------------------------------------------
# Deep Research
# ---------------------------------------------------------------------------

class ResearchRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    query: str = Field(min_length=1)
    source: str = Field(default="web")
    """``web`` or ``drive``. ``drive`` only supports ``mode='fast'``."""
    mode: str = Field(default="deep")
    """``deep`` or ``fast``. Deep is web-only."""
    auto_import: bool = Field(
        default=False,
        description=(
            "If true, all returned sources are imported back into the "
            "notebook on completion. Off by default — most callers want "
            "to inspect the source list first."
        ),
    )
    max_sources: Optional[int] = Field(default=None, ge=1, le=300)
    poll_interval: Optional[float] = Field(default=None, gt=0, le=600)
    timeout: Optional[float] = Field(default=None, gt=0, le=7200)


@router.post(
    "/notebooks/{notebook_id}/research",
    response_model=TaskSubmittedResponse,
    status_code=202,
)
async def start_research(
    notebook_id: str,
    req: ResearchRequest,
) -> TaskSubmittedResponse:
    """Kick off a Deep Research run against a notebook. Returns 202 + task_id.

    Deep Research typically takes 5-30 minutes. On completion,
    ``result`` contains ``{task_id, status, query, sources, summary,
    report, imported}``.
    """
    _check_writable(notebook_id)
    svc = _get_svc()

    async def _run():
        return await svc.run_deep_research(
            notebook_id=notebook_id,
            query=req.query,
            source=req.source,
            mode=req.mode,
            poll_interval=req.poll_interval,
            timeout=req.timeout,
            auto_import=req.auto_import,
            max_sources=req.max_sources,
        )

    task = await task_registry().submit(
        kind="research",
        coro_factory=_run,
        notebook_id=notebook_id,
        context={
            "query_len": len(req.query),
            "source": req.source,
            "mode": req.mode,
            "auto_import": req.auto_import,
        },
    )
    return _submitted_response(task)


# ---------------------------------------------------------------------------
# Task lifecycle
# ---------------------------------------------------------------------------

class TaskStatusResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    task_id: str
    kind: str
    notebook_id: Optional[str] = None
    status: str  # running | completed | error
    result: Optional[dict] = None
    error_message: Optional[str] = None
    exc_type: Optional[str] = None
    created_at: str
    completed_at: Optional[str] = None


class TaskListResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    tasks: list[TaskStatusResponse]


class TaskCancelResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    task_id: str
    cancelled: bool


@router.get("/tasks/{task_id}", response_model=TaskStatusResponse)
async def get_task(task_id: str) -> TaskStatusResponse:
    """Poll a background task for status / result / error."""
    task = task_registry().get(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail=f"Task not found: {task_id}")
    return TaskStatusResponse(**task.to_dict())


@router.delete("/tasks/{task_id}", response_model=TaskCancelResponse)
async def cancel_task(task_id: str) -> TaskCancelResponse:
    """Cancel an in-flight task. Returns ``cancelled=False`` if the task
    has already completed (in which case the result/error is preserved).
    """
    cancelled = await task_registry().cancel(task_id)
    if not cancelled and task_registry().get(task_id) is None:
        raise HTTPException(status_code=404, detail=f"Task not found: {task_id}")
    return TaskCancelResponse(task_id=task_id, cancelled=cancelled)


@router.get("/tasks", response_model=TaskListResponse)
async def list_tasks() -> TaskListResponse:
    """List all tasks in the registry. For operator debug; not paginated."""
    tasks = task_registry().list_all()
    return TaskListResponse(
        tasks=[TaskStatusResponse(**t.to_dict()) for t in tasks],
    )


# ---------------------------------------------------------------------------
# Bridge provisioning helper — Bicameral Convergence Level 1 setup.
#
# /api/v2/sessions/{id}/bridge-audit (in v2_routes.py) requires a pre-
# provisioned Bridge notebook. Without help, the caller has to: create the
# notebook + upload all 13 foundations corpus files + upload the scenario's
# Truth Packets + remember to apply the persona — ~15+ NotebookLM calls and
# multiple endpoint hits.
#
# This helper bundles all of that into one background-task call. Caller
# polls the returned task_id; on completion, task.result.notebook_id is
# ready to pass to /bridge-audit directly.
# ---------------------------------------------------------------------------


# Default location of the foundations corpus, relative to this file.
# Resolve once at import; can be overridden via GANYMEDE_FOUNDATIONS_DIR.
#   __file__ = .../ganymede-backend/app/v2_notebook_routes.py
#   .parent  = .../ganymede-backend/app
#   .parent  = .../ganymede-backend
#   .parent  = .../Project Ganymede  (the project root)
_DEFAULT_FOUNDATIONS_DIR = (
    Path(__file__).resolve().parent.parent.parent / "docs" / "foundations"
)


def _foundations_dir() -> Path:
    """Resolved foundations corpus directory. Env-overridable for tests."""
    override = os.environ.get("GANYMEDE_FOUNDATIONS_DIR")
    return Path(override) if override else _DEFAULT_FOUNDATIONS_DIR


class BridgeProvisionRequest(BaseModel):
    """Provision a Bridge notebook in one background-task call.

    Bundles four steps that otherwise require ~15 separate HTTP requests:

      1. Create a new (non-canonical) NotebookLM notebook.
      2. Upload the foundations corpus (``docs/foundations/`` — every
         ``.md`` / ``.pdf`` / ``.txt`` file except ``README.md``).
      3. Upload the supplied Truth Packets (each written to a temp ``.md``
         file with the packet's subject as title and source_label as
         attribution, then uploaded).
      4. Apply the Connection Bridge persona via
         ``configure_connection_bridge``.

    On completion, ``task.result.notebook_id`` is ready to pass directly
    to ``POST /api/v2/sessions/{id}/bridge-audit``. See
    ``docs/concepts/Bicameral_Convergence.md`` for the architectural framing.

    Operational cost: ~15+ NotebookLM calls total (one per foundation file
    + one per Truth Packet + one persona apply + one notebook create).
    With the 8s cooldown floor this is typically 3-5 minutes wall time.
    The Truth-Packet upload calls are serialised through the cooldown
    gate; the wrapper handles retry on transient failures.
    """
    model_config = ConfigDict(extra="forbid")
    title: Optional[str] = Field(
        default=None,
        max_length=200,
        description=(
            "Notebook title. Defaults to "
            "'Bridge — <first truth_packet subject>' if omitted. "
            "Truncated to 200 chars."
        ),
    )
    truth_packets: list[TruthPacket] = Field(
        min_length=1,
        description=(
            "Truth Packets to upload to the Bridge notebook. Should "
            "match the substrate the Engine reasoned over for the "
            "scenario being audited — typically the same packet list "
            "you'd pass to /api/v2/sessions/{id}/iterate or /synthesize."
        ),
    )
    include_foundations: bool = Field(
        default=True,
        description=(
            "Whether to also upload the docs/foundations/ corpus. "
            "Defaults to True (the expected case for actual Bridge use). "
            "Set False only for testing, or if foundations are pre-loaded "
            "via a different mechanism."
        ),
    )


@router.post(
    "/bridge/provision",
    response_model=TaskSubmittedResponse,
    status_code=202,
)
async def bridge_provision(req: BridgeProvisionRequest) -> TaskSubmittedResponse:
    """Provision a Bridge notebook end-to-end. Returns 202 + task_id immediately.

    Poll ``GET /api/v2/tasks/{task_id}`` until ``status == 'completed'`` or
    ``'error'``. On completion, ``result`` contains:

    .. code-block:: json

        {
          "notebook_id": "<uuid>",
          "title": "Bridge — Scenario",
          "foundations_uploaded": 13,
          "truth_packets_uploaded": 1,
          "sources_total": 14,
          "bridge_persona_applied": true
        }

    The ``notebook_id`` is then passed directly to
    ``POST /api/v2/sessions/{id}/bridge-audit``.

    Errors (raised inside the task and surfaced via task.error_message):
        ``RuntimeError`` if the foundations directory isn't found and
        ``include_foundations=True`` (caller should set
        ``GANYMEDE_FOUNDATIONS_DIR`` or use the default project layout).
        Any NotebookLM upload / create / persona-apply failure surfaces
        with its original exception type.

    Note: notebook lifecycle is NOT auto-managed. On task error the
    partial notebook (if create succeeded) is NOT auto-deleted — caller
    can clean up via ``DELETE /api/v2/notebooks/{id}`` if desired, or
    inspect for debugging. This is intentional: a partial-upload notebook
    may still be useful to retry against.
    """
    title = (req.title or f"Bridge — {req.truth_packets[0].subject[:60]}")[:200]

    task_context: dict[str, Any] = {
        "title": title,
        "truth_packet_subjects": [tp.subject for tp in req.truth_packets],
        "truth_packet_count": len(req.truth_packets),
        "include_foundations": req.include_foundations,
    }

    # Capture by value into the closure so the request body can be GC'd.
    truth_packets = list(req.truth_packets)
    include_foundations = req.include_foundations
    # Apply the env-var resolution at submit time (vs deferring to the
    # orchestrator method's default) so a missing dir fails fast on the
    # background task instead of partway through 14 upload calls.
    explicit_foundations_dir = _foundations_dir() if include_foundations else None

    async def _run() -> dict[str, Any]:
        from app.main import orchestrator as _orch
        return await _orch.provision_bridge_notebook(
            truth_packets=truth_packets,
            title=title,
            include_foundations=include_foundations,
            foundations_dir=explicit_foundations_dir,
        )

    task = await task_registry().submit(
        kind="bridge_provision",
        coro_factory=_run,
        notebook_id=None,  # not known until _run starts
        context=task_context,
    )
    return _submitted_response(task)
