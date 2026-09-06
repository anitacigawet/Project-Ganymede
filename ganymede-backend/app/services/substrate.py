"""Claude CLI analytical substrate used by Project Ganymede.

The backend talks to the authenticated ``claude`` executable instead of an
API-key-specific SDK. Analytical strokes run with every tool disabled. Web
research is implemented separately in :mod:`app.services.claude_runtime` and
allows only Claude Code's built-in ``WebSearch`` tool.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import os
import shutil
import signal
import subprocess
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Protocol

from app.services.personas import (
    CHESS_ENGINE_PERSONA,
    CONNECTION_BRIDGE_PERSONA,
    MIRROR_AUDITOR_PERSONA,
)

logger = logging.getLogger(__name__)


SPHERE_DISCIPLINE_BLOCK = """\
KNOWLEDGE SPHERE — NON-NEGOTIABLE:
Your knowledge sphere for this analysis is EXCLUSIVELY: (a) the 9D
foundations corpus below, (b) any Truth Packets supplied in the prompt,
and (c) any prior strokes supplied in the prompt. Do not introduce factual
claims from general memory.

If Truth Packets contain external-world facts, open with this notice shape:
"Notice: Data regarding <domains> utilized in this analysis are derived
from the external truth packets and are not from my sources; you may want
to independently verify that information."

If required information is absent, state "DATA NOT AVAILABLE IN SPHERE"."""

BRIDGE_OUT_OF_SPHERE_ADDENDUM = """\
ADDITIONAL DUTY — OUT-OF-SPHERE FLAGS:
If a synthesis claim rests on a fact absent from both the Truth Packets and
the foundations corpus, flag it as:
OUT-OF-SPHERE: <claim> — not grounded in packets or foundations."""


@dataclass
class SubstrateResult:
    text: str
    substrate: str = "claude_cli"
    model_id: Optional[str] = None
    cost_usd: Optional[float] = None
    sphere_notice_missing: bool = False
    raw_usage: Optional[dict] = None


class EngineSubstrate(Protocol):
    async def query_engine(self, prompt: str) -> SubstrateResult: ...
    async def query_auditor(self, prompt: str) -> SubstrateResult: ...
    async def query_bridge(self, prompt: str) -> SubstrateResult: ...
    async def translate(self, prompt: str) -> SubstrateResult: ...


def default_foundations_dir() -> Path:
    if configured := os.environ.get("GANYMEDE_FOUNDATIONS_DIR"):
        return Path(configured).expanduser().resolve()
    return Path(__file__).resolve().parents[3] / "docs" / "foundations"


def resolve_corpus_paths(
    files: Optional[list[str]] = None, *, root: Optional[Path] = None,
) -> list[Path]:
    """Canonical Markdown selection for every analytical role."""
    root = Path(root).expanduser().resolve() if root is not None else default_foundations_dir()
    if not root.is_dir():
        raise RuntimeError(
            f"Foundations directory not found: {root}. "
            "Set GANYMEDE_FOUNDATIONS_DIR to a directory containing the "
            "Project Ganymede foundation Markdown files."
        )

    selected = files
    if selected is None and (raw := os.environ.get("GANYMEDE_CORPUS_FILES")):
        selected = [item.strip() for item in raw.split(",") if item.strip()]

    paths = [
        path
        for path in sorted(root.glob("*.md"))
        if path.is_file() and path.name.lower() != "readme.md"
        and (selected is None or path.name in selected)
    ]
    if selected is not None:
        found = {path.name for path in paths}
        missing = [name for name in selected if name not in found]
        if missing:
            raise RuntimeError(f"Foundation files not found: {missing}")
    if not paths:
        raise RuntimeError(f"No foundation Markdown files found in {root}")
    return paths


def assemble_corpus(files: Optional[list[str]] = None) -> str:
    paths = resolve_corpus_paths(files)

    blocks: list[str] = []
    for path in paths:
        blocks.extend(
            [
                f"===== FOUNDATION DOCUMENT: {path.name} =====",
                path.read_text(encoding="utf-8").strip(),
                "",
            ]
        )
    return "\n".join(blocks).strip()


def resolve_claude_bin() -> Optional[str]:
    configured = os.environ.get("GANYMEDE_CLAUDE_BIN")
    if configured:
        expanded = str(Path(configured).expanduser())
        return expanded if Path(expanded).is_file() else None
    return shutil.which("claude") or shutil.which("claude.cmd")


def claude_status() -> dict[str, object]:
    executable = resolve_claude_bin()
    return {
        "available": executable is not None,
        "executable": executable,
        "model": os.environ.get("GANYMEDE_ENGINE_MODEL", "sonnet"),
    }


class ClaudeCliRunner:
    """Bounded, cancellation-safe wrapper around ``claude -p``.

    ``subprocess.Popen`` runs on a worker thread. This avoids the Windows
    event-loop subprocess failure seen when Uvicorn reload is active while
    still keeping FastAPI's event loop responsive.
    """

    def __init__(self, *, model: Optional[str] = None) -> None:
        self.model = model or os.environ.get("GANYMEDE_ENGINE_MODEL", "sonnet")
        self.timeout = float(os.environ.get("GANYMEDE_CLAUDE_TIMEOUT", "600"))
        self.max_attempts = int(os.environ.get("GANYMEDE_CLAUDE_MAX_ATTEMPTS", "2"))

    def _base_command(self, *, system_file: Path, tools: list[str]) -> list[str]:
        executable = resolve_claude_bin()
        if executable is None:
            raise RuntimeError(
                "Claude Code CLI was not found. Install Claude Code, run "
                "`claude` once to authenticate, or set GANYMEDE_CLAUDE_BIN."
            )
        command = [
            executable,
            "-p",
            "--model",
            self.model,
            "--output-format",
            "json",
            "--strict-mcp-config",
            "--mcp-config",
            '{"mcpServers":{}}',
            "--permission-mode",
            "dontAsk",
            "--no-session-persistence",
            "--safe-mode",
            "--disable-slash-commands",
            "--system-prompt-file",
            str(system_file),
        ]
        if tools:
            command.extend(["--tools", ",".join(tools)])
            command.extend(["--allowedTools", *tools])
        else:
            command.extend(["--tools", ""])
        return command

    @staticmethod
    def _stop_process(process: subprocess.Popen) -> None:
        """Stop a POSIX process group or an unassigned Windows process."""
        if os.name == "nt":
            if process.poll() is None:
                process.kill()
        else:
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass

    @staticmethod
    def _communicate(
        command: list[str], prompt: str, timeout: float,
        stop: Optional[threading.Event] = None,
    ) -> tuple[int, str, str]:
        stop = stop or threading.Event()
        if stop.is_set():
            raise RuntimeError("Claude invocation cancelled before process creation")
        creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
        job = None
        if os.name == "nt":
            from app.services.windows_job import WindowsJob
            job = WindowsJob()
            creationflags |= 0x4  # CREATE_SUSPENDED: no descendant can escape assignment
        process = None
        try:
            process = subprocess.Popen(
                command,
                stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                text=True, encoding="utf-8", errors="replace",
                creationflags=creationflags, start_new_session=os.name != "nt",
            )
            if job is not None:
                job.attach_and_resume(process)
            deadline = time.monotonic() + timeout
            first = True
            while True:
                if stop.is_set():
                    raise RuntimeError("Claude invocation cancelled")
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise TimeoutError(f"Claude CLI timed out after {timeout:.0f} seconds")
                try:
                    stdout, stderr = process.communicate(
                        prompt if first else None, timeout=min(0.1, remaining),
                    )
                    return process.returncode, stdout, stderr
                except subprocess.TimeoutExpired:
                    first = False
        except BaseException:
            if job is not None:
                job.close()
            if process is not None:
                ClaudeCliRunner._stop_process(process)
                process.communicate(timeout=5)
            raise
        finally:
            if job is not None:
                job.close()
            elif process is not None:
                # A successful wrapper can exit while detached descendants remain.
                ClaudeCliRunner._stop_process(process)

    async def invoke(
        self,
        *,
        prompt: str,
        system_file: Path,
        tools: Optional[list[str]] = None,
    ) -> SubstrateResult:
        command = self._base_command(system_file=system_file, tools=tools or [])
        last_error = "unknown error"
        for attempt in range(1, self.max_attempts + 1):
            stop = threading.Event()
            worker = asyncio.create_task(asyncio.to_thread(
                self._communicate, command, prompt, self.timeout, stop,
            ))
            try:
                returncode, stdout, stderr = await asyncio.shield(worker)
            except TimeoutError as exc:
                last_error = str(exc)
                logger.warning("Claude CLI attempt %d timed out", attempt)
                continue
            except asyncio.CancelledError:
                stop.set()
                # Do not release the operation until its owned worker is reaped.
                while not worker.done():
                    try:
                        await asyncio.shield(worker)
                    except asyncio.CancelledError:
                        continue
                    except Exception:
                        break
                if not worker.cancelled():
                    worker.exception()
                raise
            except Exception as exc:
                last_error = f"{type(exc).__name__}: {exc}"
                logger.warning("Claude CLI attempt %d failed: %s", attempt, last_error)
                continue

            if returncode != 0:
                last_error = f"exit {returncode}: {stderr.strip()[:500]}"
                logger.warning("Claude CLI attempt %d failed: %s", attempt, last_error)
                continue
            try:
                payload = json.loads(stdout)
            except json.JSONDecodeError as exc:
                last_error = f"invalid JSON output: {exc}"
                continue

            text = payload.get("result") or ""
            if not text.strip():
                last_error = payload.get("error") or "Claude CLI returned an empty result"
                continue
            return SubstrateResult(
                text=text,
                model_id=(payload.get("model") or self.model),
                cost_usd=payload.get("total_cost_usd"),
                raw_usage=payload.get("usage"),
            )
        raise RuntimeError(
            f"Claude CLI failed after {self.max_attempts} attempt(s): {last_error}"
        )


class ClaudeSubstrate:
    name = "claude_cli"

    def __init__(self, *, corpus_files: Optional[list[str]] = None) -> None:
        self.runner = ClaudeCliRunner()
        self.corpus = assemble_corpus(corpus_files)
        data_root = Path(
            os.environ.get(
                "GANYMEDE_DATA_DIR", str(Path(__file__).resolve().parents[2] / "data")
            )
        )
        self.prompt_dir = data_root / "substrate_prompts"
        self.prompt_dir.mkdir(parents=True, exist_ok=True)
        self._system_files: dict[str, Path] = {}

    def _system_file(self, role: str) -> Path:
        if role in self._system_files:
            return self._system_files[role]
        personas = {
            "engine": CHESS_ENGINE_PERSONA,
            "auditor": MIRROR_AUDITOR_PERSONA,
            "bridge": CONNECTION_BRIDGE_PERSONA + "\n\n" + BRIDGE_OUT_OF_SPHERE_ADDENDUM,
            "translate": CHESS_ENGINE_PERSONA,
        }
        body = personas[role] + "\n\n" + SPHERE_DISCIPLINE_BLOCK
        if role != "translate":
            body += "\n\n===== 9D FOUNDATIONS CORPUS =====\n\n" + self.corpus
        digest = hashlib.sha256(body.encode("utf-8")).hexdigest()[:12]
        path = self.prompt_dir / f"{role}-{digest}.txt"
        if not path.exists():
            path.write_text(body, encoding="utf-8")
        self._system_files[role] = path
        return path

    async def _invoke(self, role: str, prompt: str) -> SubstrateResult:
        result = await self.runner.invoke(
            prompt=prompt,
            system_file=self._system_file(role),
            tools=[],
        )
        result.substrate = self.name
        return result

    async def query_engine(self, prompt: str) -> SubstrateResult:
        return await self._invoke("engine", prompt)

    async def query_auditor(self, prompt: str) -> SubstrateResult:
        return await self._invoke("auditor", prompt)

    async def query_bridge(self, prompt: str) -> SubstrateResult:
        return await self._invoke("bridge", prompt)

    async def translate(self, prompt: str) -> SubstrateResult:
        return await self._invoke("translate", prompt)

    @staticmethod
    def check_sphere_notice(
        result: SubstrateResult, *, packets_present: bool
    ) -> SubstrateResult:
        if packets_present and not result.text.lstrip().startswith("Notice:"):
            result.sphere_notice_missing = True
        return result


SonnetSubstrate = ClaudeSubstrate
