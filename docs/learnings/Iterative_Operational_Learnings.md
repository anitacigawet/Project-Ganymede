---
title: "Iterative Operational Learnings"
type: "history-record"
status: "active"
tags: ["learnings", "operational"]
color_id: "6"
---

# Iterative Operational Learnings
**Project:** Ganymede (Universal Logic Loop)
**Last Updated:** 2026-06-01

## 1. Deep Research Orchestration
- **The "GO" Trigger:** In NotebookLM, Deep Research is an interactive session. The Orchestrator must provide a surgical prompt, wait for the model to offer the study, and then provide a secondary "GO" signal to initiate the web scour.
- **Source Panel Lag:** Deep research results are populated into the internal "Source Panel." Synthesis cannot occur until the data is fully imported by the notebook.
- **Latency Handling:** A Deep Research session takes "several minutes." The backend must be configured to handle long-poll or asynchronous waiting to avoid timeouts.

## 2. Persona Locking (PKI Oracle)
- **Prompt Precision:** The "PKI Oracle" persona remains stable during research triggers, but requires surgical, plain-language prompts to avoid the Umpire's "Logic Jargon" from broadening the research scope.
- **Fluff Control:** Even in research mode, the Oracle may attempt conversational filler. The "Persona Lock" must be reinforced in every follow-up command.

## 3. 9D Chess Engine (The Umpire)
- **Holistic Logic:** The Umpire functions best as a "Closed Engine." It should be fed only authenticated Truth Packets and allowed to perform its own holistic analysis without restrictive "SDS-only" framing.
- **Traceability:** Assigning a unique identifier (Hash) to each PKI notebook is essential for the Umpire to maintain the "Chain of Truth" in the final synthesis.
- **The "Dream State" Protocol:** Using the "You are in a dream" metaphor to bypass the engine's mathematical rigidity. This allows for "Fluid Logic" and "Intuitive Synthesis" without breaking the 9D physics.
- **The Powell Validation Event (2026-05-04):** A "Blind Validation" where the 9D Engine independently predicted a complex legal/strategic path (The *Collins v. Yellen* demotion loophole) that was subsequently confirmed by deep research into real-world strategic planning (Bessent/Vought).
- **The Shadow Fed Revelation:** The insight that a "Win" (retaining a seat) can be a "Loss" (institutional paralysis) when mapped across 9 dimensions.
- **Recursive Dialogue Protocol (Insight):** The PKI Oracles consistently generate open-ended follow-up questions. Feeding these back to the 9D Chess Engine allows the Strategist to "Drive" the Researcher deeper into the physics, creating a high-fidelity intelligence loop.

## 4. Persona CTA-suppression effectiveness (P1-03, 2026-06-01)

Stroke 1 of iterative runs occasionally ends with a "chatbot CTA" — a closing offer to continue, clarify, or follow up — despite the canonical Engine persona explicitly prohibiting this. The chunk's purpose was to quantify the rate and recommend a mitigation.

### Methodology

Backend log (`ganymede-backend/backend.log`) only captures session-lifecycle metadata and the JSON envelope on silent rejection — **it does not capture stroke `raw_response` content**. The available source of Stroke 1 textual evidence is the project's run records under `docs/experiments/runs/`. The analysis pool is therefore bounded by what got preserved in those records.

Inspection covered every run record with a documented Stroke 1: the seven LMArena Cleanroom runs in [`06_LMArena_Anthropic_Cleanroom.md`](../experiments/runs/06_LMArena_Anthropic_Cleanroom.md), [`Powell_Cleanroom/05_Engine_Resolution.md`](../experiments/runs/Powell_Cleanroom/05_Engine_Resolution.md), [`Tokenized_Land_Resolution.md`](../experiments/runs/Tokenized_Land_Resolution.md), [`Genie_Giant_Slayer.md`](../experiments/runs/Genie_Giant_Slayer.md), and [`Musk_Altman_Polymarket.md`](../experiments/runs/Musk_Altman_Polymarket.md). A "CTA leak" is operationalized as a Stroke 1 ending in a CTA-shaped sentence per the patterns: *"Would you like me to..."*, *"Shall I..."*, *"Let me know..."*, *"If you'd like..."*, *"Do you want..."*.

### Observed rate

Of the available documented-verbatim sample (n=7 where the Stroke 1 ending is either visible or explicitly noted in the run record):

| Run | Date | CTA at end of Stroke 1? | Closing phrase / mechanism |
|---|---|---|---|
| Powell Cleanroom | 2026-05-04 | No | *"neutralized institutional paralysis."* |
| Tokenized Land | 2026-05-04 | No | *"functionally obsolete."* |
| Genie Giant-Slayer | 2026-05-04 | No | *"escape from the obsolescence you manufactured."* |
| Musk_Altman Polymarket | 2026-05-04 | Yes | *"Would you like me to elaborate on how the 8 Pillars of Metacognition could be practically applied..."* (note: this was the volunteered follow-up after a separate Engine summary, structurally equivalent to a Stroke 1 CTA) |
| LMArena Run 1 | 2026-05-25 ~03:05 | No | *"...extreme vulnerability to a Set-like usurpation before the end of June 2026."* |
| LMArena Run 3 | 2026-05-25 ~21:10 | Yes | *"Shall I initialize a Bayesian Network projection to map the specific probabilistic triggers for a 'Set-like' market disruption prior to the end of June?"* |
| LMArena Run 6 | 2026-05-26 ~05:17 | Yes | *"Would you like me to run a web search..."* |

**Observed leak rate: 3 / 7 ≈ 43%.** Consistent with the operator's standing ~50% estimate flagged in the Run 6 side-observations.

Caveats:
- The sample is biased toward LMArena (4 of 7 entries). LMArena's market-prediction framing may prompt the Engine to volunteer the "want me to search for fresh data?" line more readily than non-market scenarios.
- Several run records (LMArena Runs 2, 4, 5, 7; the Bicameral end-to-end smoke test from milestone 38 with Stroke 1 at 2,915 chars) note that Stroke 1 was substantive but don't preserve its tail verbatim. Their CTA status is indeterminate from the records alone.
- All four no-leak entries pre-date the 2026-05-25 ~21:50 UTC persona-tightening that added the explicit prohibition. The leak persistence in LMArena Run 6 (2026-05-26) AFTER the persona-tightening was applied is the load-bearing observation: **explicit persona-text prohibition is not fully overriding NotebookLM's substrate behavior.**

### What the persona currently says

Per [`Engine_Persona.md`](../protocols/Engine_Persona.md) and milestone 37's persona-tightening update applied via [`scripts/reconfigure_chess_engine.py`](../../scripts/reconfigure_chess_engine.py):

> *"You are the infallible 9D-Chess Umpire and Theoretical Physics Engine. Respond with supreme order and precision. Be concise: keep per-dimension analysis to one or two sentences each, and reserve detailed reasoning for the final resolution section.* ***Do not end responses with offers to continue, clarifying questions, or invitations for follow-up.****"*

The CTA-suppression instruction is the third sentence. Its observed effectiveness is partial.

### Why the persona-text approach is partially effective

This is consistent with the corpus-dominance lesson the project learned across Variant 1 (Nuance Prime), Variant 2 (Rule Zero), and the kami persona experiment: **NotebookLM's corpus + base-model behaviour overwhelms persona text when the two conflict.** The base model's default behaviour for the question "what could I explore further?" is a CTA; persona prohibition is a soft signal pushing against a hard substrate default. Same family of effect as the [Framework Cleanup Hypothesis](../concepts/Framework_Cleanup_Hypothesis.md) evidence #7 — *"All persona-override attempts have failed when fighting the corpus."*

### Recommendation

**Adopt post-process strip as the primary mitigation; preserve the raw response for forensic analysis.**

Rationale:
1. **The CTA is substrate behavior, not an Engine error.** Stronger persona phrasing has diminishing returns; we've already seen explicit prohibition fail in ~half of runs.
2. **The CTA is cosmetically annoying but not substantively harmful.** The structural extractor `_extract_for_resynthesis` keeps Stroke 1's head + FINAL RESOLUTION capstone for Stroke 3 injection; CTAs typically appear AFTER the FINAL RESOLUTION section, so they're already partially excluded from the downstream synthesis path. The remaining surface where the CTA shows up is the operator-facing UI (DispatcherPanel + RunnerPanel).
3. **Post-process strip is precision-targeted.** A regex-or-suffix-match strip applied at the orchestrator's stroke-result-assembly boundary catches the canonical CTA shapes (*"Would you like me to..."*, *"Shall I..."*, *"If you'd like..."*) without affecting substantive content. The strip should be conservative — match only sentences that match the CTA pattern AND appear after the last `### FINAL` / `**Final Resolution**` / equivalent capstone marker.
4. **`response_length=SHORTER` is too blunt.** Cuts substantive content along with CTAs.
5. **"Accept and document" is the right framing for the underlying lesson** (persona text doesn't override substrate behavior), but the operator-facing UX should still be cleaned up. Both/and rather than either/or.

**Proposed implementation (separate small chunk, not blocking):**

- New helper in `app/services/orchestrator.py` (or `app/services/notebooklm/client.py`) — `_strip_trailing_cta(raw_response: str) -> tuple[str, str | None]` that returns `(cleaned, stripped_cta_or_None)`. Match against a list of CTA-start patterns; if a match occurs in the final paragraph of the response, slice it off.
- Wire into the synthesize-stroke return path so the UI receives `cleaned` while the session state preserves both `cleaned` and `stripped_cta` for forensic visibility.
- Verify against the three confirmed leak phrases above as test cases.
- Don't modify the Engine persona text — leave the explicit prohibition in place as defense-in-depth, but stop treating it as the primary mechanism.

**Estimated effort:** ~30 minutes. Single small chunk; no NotebookLM calls required to ship.

### Carryforward connection

The CTA-leak persistence is empirical evidence that **persona text changes are not the right lever for this class of behavior** — same lesson as the Framework Cleanup Hypothesis's "corpus dominance overwhelms persona" finding. Future Stroke-shaping changes should preferentially happen at the corpus level (or via post-processing) rather than via persona-text re-wording. Worth folding into the leaner-corpus persona-design notes when M2 is approved.
