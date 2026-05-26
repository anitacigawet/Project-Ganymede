"""NotebookLM Studio output methods — audio / video / infographic generation.

Mixin into :class:`~app.services.notebooklm.client.NotebookLMService`. Each
public method (``generate_audio_overview``, ``generate_video_overview``,
``generate_infographic``) wraps the upstream ``notebooklm.artifacts`` API
with cooldown discipline, silent-rejection retry, and download polling that
bypasses the wrapper's ``wait_for_completion`` quirks.

Pattern adapted from the Z-SPAN bridge — see
``_scratch/Z-SPAN/02_Core_Project/notebooklm_bridge/client.py`` and the
``STUDIO_REFERENCE.md`` next to it for the UI-mapped enum reference.

Why a mixin and not a free-standing service: every Studio call wants the same
``self.client`` and the same module-global cooldown gate as the chat/query
path. Composing them on one class keeps callers from juggling two service
objects.
"""

from __future__ import annotations

import asyncio
import logging
import os
import time

from .cooldown import _GATE

logger = logging.getLogger(__name__)


# Generation timeouts (seconds). Studio media takes minutes; defaults are
# generous. Override with GANYMEDE_NOTEBOOKLM_* env vars if NotebookLM speeds
# up or we want shorter waits during testing.
_STUDIO_TIMEOUT_AUDIO = float(os.environ.get("GANYMEDE_NOTEBOOKLM_AUDIO_TIMEOUT", "1500"))
_STUDIO_TIMEOUT_VIDEO = float(os.environ.get("GANYMEDE_NOTEBOOKLM_VIDEO_TIMEOUT", "1800"))
_STUDIO_TIMEOUT_INFOGRAPHIC = float(os.environ.get("GANYMEDE_NOTEBOOKLM_INFOGRAPHIC_TIMEOUT", "600"))

# Silent-rejection retry config. Sometimes NotebookLM accepts an artifact-create
# call (HTTP 200) but returns an empty task_id, which means Google quietly
# refused to actually kick off the generation. There's no error to catch — the
# response just has no task to track. Without a guard we'd poll a non-existent
# task for the full timeout (~25 min for audio) and only then fail.
#
# When we see an empty task_id we retry the create call up to
# GANYMEDE_NOTEBOOKLM_STUDIO_CREATE_MAX_ATTEMPTS times with exponential backoff,
# then give up cleanly with status="silent_rejection" so the caller can mark
# the output as a dud and move on. The polling/download path is untouched.
_STUDIO_CREATE_MAX_ATTEMPTS = int(
    os.environ.get("GANYMEDE_NOTEBOOKLM_STUDIO_CREATE_MAX_ATTEMPTS", "3")
)
_STUDIO_CREATE_BACKOFF_BASE = float(
    os.environ.get("GANYMEDE_NOTEBOOKLM_STUDIO_CREATE_BACKOFF", "60.0")
)


class StudioSilentRejection(RuntimeError):
    """Studio create call returned 200 OK with an empty task_id — Google
    silently refused to start the generation.

    Retried automatically inside the mixin; only surfaces when retries are
    exhausted. Public so callers can catch it explicitly if they want
    finer-grained handling than the ``status="silent_rejection"`` return.
    """


class _StudioMixin:
    """Studio output methods. Mixed into ``NotebookLMService``.

    Requires the host class to expose ``self.client`` (the underlying
    ``notebooklm-py`` client, populated by ``initialize()``).
    """

    # ------------------------------------------------------- private helpers

    async def _poll_studio_download(
        self,
        download_callable,
        notebook_id: str,
        artifact_id: str,
        output_path: str,
        timeout_seconds: float,
        artifact_label: str,
    ) -> str | None:
        """Poll the wrapper's download_* function with backoff.

        Bypasses ``wait_for_completion``, which has been observed to get
        stuck downgrading COMPLETED to PROCESSING via ``_is_media_ready``.
        The download function does its own COMPLETED-status check and
        succeeds the moment the artifact is truly ready.

        Returns the downloaded path, or None on timeout.

        ``download_callable`` must be an async function with signature::

            (notebook_id, output_path, artifact_id) -> str
        """
        from notebooklm.types import ArtifactNotReadyError, ArtifactDownloadError

        deadline = time.monotonic() + timeout_seconds
        delay = 30.0  # seconds between download attempts; gentle on the API
        attempt = 0
        while True:
            attempt += 1
            await _GATE.acquire()
            try:
                path = await download_callable(
                    notebook_id=notebook_id,
                    output_path=output_path,
                    artifact_id=artifact_id,
                )
                logger.info(
                    "%s: download succeeded on attempt %d (id=%s)",
                    artifact_label, attempt, artifact_id,
                )
                return path
            except (ArtifactNotReadyError, ArtifactDownloadError) as e:
                logger.debug(
                    "%s: not ready on attempt %d (%s)",
                    artifact_label, attempt, e,
                )
            except Exception:
                logger.exception(
                    "%s: unexpected download error on attempt %d",
                    artifact_label, attempt,
                )
                raise

            remaining = deadline - time.monotonic()
            if remaining <= 0:
                logger.warning(
                    "%s: download timed out after %.0fs (id=%s)",
                    artifact_label, timeout_seconds, artifact_id,
                )
                return None
            await asyncio.sleep(min(delay, remaining))

    async def _create_studio_with_retry(self, label: str, create_callable):
        """Run a studio artifact-create call with retry on silent rejection.

        After ``_STUDIO_CREATE_MAX_ATTEMPTS`` empty responses we give up and
        raise :class:`StudioSilentRejection` — the public methods catch this
        and surface ``status="silent_rejection"`` so the caller can mark the
        output as a dud and move on.

        ``create_callable`` is a zero-arg async callable that performs the
        actual create RPC and returns the wrapper's GenerationResult
        (with ``.task_id``).
        """
        for attempt in range(1, _STUDIO_CREATE_MAX_ATTEMPTS + 1):
            await _GATE.acquire()
            gen = await create_callable()

            task_id = getattr(gen, "task_id", None)
            if task_id:
                if attempt > 1:
                    logger.info(
                        "%s: create succeeded on attempt %d after silent rejection(s)",
                        label, attempt,
                    )
                return gen

            logger.warning(
                "%s: silent rejection (empty task_id) on attempt %d/%d",
                label, attempt, _STUDIO_CREATE_MAX_ATTEMPTS,
            )
            if attempt < _STUDIO_CREATE_MAX_ATTEMPTS:
                backoff = _STUDIO_CREATE_BACKOFF_BASE * attempt
                logger.info("%s: retrying create in %.0fs", label, backoff)
                await asyncio.sleep(backoff)

        raise StudioSilentRejection(
            f"{label}: NotebookLM silently rejected create "
            f"{_STUDIO_CREATE_MAX_ATTEMPTS} times (empty task_id each time)"
        )

    # ----------------------------------------------------------- audio

    async def generate_audio_overview(
        self,
        notebook_id: str,
        instructions: str,
        audio_format: str = "DEEP_DIVE",
        audio_length: str = "LONG",
        language: str = "en",
        output_path: str | None = None,
    ) -> dict:
        """Generate an Audio Overview ("Deep Dive" podcast).

        Returns ``{ task_id, status, is_complete, downloaded_path }``.
        ``status`` is one of: ``"ok"``, ``"timeout"``, ``"silent_rejection"``.

        On silent rejection (Google returns HTTP 200 + empty task_id) we
        retry the create up to ``_STUDIO_CREATE_MAX_ATTEMPTS`` times before
        returning the rejection status.

        :param audio_format: One of DEEP_DIVE / BRIEF / CRITIQUE / DEBATE.
        :param audio_length: One of SHORT / DEFAULT / LONG.
        :param output_path: If provided, blocks until the audio downloads
            (or until ``_STUDIO_TIMEOUT_AUDIO`` elapses). If None, returns
            immediately after the create succeeds; caller polls.
        """
        if not self.client:
            raise Exception("NotebookLMClient is not initialized.")
        from notebooklm.rpc import AudioFormat, AudioLength

        fmt = AudioFormat[audio_format]
        length = AudioLength[audio_length]

        async def _create():
            return await self.client.artifacts.generate_audio(
                notebook_id=notebook_id,
                instructions=instructions,
                audio_format=fmt,
                audio_length=length,
                language=language,
            )

        try:
            gen = await self._create_studio_with_retry("audio", _create)
        except StudioSilentRejection as e:
            logger.error(str(e))
            return {
                "task_id": None,
                "status": "silent_rejection",
                "is_complete": False,
                "downloaded_path": None,
            }

        logger.info(
            "audio: task %s queued, polling download up to %.0fs",
            gen.task_id, _STUDIO_TIMEOUT_AUDIO,
        )
        downloaded = None
        if output_path:
            downloaded = await self._poll_studio_download(
                download_callable=self.client.artifacts.download_audio,
                notebook_id=notebook_id,
                artifact_id=gen.task_id,
                output_path=output_path,
                timeout_seconds=_STUDIO_TIMEOUT_AUDIO,
                artifact_label="audio",
            )
        return {
            "task_id": gen.task_id,
            "status": "ok" if downloaded else ("timeout" if output_path else "ok"),
            "is_complete": downloaded is not None,
            "downloaded_path": downloaded,
        }

    # ----------------------------------------------------------- video

    async def generate_video_overview(
        self,
        notebook_id: str,
        instructions: str,
        video_format: str = "EXPLAINER",
        video_style: str = "CLASSIC",
        language: str = "en",
        output_path: str | None = None,
    ) -> dict:
        """Generate a Video Overview.

        See :meth:`generate_audio_overview` for the return contract.

        :param video_format: EXPLAINER or BRIEF.
        :param video_style: One of AUTO_SELECT / CUSTOM / CLASSIC / WHITEBOARD
            / KAWAII / ANIME / WATERCOLOR / RETRO_PRINT / HERITAGE / PAPER_CRAFT.
        """
        if not self.client:
            raise Exception("NotebookLMClient is not initialized.")
        from notebooklm.rpc import VideoFormat, VideoStyle

        fmt = VideoFormat[video_format]
        style = VideoStyle[video_style]

        async def _create():
            return await self.client.artifacts.generate_video(
                notebook_id=notebook_id,
                instructions=instructions,
                video_format=fmt,
                video_style=style,
                language=language,
            )

        try:
            gen = await self._create_studio_with_retry("video", _create)
        except StudioSilentRejection as e:
            logger.error(str(e))
            return {
                "task_id": None,
                "status": "silent_rejection",
                "is_complete": False,
                "downloaded_path": None,
            }

        logger.info(
            "video: task %s queued, polling download up to %.0fs",
            gen.task_id, _STUDIO_TIMEOUT_VIDEO,
        )
        downloaded = None
        if output_path:
            downloaded = await self._poll_studio_download(
                download_callable=self.client.artifacts.download_video,
                notebook_id=notebook_id,
                artifact_id=gen.task_id,
                output_path=output_path,
                timeout_seconds=_STUDIO_TIMEOUT_VIDEO,
                artifact_label="video",
            )
        return {
            "task_id": gen.task_id,
            "status": "ok" if downloaded else ("timeout" if output_path else "ok"),
            "is_complete": downloaded is not None,
            "downloaded_path": downloaded,
        }

    # ----------------------------------------------------------- infographic

    async def generate_infographic(
        self,
        notebook_id: str,
        instructions: str,
        orientation: str = "PORTRAIT",
        detail_level: str = "DETAILED",
        style: str = "PROFESSIONAL",
        language: str = "en",
        output_path: str | None = None,
    ) -> dict:
        """Generate an Infographic (PNG).

        See :meth:`generate_audio_overview` for the return contract.

        :param orientation: LANDSCAPE / PORTRAIT / SQUARE.
        :param detail_level: CONCISE / STANDARD / DETAILED.
        :param style: AUTO_SELECT / SKETCH_NOTE / PROFESSIONAL / BENTO_GRID
            / EDITORIAL / INSTRUCTIONAL / BRICKS / CLAY / ANIME / KAWAII
            / SCIENTIFIC.
        """
        if not self.client:
            raise Exception("NotebookLMClient is not initialized.")
        from notebooklm.rpc import (
            InfographicOrientation,
            InfographicDetail,
            InfographicStyle,
        )

        orient = InfographicOrientation[orientation]
        detail = InfographicDetail[detail_level]
        st = InfographicStyle[style]

        async def _create():
            return await self.client.artifacts.generate_infographic(
                notebook_id=notebook_id,
                instructions=instructions,
                orientation=orient,
                detail_level=detail,
                style=st,
                language=language,
            )

        try:
            gen = await self._create_studio_with_retry("infographic", _create)
        except StudioSilentRejection as e:
            logger.error(str(e))
            return {
                "task_id": None,
                "status": "silent_rejection",
                "is_complete": False,
                "downloaded_path": None,
            }

        logger.info(
            "infographic: task %s queued, polling download up to %.0fs",
            gen.task_id, _STUDIO_TIMEOUT_INFOGRAPHIC,
        )
        downloaded = None
        if output_path:
            downloaded = await self._poll_studio_download(
                download_callable=self.client.artifacts.download_infographic,
                notebook_id=notebook_id,
                artifact_id=gen.task_id,
                output_path=output_path,
                timeout_seconds=_STUDIO_TIMEOUT_INFOGRAPHIC,
                artifact_label="infographic",
            )
        return {
            "task_id": gen.task_id,
            "status": "ok" if downloaded else ("timeout" if output_path else "ok"),
            "is_complete": downloaded is not None,
            "downloaded_path": downloaded,
        }
