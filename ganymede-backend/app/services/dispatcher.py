"""Natural-language pathway classification through Claude CLI."""

from __future__ import annotations

import hashlib
import json
import logging
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.contracts import Scenario

from app.services.substrate import ClaudeCliRunner

logger = logging.getLogger(__name__)

SYSTEM = """\
Classify a Project Ganymede request into exactly one pathway:
- cleanroom: predict or analyze a question
- genie: find a path from a current state to a wished-for state
- offensive: design a strategy against a target toward an objective
- mirror_audit: audit an existing analysis

Return JSON only with keys: pathway, confidence, scenario,
needs_external_knowledge, rationale, clarifying_questions. Scenario may use
question, current_state, wished_for_state, target, objective_state,
prior_resolution, dream_state, and extra_context. Ask at most two concise
clarifying questions. Do not perform the analysis itself."""


class DispatchDecision(BaseModel):
    model_config = ConfigDict(extra="ignore", strict=True)
    pathway: Literal["cleanroom", "genie", "offensive", "mirror_audit"]
    confidence: float = Field(0, ge=0, le=1, allow_inf_nan=False)
    scenario: Scenario = Field(default_factory=Scenario)
    needs_external_knowledge: bool = True
    rationale: str = "Local fallback classification."
    clarifying_questions: list[str] = Field(default_factory=list, max_length=2)


class DispatcherService:
    def __init__(self, prompt_dir: Path) -> None:
        self.runner = ClaudeCliRunner()
        digest = hashlib.sha256(SYSTEM.encode("utf-8")).hexdigest()[:12]
        prompt_dir.mkdir(parents=True, exist_ok=True)
        self.system_file = prompt_dir / f"dispatcher-{digest}.txt"
        if not self.system_file.exists():
            self.system_file.write_text(SYSTEM, encoding="utf-8")

    async def dispatch_intent(self, text: str) -> dict[str, object]:
        try:
            result = await self.runner.invoke(
                prompt=f"Classify this request:\n\n{text.strip()}",
                system_file=self.system_file,
                tools=[],
            )
            raw = result.text.strip()
            if raw.startswith("```"):
                raw = raw.removeprefix("```json").removeprefix("```").rstrip("` \n")
            payload = json.loads(raw)
            decision = DispatchDecision.model_validate(payload, strict=True)
            if not any(getattr(decision.scenario, key) for key in (
                "question", "current_state", "target", "prior_resolution",
            )):
                decision.scenario.question = text.strip()
            return decision.model_dump()
        except Exception as exc:
            logger.warning("Dispatcher classification fell back to cleanroom: %s", exc)
            return {
                "pathway": "cleanroom",
                "confidence": 0.0,
                "scenario": {"question": text.strip(), "dream_state": True},
                "needs_external_knowledge": True,
                "rationale": "Classification was unavailable; using the general analysis path.",
                "clarifying_questions": [],
            }
