"""Engine substrate abstraction — SM-1 of the Substrate Migration.

Two implementations of the same seam:

- :class:`SonnetSubstrate` — headless ``claude -p`` per stroke. Persona +
  sphere discipline + the FULL 9D foundations corpus ride as a byte-stable
  ``--system-prompt-file`` (cache-friendly prefix; the corpus is ~30k tokens
  and fits with 100k+ headroom); the stroke's rendered prompt rides stdin.
  Cost per invocation is parsed from the stream-json ``result`` event and
  surfaced on :class:`SubstrateResult` (bills the Max plan's included
  non-interactive cap — see docs/concepts/Substrate_Migration.md § 4).
- :class:`NotebookLMSubstrate` — thin delegation to the legacy
  :class:`NotebookLMService` path. DORMANT under the migration (retained as
  the rollback artifact + the SM-3 recorded-baseline reference); constructed
  only when ``GANYMEDE_SUBSTRATE=notebooklm``.

Invocation shape (live-verified 2026-07-02 on CLI 2.1.198, model
``claude-sonnet-5``, plan § SM-1):

    claude -p --model <pinned> --output-format stream-json --verbose \\
      --strict-mcp-config --disallowedTools "*" \\
      --settings '{"disableAllHooks":true}' \\
      --system-prompt-file <persona+sphere+corpus>

Measured base overhead: ~21k cache-creation tokens on a cold prefix
(~$0.13 trivial-prompt cost), cache-read pennies while warm. The model id is
passed explicitly per invocation — never rely on CLI defaults (silent-routing
discipline; Z-SPAN D-121 verified ``total_cost_usd`` emission the same way).
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import os
import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Protocol

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Sphere discipline (plan § 5 — the closed RAG sphere moves from substrate
# physics to prompt policy on the Sonnet side).
# ---------------------------------------------------------------------------

SPHERE_DISCIPLINE_BLOCK = """\

KNOWLEDGE SPHERE — NON-NEGOTIABLE:
Your knowledge sphere for this analysis is EXCLUSIVELY: (a) the 9D
foundations corpus below, (b) any Truth Packets supplied in the prompt,
(c) any prior strokes supplied in the prompt. You must not introduce facts,
entities, statistics, or events from outside these sources — your general
world knowledge is OUT OF SPHERE for factual claims.

If the Truth Packets contain external-world facts (companies, markets,
people, events, prices), open your response with exactly this notice shape:
"Notice: Data regarding <domains> utilized in this analysis are derived
from the external truth packets and are not from my sources; you may want
to independently verify that information."

If a fact you need is not present in the sphere, state
"DATA NOT AVAILABLE IN SPHERE" rather than supplying it from memory."""

# Sonnet-side Bridge extension (plan § 5 layer 3): the Bridge polices the
# synthesis for out-of-sphere claims in addition to its missed-connection
# duties. Appended after the canonical Bridge persona.
BRIDGE_OUT_OF_SPHERE_ADDENDUM = """\

ADDITIONAL DUTY — OUT-OF-SPHERE FLAGS:
While mapping the synthesis, if any synthesis claim rests on a fact absent
from both the Truth Packets and the foundations corpus, flag it:

  OUT-OF-SPHERE: <the claim> — not grounded in packets or foundations.

List these before your missed-bridge enumeration. If there are none, omit
the section entirely."""


# ---------------------------------------------------------------------------
# Result + corpus assembly
# ---------------------------------------------------------------------------

@dataclass
class SubstrateResult:
    """One stroke's worth of substrate output + provenance."""

    text: str
    substrate: str                       # "sonnet" | "notebooklm"
    model_id: Optional[str] = None       # resolved model, from result event
    cost_usd: Optional[float] = None     # None on the NotebookLM side
    sphere_notice_missing: bool = False  # packets present but no Notice: prefix
    raw_usage: Optional[dict] = None     # stream-json usage block (ops)


def default_foundations_dir() -> Path:
    """Mirror provision_bridge_notebook's resolution: env override, else
    docs/foundations relative to the repo root."""
    if env := os.environ.get("GANYMEDE_FOUNDATIONS_DIR"):
        return Path(env)
    return Path(__file__).resolve().parents[3] / "docs" / "foundations"


def assemble_corpus(files: Optional[list[str]] = None) -> str:
    """Concatenate the foundations corpus (sorted .md, README excluded) into
    the system-prompt corpus block.

    ``files`` (or env ``GANYMEDE_CORPUS_FILES``, comma-separated basenames)
    selects a subset — this is the leaner-corpus flag that makes the M2
    kernel-vs-scaffolding test a parameter instead of a build (plan § 6).
    Default: every non-README ``.md`` in the foundations dir. PDF sources
    join the corpus when their extracted ``.md`` siblings land (SM-2).
    """
    root = default_foundations_dir()
    if not root.is_dir():
        raise RuntimeError(
            f"Foundations directory not found: {root}. "
            f"Set GANYMEDE_FOUNDATIONS_DIR or fix the checkout."
        )
    subset = files
    if subset is None and (env := os.environ.get("GANYMEDE_CORPUS_FILES")):
        subset = [s.strip() for s in env.split(",") if s.strip()]

    paths = [
        p for p in sorted(root.iterdir())
        if p.is_file() and p.suffix.lower() == ".md"
        and p.name.lower() != "readme.md"
        and (subset is None or p.name in subset)
    ]
    if subset is not None and len(paths) != len(subset):
        found = {p.name for p in paths}
        missing = [s for s in subset if s not in found]
        raise RuntimeError(f"Corpus subset names not found: {missing}")

    parts: list[str] = []
    for p in paths:
        parts.append(f"===== FOUNDATION DOCUMENT: {p.name} =====")
        parts.append(p.read_text(encoding="utf-8").strip())
        parts.append("")
    return "\n".join(parts).strip()


# ---------------------------------------------------------------------------
# The seam
# ---------------------------------------------------------------------------

class EngineSubstrate(Protocol):
    """What the orchestrator needs from an analytical substrate (SM-2 threads
    this through every stroke call site)."""

    async def query_engine(self, prompt: str) -> SubstrateResult: ...
    async def query_auditor(self, prompt: str) -> SubstrateResult: ...
    async def query_bridge(self, prompt: str) -> SubstrateResult: ...
    async def translate(self, prompt: str) -> SubstrateResult: ...


# ---------------------------------------------------------------------------
# Sonnet implementation
# ---------------------------------------------------------------------------

_DEFAULT_MODEL = os.environ.get("GANYMEDE_ENGINE_MODEL", "claude-sonnet-5")
_INVOKE_TIMEOUT = float(os.environ.get("GANYMEDE_SONNET_TIMEOUT", "300"))
_INVOKE_MAX_ATTEMPTS = int(os.environ.get("GANYMEDE_SONNET_MAX_ATTEMPTS", "2"))


def _resolve_claude_bin() -> str:
    """Z-SPAN's resolution chain (qdrant_synthesizer.py pattern): PATH →
    env override → known-good nvm path. Service contexts drop nvm from PATH."""
    found = (
        shutil.which("claude")
        or os.environ.get("GANYMEDE_CLAUDE_BIN")
        or "/Users/macbook/.nvm/versions/node/v22.22.1/bin/claude"
    )
    if not Path(found).exists():
        raise RuntimeError(
            f"`claude` CLI not found (tried PATH, GANYMEDE_CLAUDE_BIN, "
            f"fallback {found!r}). Install Claude Code or set GANYMEDE_CLAUDE_BIN."
        )
    return found


class SonnetSubstrate:
    """Analytical strokes via headless ``claude -p``.

    One system-prompt file is rendered per (persona, corpus) pair and reused
    across strokes — byte-stable so the prompt-cache prefix holds. Files live
    under ``data/substrate_prompts/`` (gitignored with the rest of data/).
    """

    name = "sonnet"

    def __init__(
        self,
        *,
        model: str = _DEFAULT_MODEL,
        corpus_files: Optional[list[str]] = None,
        prompt_cache_dir: Optional[Path] = None,
    ):
        self.model = model
        self.claude_bin = _resolve_claude_bin()
        self._corpus = assemble_corpus(corpus_files)
        self._prompt_dir = prompt_cache_dir or (
            Path(__file__).resolve().parents[2] / "data" / "substrate_prompts"
        )
        self._prompt_dir.mkdir(parents=True, exist_ok=True)
        self._system_files: dict[str, Path] = {}
        logger.info(
            "SonnetSubstrate: model=%s corpus=%d chars claude=%s",
            model, len(self._corpus), self.claude_bin,
        )

    # ------------------------------------------------------------ personas

    def _system_file(self, role: str) -> Path:
        """Render (once) and return the system-prompt file for a role."""
        if role in self._system_files:
            return self._system_files[role]

        # Personas are the canonical constants from the NotebookLM client —
        # the same text that configured the notebooks, now with the sphere
        # discipline appended (and the Bridge's out-of-sphere duty).
        from app.services.notebooklm.client import (
            CHESS_ENGINE_PERSONA,
            CONNECTION_BRIDGE_PERSONA,
            MIRROR_AUDITOR_PERSONA,
        )
        personas = {
            "engine": CHESS_ENGINE_PERSONA,
            "auditor": MIRROR_AUDITOR_PERSONA,
            "bridge": CONNECTION_BRIDGE_PERSONA + BRIDGE_OUT_OF_SPHERE_ADDENDUM,
            # Translation is a pure text transform: register mappings live in
            # the prompt templates; corpus grounding is unnecessary. Keep the
            # Engine voice for continuity with the notebook-era behavior.
            "translate": CHESS_ENGINE_PERSONA,
        }
        body = personas[role] + "\n" + SPHERE_DISCIPLINE_BLOCK
        if role != "translate":
            body += (
                "\n\n===== 9D FOUNDATIONS CORPUS (your grounding substrate) "
                "=====\n\n" + self._corpus
            )
        digest = hashlib.sha256(body.encode()).hexdigest()[:12]
        path = self._prompt_dir / f"{role}-{digest}.txt"
        if not path.exists():
            path.write_text(body, encoding="utf-8")
        self._system_files[role] = path
        return path

    # ------------------------------------------------------------ invocation

    async def _invoke(self, role: str, prompt: str) -> SubstrateResult:
        system_file = self._system_file(role)
        cmd = [
            self.claude_bin, "-p",
            "--model", self.model,
            "--output-format", "stream-json", "--verbose",
            "--strict-mcp-config",
            "--disallowedTools", "*",
            "--settings", '{"disableAllHooks":true}',
            "--system-prompt-file", str(system_file),
        ]
        last_err = "unknown"
        for attempt in range(1, _INVOKE_MAX_ATTEMPTS + 1):
            logger.info(
                "SonnetSubstrate %s stroke (attempt %d/%d, prompt %d chars, "
                "system %s)",
                role, attempt, _INVOKE_MAX_ATTEMPTS, len(prompt),
                system_file.name,
            )
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            try:
                out, err = await asyncio.wait_for(
                    proc.communicate(prompt.encode("utf-8")),
                    timeout=_INVOKE_TIMEOUT,
                )
            except asyncio.TimeoutError:
                proc.kill()
                last_err = f"timeout after {_INVOKE_TIMEOUT}s"
                logger.warning("SonnetSubstrate %s: %s", role, last_err)
                continue

            result = self._parse_stream_json(out.decode("utf-8", "replace"))
            if proc.returncode == 0 and result and result.text.strip():
                if attempt > 1:
                    logger.info(
                        "SonnetSubstrate %s: succeeded on attempt %d",
                        role, attempt,
                    )
                return result
            last_err = (
                f"returncode={proc.returncode}, "
                f"stderr={err.decode('utf-8', 'replace')[:300]!r}"
            )
            logger.warning(
                "SonnetSubstrate %s attempt %d failed: %s",
                role, attempt, last_err,
            )
        raise RuntimeError(
            f"SonnetSubstrate {role} stroke failed after "
            f"{_INVOKE_MAX_ATTEMPTS} attempts: {last_err}"
        )

    def _parse_stream_json(self, raw: str) -> Optional[SubstrateResult]:
        """Extract text + cost + model from the stream-json result event."""
        result_ev: Optional[dict] = None
        model_id: Optional[str] = None
        for line in raw.splitlines():
            line = line.strip()
            if not line.startswith("{"):
                continue
            try:
                ev = json.loads(line)
            except json.JSONDecodeError:
                continue
            if ev.get("type") == "assistant":
                model_id = (ev.get("message") or {}).get("model") or model_id
            elif ev.get("type") == "result":
                result_ev = ev
        if result_ev is None:
            return None
        return SubstrateResult(
            text=result_ev.get("result") or "",
            substrate=self.name,
            model_id=model_id,
            cost_usd=result_ev.get("total_cost_usd"),
            raw_usage=result_ev.get("usage"),
        )

    @staticmethod
    def check_sphere_notice(result: SubstrateResult, *, packets_present: bool) -> SubstrateResult:
        """Plan § 5 layer 2 — syntactic drift detector, WARNING not gate."""
        if packets_present and not result.text.lstrip().startswith("Notice:"):
            result.sphere_notice_missing = True
            logger.warning(
                "SonnetSubstrate: packets present but no epistemic notice "
                "prefix — sphere discipline drift? (flagged on stroke)"
            )
        return result

    # ------------------------------------------------------------ protocol

    async def query_engine(self, prompt: str) -> SubstrateResult:
        return await self._invoke("engine", prompt)

    async def query_auditor(self, prompt: str) -> SubstrateResult:
        return await self._invoke("auditor", prompt)

    async def query_bridge(self, prompt: str) -> SubstrateResult:
        return await self._invoke("bridge", prompt)

    async def translate(self, prompt: str) -> SubstrateResult:
        return await self._invoke("translate", prompt)


# ---------------------------------------------------------------------------
# NotebookLM implementation (dormant — rollback artifact)
# ---------------------------------------------------------------------------

class NotebookLMSubstrate:
    """Delegates to the legacy notebook path. Requires initialized
    NotebookLMService + live auth — neither exists under dormancy; SM-2 only
    constructs this when GANYMEDE_SUBSTRATE=notebooklm."""

    name = "notebooklm"

    def __init__(self, svc, *, bridge_notebook_id: Optional[str] = None):
        self.svc = svc
        self.bridge_notebook_id = bridge_notebook_id

    async def query_engine(self, prompt: str) -> SubstrateResult:
        return SubstrateResult(
            text=await self.svc.query_chess_engine(prompt),
            substrate=self.name,
        )

    async def query_auditor(self, prompt: str) -> SubstrateResult:
        return SubstrateResult(
            text=await self.svc.query_mirror_auditor(prompt),
            substrate=self.name,
        )

    async def query_bridge(self, prompt: str) -> SubstrateResult:
        if not self.bridge_notebook_id:
            raise RuntimeError(
                "NotebookLMSubstrate.query_bridge needs a provisioned "
                "bridge_notebook_id (legacy provisioning path)."
            )
        return SubstrateResult(
            text=await self.svc.query_notebook(self.bridge_notebook_id, prompt),
            substrate=self.name,
        )

    async def translate(self, prompt: str) -> SubstrateResult:
        return SubstrateResult(
            text=await self.svc.query_chess_engine(prompt),
            substrate=self.name,
        )


def substrate_mode() -> str:
    """The configured substrate: 'sonnet' (default post-migration) or
    'notebooklm' (dormant legacy)."""
    return os.environ.get("GANYMEDE_SUBSTRATE", "sonnet").strip().lower()
