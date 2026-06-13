---
name: project-closed-rag-sphere-principle
description: "Ganymede's load-bearing architecture: analytical content stays inside the NotebookLM closed RAG sphere; Gemini is scoped to dispatcher intent classification ONLY. If a future feature touches analytical content (carries strategic claims forward), it routes through the canonical Engine notebook — NOT Gemini."
metadata: 
  node_type: memory
  type: project
  originSessionId: b1fabc43-1fa7-4ec9-b300-429b7b733143
---

The load-bearing architectural principle for Ganymede: **anything analytical stays inside the NotebookLM closed RAG sphere; Gemini is scoped to dispatcher intent classification only.** This is a design principle, not just an implementation choice. Future-Claude WILL be tempted to route analytical work through Gemini for speed/cost reasons. Resist.

**The principle:**

| Where the work lives | What it does | Why |
|---|---|---|
| **Canonical NotebookLM Engine** (`0a7d2672-...`) | All synthesis — Stroke 1, Stroke 3 re-synthesis, ANY translation/reformulation of analytical content | Grounded in `docs/foundations/` corpus → understands what DAI / SDS / ROEM / Strategic Lasso / etc. actually MEAN, not just surface-jargon mapping |
| **Mirror Auditor sibling** (`756e3683-...`) | Stroke 2 audit (fault-finding) | Same corpus grounding, different output discipline |
| **Connection Bridge** (provisioned per-use or persistent) | Stroke 2b audit (missed connections) | Same corpus grounding, different output discipline |
| **Gemini Flash** | Dispatcher intent classification (`POST /api/v2/dispatch`) ONLY | Thin "what does the operator want?" call that doesn't touch analytical content |

**Why this matters:**

1. **Translation IS analytical content.** If the model distorts a translation, the operator's read of the analysis is distorted. Not a safe space for an ungrounded model.
2. **The grounding is what makes Ganymede's reasoning real.** The framework's primitives (DAI, ROEM, Lasso, Incomprehensible Move, Set/Horus) only mean something to a model that has the foundations corpus loaded. Gemini Flash doesn't have that; it would do surface-level jargon substitution that LOOKS like translation but loses the structural meaning.
3. **The Cube-of-Space exchange (milestone 43) worked specifically because** the notebook understood the framework concepts from grounding. A Gemini Flash translator would not have produced that quality of output. Future-Claude looking at the milestone 43 transcript should KNOW the quality came from the grounding, not from clever vocabulary substitution.
4. **The closed sphere is what makes Ganymede a "module" rather than a generic LLM wrapper.** Z-SPAN and future consumers depend on the analytical content being trustworthy. Mixing in ungrounded paths erodes that trust surface.

**The Pl3 correction story (2026-06-06):**

I shipped Pl3 Operator Lens initially with Gemini Flash backing translation (~1-2s wall, cheap, no provisioning). James pushed back immediately and correctly:

> *"This kinda goes against the whole notebook RAG closed information sphere thing since Gemini was only used for that one specific thing of deducing my query. I was just envisioning another couple of final queries to the notebook before we stopped using it for the final lens thing."*

Correction landed at commit `2e0a699`. `run_translation` now routes through `self.svc.query_chess_engine` with register-specific prompts. Cost ~30-50s per translation (matches every other NL-backed surface). Quality matches milestone 43 because it's the same notebook with the same grounding.

**Recorded:** the deprecated Gemini translation prompts are preserved as `_DEPRECATED_GEMINI_TRANSLATION_PROMPTS` in `gemini_service.py` for historical reference. The canonical translation prompt library lives in `orchestrator.py` as `TRANSLATION_PROMPT_TEMPLATES`.

**How to apply (forward-looking rule):**

When designing ANY new feature that produces operator-facing analytical content (translation, summarization, reformulation, framing-shift, etc.):

1. **Default to routing through the canonical Engine** (or a sibling NotebookLM notebook with the foundations grounding) with a task-shaped prompt.
2. **Only use Gemini if the work is purely classification / extraction** that doesn't carry analytical claims forward (e.g., the dispatcher's pathway routing — "what's the intent?" — qualifies; translation does NOT qualify).
3. **If in doubt, ask: does this output influence how the operator reads the analytical content?** If yes, it's analytical and belongs in the closed sphere.
4. **Speed/cost arguments are not sufficient** to break this rule. The closed-sphere discipline is what makes Ganymede's outputs trustworthy at the consumer surface.

**Cross-references:**
- Pl3 implementation: `app/services/orchestrator.py:run_translation` + `TRANSLATION_PROMPT_TEMPLATES`
- Pl3 endpoint: `POST /api/v2/sessions/{id}/translate` in `app/v2_routes.py`
- Architecture_History milestone 45 (records the correction mid-flight)
- Deprecated path (don't reuse): `_DEPRECATED_GEMINI_TRANSLATION_PROMPTS` in `app/services/gemini_service.py`
- Dispatcher (legitimate Gemini use case): `POST /api/v2/dispatch` + `GeminiService.dispatch_intent`
