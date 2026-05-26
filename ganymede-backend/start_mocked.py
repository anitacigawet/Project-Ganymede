"""Start the Ganymede backend with NotebookLM calls mocked.

For Phase 6 PrisonBreak integration smoke testing — runs a real uvicorn
server but intercepts query_chess_engine and query_mirror_auditor so we
don't burn live API quota during integration tests.

Usage:
    ./venv_312/Scripts/python.exe start_mocked.py
"""
from __future__ import annotations

import asyncio
import logging

import uvicorn

from app.services import notebooklm as nbsvc

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def fake_query_chess_engine(self, prompt, *args, **kwargs):
    logger.info("[mock] query_chess_engine: %d-char prompt", len(prompt))
    await asyncio.sleep(0.5)  # simulate latency so events arrive over time
    if "AUDIT FINDINGS" in prompt:
        return (
            "STROKE 3 RESYNTHESIS:\n\n"
            "Given the audit's identification of pattern-matching and "
            "confidence gaps, the recalibrated motion is a Brady "
            "discovery demand backed by the eyewitness contradiction "
            "log. Strategic Lasso: prosecution's reliance on a single "
            "uncorroborated identification. Incomprehensible Move: "
            "request the witness's pre-trial coaching transcripts."
        )
    return (
        "STROKE 1 SYNTHESIS:\n\n"
        "STRATEGIC LASSO: Prosecution's case rests entirely on the "
        "eyewitness identification despite contradictions in the trial "
        "transcript at p.42.\n\n"
        "INCOMPREHENSIBLE MOVE: File a motion to compel disclosure of "
        "the eyewitness's prior identifications and any pre-trial "
        "coaching materials — the prosecution is structurally not "
        "defending against this because the original ID was logged as "
        "unequivocal.\n\n"
        "FINAL RESOLUTION: The strongest available motion is a Brady "
        "discovery demand targeting the eyewitness's identification "
        "history, paired with a Daubert challenge on any forensic "
        "analysis used to corroborate the ID."
    )


async def fake_query_mirror_auditor(self, prompt):
    logger.info("[mock] query_mirror_auditor: %d-char prompt", len(prompt))
    await asyncio.sleep(0.5)
    return (
        "1. RIGIDITY ERRORS — The analysis assumes the prosecution's "
        "stance is static; in practice, prosecutors retreat to lesser "
        "charges when discovery exposes weakness.\n"
        "2. PATTERN-MATCHING — The Brady demand is a familiar template; "
        "the auditor flags this as a weak signal that the original "
        "stroke reached for a known move rather than synthesizing.\n"
        "3. CONFIDENCE-EVIDENCE GAPS — Confidence in 'eyewitness "
        "contradiction' exceeds what the trial transcript citation "
        "supports without the actual witness statement.\n"
        "4. DIMENSIONAL GREEDS — The synthesis selected the most "
        "aesthetically clean motion (single Brady demand) rather than "
        "the messier but stronger combination of Brady + Daubert + "
        "ineffective-counsel claim."
    )


# Monkey-patch BEFORE the orchestrator is constructed by app.main.
nbsvc.NotebookLMService.query_chess_engine = fake_query_chess_engine
nbsvc.NotebookLMService.query_mirror_auditor = fake_query_mirror_auditor

# Now import and run.
if __name__ == "__main__":
    logger.info("=== Ganymede backend starting in MOCKED mode ===")
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, log_level="warning")
