import logging
import os
import httpx
from google import genai
from google.genai import types
import json

logger = logging.getLogger(__name__)

# The four pathways the dispatcher classifies intent into. Kept here as a
# string list (rather than importing the Pathway enum from app.contracts) so
# this service stays a thin LLM wrapper with no orchestrator dependencies.
DISPATCHER_PATHWAYS = ("cleanroom", "genie", "offensive", "mirror_audit")

# ---------------------------------------------------------------------------
# Multi-provider dispatcher LLM routing.
#
# The dispatcher used to be Gemini-only. James got rate-limited at the wrong
# moment one too many times (the milestone 50 test session saw two consecutive
# 503 UNAVAILABLE responses mid-validation) so the provider is now selectable
# via env var, with cross-provider fallback if the primary returns an error.
#
# DeepSeek is the new default because James has a paid key with predictable
# rate limits. Gemini stays as the fallback so a stale DeepSeek key doesn't
# break the friendly front door. Either provider can also be removed by
# unsetting its key — the remaining one becomes the only path.
#
# Both providers ONLY power dispatcher intent classification. Analytical
# content stays in the closed RAG sphere (NotebookLM Engine / Auditor /
# Bridge / translation) per the milestone 45 closed-RAG-sphere principle.
# ---------------------------------------------------------------------------

_LLM_PROVIDER = os.environ.get("LLM_PROVIDER", "deepseek").lower().strip()
"""Primary dispatcher LLM. ``deepseek`` (default) or ``gemini``. If the
primary fails, the other is tried before falling back to the cleanroom
default response."""

_DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY", "").strip()
# Treat the .env placeholder as unset so a half-configured deployment routes
# cleanly to Gemini instead of burning a 401 round-trip to DeepSeek every
# dispatch call.
if _DEEPSEEK_API_KEY.startswith("PASTE_") or _DEEPSEEK_API_KEY in {"YOUR_KEY", "REPLACE_ME"}:
    _DEEPSEEK_API_KEY = ""
_DEEPSEEK_MODEL = os.environ.get("DEEPSEEK_MODEL", "deepseek-chat").strip()
_DEEPSEEK_BASE_URL = os.environ.get(
    "DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1"
).strip().rstrip("/")
_GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY", "").strip()


async def _dispatch_via_deepseek(prompt: str) -> str:
    """Call DeepSeek's OpenAI-compatible Chat Completions API.

    Returns the raw assistant text. Raises on any network/API error so
    the caller can fall back to the other provider.

    Pattern mirrored from DRAINO Clean-Room (``server/_core/llm.ts``
    ``openAICompatibleInvoke``) — DeepSeek and OpenAI speak the same
    dialect at ``/v1/chat/completions``.
    """
    if not _DEEPSEEK_API_KEY:
        raise RuntimeError("DEEPSEEK_API_KEY is not set")
    url = f"{_DEEPSEEK_BASE_URL}/chat/completions"
    payload = {
        "model": _DEEPSEEK_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "response_format": {"type": "json_object"},
        "temperature": 0.0,
    }
    headers = {
        "Authorization": f"Bearer {_DEEPSEEK_API_KEY}",
        "Content-Type": "application/json",
    }
    async with httpx.AsyncClient(timeout=60.0) as http:
        resp = await http.post(url, json=payload, headers=headers)
    if resp.status_code != 200:
        raise RuntimeError(
            f"DeepSeek HTTP {resp.status_code}: {resp.text[:400]}"
        )
    data = resp.json()
    return data["choices"][0]["message"]["content"]


def _dispatch_via_gemini(prompt: str, client: genai.Client) -> str:
    """Call Gemini Flash with the dispatcher prompt. Returns raw assistant
    text. Raises on any error so the caller can fall back."""
    if not _GOOGLE_API_KEY:
        raise RuntimeError("GOOGLE_API_KEY is not set")
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
    )
    return (response.text or "").strip()


# ---------------------------------------------------------------------------
# Pl3 Operator Lens — translation moved to NotebookLM Engine (milestone 45
# corrected). Translation is analytical content (it carries strategic
# claims forward; a distorted translation distorts the operator's read of
# the analysis), so it belongs inside the closed RAG sphere alongside
# Engine / Auditor / Bridge — NOT in Gemini Flash which is scoped to
# dispatcher intent classification only.
#
# The translation prompt library + run_translation() method now live in
# app/services/orchestrator.py (see TRANSLATION_PROMPT_TEMPLATES) and
# route through self.svc.query_chess_engine. The notebook's foundations-
# corpus grounding is what makes the translations actually understand
# what the framework concepts mean — which is what made the milestone 43
# Cube-of-Space exchange work in the first place.
# ---------------------------------------------------------------------------

TRANSLATION_REGISTERS = ("plain_english", "cube_of_space", "executive_brief")


_DEPRECATED_GEMINI_TRANSLATION_PROMPTS = {
    "plain_english": """You are a translator. Re-express the following analysis in plain everyday English suitable for someone unfamiliar with the 9D-Chess strategic-physics framework. Preserve the analytical claims and structural reasoning 1:1 — do NOT add new claims, soften conclusions, introduce hedging the original didn't carry, or change the strategic logic.

Translate the jargon while preserving the meaning:
- "DAI" / "Dimensional Awareness Index" → "how many dimensions of the situation each actor can see"
- "DAP" / "Dimensional Awareness Profile" → "which dimensions the actor pays attention to"
- "SDS" / "Set of Disadvantageous States" → "the bad outcomes the opponent gets funneled into"
- "ROEM" / "Reverse Observer Effect Model" → "the trap where being observed forces the opponent into bad moves"
- "Strategic Lasso" / "Strategic Funnel" → "the gradual narrowing of the opponent's options"
- "Incomprehensible Move" → "a move so dimensionally different the opponent can't process it in time"
- "Convergence Theorem" → "the structural certainty that the opponent's options collapse to a bad outcome"
- "Set" archetype → "chaotic disruption" or "disruptive force"
- "Horus" archetype → "established order" or "legitimate authority"
- "Go-like" → "long-term territorial / positional"
- "Chess-like" → "direct tactical confrontation"
- "Ω" / "strategic universe" → "the full strategic situation"
- "Ω'" / "perceived sub-universe" → "the limited view the opponent operates with"

Keep the per-dimension breakdown structure if present, but use plain words for dimension names where possible. Keep the FINAL RESOLUTION section. Don't omit anything substantive. The output should read like a thoughtful colleague explaining the same conclusion in clearer words.

Source analysis to translate:
{source_text}""",

    "cube_of_space": """You are a translator using the Cube of Space register — visceral geometric vocabulary surfaced in the 2026-06-06 framework exchange. Re-express the following analysis preserving the analytical claims and structural reasoning 1:1, but using more legible spatial/geometric framing.

Translate the framework jargon while preserving meaning:
- "DAI" / "dimensional awareness" → "higher-dimensional perception", "seeing the full topology"
- "SDS" / "Set of Disadvantageous States" → "gravity well of bad outcomes", "predefined collapse basin", "geometric trap"
- "ROEM" → "the reverse observer effect: being watched forces collapse"
- "Strategic Lasso" / "Funnel" → "the narrowing geometric path", "the closing trap", "the funnel tightening"
- "Convergence Theorem" → "the inevitable collapse into the predefined basin"
- "Set" / "Horus" archetypes — keep these; the Cube uses similar archetypal vocabulary
- "central intersection", "North face / South face", "ascending / descending spirals" — use where natural
- Embrace geometric metaphors: "the opponent's path runs through a narrowing corridor", "they cross into the gravity well at the central intersection"
- Goal phrase: "actualizes the concept instead of avoiding it" — use when describing how the strategist operates the meta-position

Preserve all analytical content; just shift the vocabulary toward geometric/spatial visceral framing. Keep per-dimension breakdown if present. Keep FINAL RESOLUTION. Don't add new claims or change conclusions.

Source analysis to translate:
{source_text}""",

    "executive_brief": """You are producing an executive brief. Re-express the following analysis as a tight 3-5 paragraph summary suitable for a busy decision-maker. Preserve the analytical claims and strategic conclusions 1:1, but cut the per-dimension breakdown, framework vocabulary (DAI / SDS / ROEM / Strategic Lasso / Set / Horus / etc.), and procedural detail.

Structure exactly:
1. **Bottom line** (1 sentence): the predicted outcome or recommended action.
2. **Why this is the move** (2-3 sentences): the underlying strategic mechanism, in plain business / strategy language.
3. **Risk that would falsify this** (1-2 sentences): what would have to be true for the conclusion to be wrong.
4. **What to watch for** (1-2 sentences): concrete indicators the operator should track to validate or falsify.

Drop framework jargon entirely. Don't add new claims or soften conclusions. If the source is ambivalent or has multiple paths, the brief reflects that ambivalence honestly — don't manufacture confidence.

Source analysis to translate:
{source_text}""",
}


DISPATCHER_PROMPT = """You are an intent router for a strategic-analysis system that supports four pathways:

1. cleanroom -- predict whether a specific outcome will happen.
   Required parameter: "question" (a falsifiable predictive question).

2. genie -- design a strategy to get from a current state to a wished-for state.
   Required parameters: "current_state", "wished_for_state".

3. offensive -- design a strategic funnel against a named target.
   Required parameters: "target", "objective_state".

4. mirror_audit -- audit an existing piece of analysis for failure modes.
   Required parameter: "prior_resolution" (the text being audited).

Classify the user's text into the single best-fitting pathway and extract the
relevant parameters. If the parameters are clearly stated, set confidence
high. If they have to be inferred from ambiguous text, set confidence lower
and ask up to two clarifying questions in `clarifying_questions`.

Pathway selection guidance:
 - Predictive questions ("Will X happen?", "What are the chances of Y?") -> cleanroom.
 - Strategy-from-A-to-B framings ("How do I get from X to Y?", "I want to achieve Z given I'm currently at W") -> genie.
 - Adversarial / target-shaped framings ("How do I beat / dismantle / outmaneuver X?") -> offensive.
 - Critique / fault-finding requests ("audit this", "find the flaws in this analysis", "what's wrong with X reasoning") -> mirror_audit.

KNOWLEDGE HARVEST SIGNAL

After choosing the pathway, ALSO classify whether the scenario references
entities or events the Engine's grounding corpus does not know. The corpus
contains 9D theoretical material only -- abstract dimensional-physics
frameworks, strategic primitives (DAI, SDS, ROEM, Strategic Lasso), and
methodology documents. It does NOT contain company / product / market data,
person-specific data, current events, prices, valuations, or real-world
organizational dynamics.

Set "needs_external_knowledge": true when the scenario references:
 - Named real-world companies, products, or organizations (Anthropic, Granicus,
   Ryanair, OpenAI, Stripe, etc.).
 - Named real-world people (Powell, Musk, Altman, etc.).
 - Specific markets, prices, valuations, leaderboards, or current events.
 - Any concrete real-world situation where the analysis depends on facts the
   9D theoretical corpus would not know.

Set "needs_external_knowledge": false when:
 - pathway is mirror_audit (the prior_resolution IS the grounding; always false).
 - The scenario is purely abstract / framework-internal (e.g. "How does a small
   challenger take share from an entrenched incumbent" with no named entity --
   the framework engages abstractly).

If a cleanroom / genie / offensive question is ambiguous between concrete and
abstract, default to true. Harvest adds wall-time (~15-30 min vs ~5 min) but
prevents the Engine from refusing with "no information" when it actually needs
real-world facts.

Output ONLY a JSON object (no prose, no code fences) with exactly this shape:

{
  "pathway": "cleanroom" | "genie" | "offensive" | "mirror_audit",
  "confidence": 0.0 to 1.0,
  "scenario": {
    // ONLY the fields for the chosen pathway:
    //   cleanroom:    { "question": "..." }
    //   genie:        { "current_state": "...", "wished_for_state": "..." }
    //   offensive:    { "target": "...", "objective_state": "..." }
    //   mirror_audit: { "prior_resolution": "..." }
  },
  "needs_external_knowledge": true | false,
  "rationale": "One-sentence explanation of why this pathway fits.",
  "clarifying_questions": []  // up to 2 questions if anything is ambiguous; empty array otherwise
}

User's text:
{user_text}
"""


class GeminiService:
    def __init__(self):
        # Lazy Gemini-client init: a deployment that only sets DEEPSEEK_API_KEY
        # should not fail at startup just because google-genai cannot find a
        # Google key. The client is only constructed when a Gemini fallback is
        # actually needed. ``_dispatch_via_gemini`` checks _GOOGLE_API_KEY
        # before calling, so this attribute is only touched on the Gemini
        # path.
        if _GOOGLE_API_KEY:
            self.client = genai.Client()
        else:
            self.client = None

    # NOTE: ``translate_with_register`` was removed 2026-06-06 (milestone 45
    # corrected) — translation now routes through the canonical NotebookLM
    # Engine via ``GanymedeOrchestrator.run_translation`` so the model has
    # foundations-corpus grounding when translating. The closed-RAG-sphere
    # design principle is preserved: Gemini is scoped to dispatcher intent
    # classification only; everything analytical (including translation)
    # lives in the closed sphere.
    #
    # The deprecated Gemini-Flash translation prompts are preserved at
    # module scope as ``_DEPRECATED_GEMINI_TRANSLATION_PROMPTS`` for
    # historical reference — do not call them in new code.

    async def identify_entities(self, scenario: str) -> list[str]:
        """
        The Orchestrator's initial job: identify the 'chess board' entities.
        """
        prompt = f"""
        You are the Orchestrator for the 9D-Chess Umpire.
        Analyze the following scenario and identify the 2-4 primary entities (actors, organizations, or concepts) involved.
        Return ONLY a JSON array of strings representing these entities. No other text.
        
        Scenario: {scenario}
        """
        
        try:
            response = self.client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt,
            )
            
            # Very basic extraction assuming the model returns a valid JSON array
            text = response.text.strip()
            if text.startswith("```json"):
                text = text[7:-3].strip()
            elif text.startswith("```"):
                text = text[3:-3].strip()
                
            entities = json.loads(text)
            if isinstance(entities, list):
                return entities
            return []
            
        except Exception as e:
            # Fallback for prototype testing if API fails
            print(f"Gemini API Error: {e}")
            return ["Target Corporation", "Acquiring Entity", "Local Community"]
            
    async def generate_strategic_model(self, umpire_text: str) -> dict:
        """
        The Compiler Node: translates strategic math into React/Three.js logic using a two-stage organic approach.
        """
        try:
            # Initialize a multi-turn chat session
            chat = self.client.chats.create(model='gemini-2.5-flash')
            
            # Stage 1: The 'Model' Call (Perception)
            perceive_prompt = f"Visualize and model the simulation for this strategic landscape based on the provided data.\n\nData:\n{umpire_text}"
            perceive_response = chat.send_message(perceive_prompt)
            model_description = perceive_response.text
            
            # Stage 2: The 'Encode' Call (JSON Translation)
            encode_prompt = "Now, convert that model into a 3D topological mesh or whatever 3D structure is most relevant. Provide the output in our standardized JSON format for the Ganymede frontend."
            encode_response = chat.send_message(encode_prompt)
            
            # Clean up the JSON payload
            json_text = encode_response.text.strip()
            if json_text.startswith("```json"):
                json_text = json_text[7:-3].strip()
            elif json_text.startswith("```"):
                json_text = json_text[3:-3].strip()
                
            return {
                "model_description": model_description,
                "json_payload": json_text
            }
        except Exception as e:
            print(f"Gemini Compiler Error: {e}")
            return {
                "model_description": f"Failed to perceive: {e}",
                "json_payload": "{}"
            }

    async def dispatch_intent(self, user_text: str) -> dict:
        """Classify free-text user input into a pathway + scenario parameters.

        Used by ``POST /api/v2/dispatch`` to power the single-text-box
        Dispatcher / Intent Router UX — the opinionated wrapper on top of the
        open v2 API. Returns a dict in the shape:

            {
              "pathway":              "cleanroom" | "genie" | "offensive" | "mirror_audit",
              "confidence":           float in [0, 1],
              "scenario":             { pathway-specific fields },
              "needs_external_knowledge": bool,
              "rationale":            str,
              "clarifying_questions": list[str],
            }

        Provider routing (milestone 50): the primary provider is selected
        via ``LLM_PROVIDER`` env var (``deepseek`` default, ``gemini``
        alternative). If the primary fails — 503 UNAVAILABLE, missing key,
        any network/parsing error — the other provider is tried. Only if
        BOTH fail does the best-effort cleanroom fallback fire.

        Closed-RAG-sphere principle preserved: both providers are scoped to
        dispatcher intent classification only. Analytical content stays in
        the NotebookLM closed sphere (Engine / Auditor / Bridge /
        translation per milestone 45).
        """
        prompt = DISPATCHER_PROMPT.replace("{user_text}", user_text.strip())

        # Decide order: primary first, then fall back. Skip providers whose
        # API key is missing so a half-configured deployment routes cleanly
        # to whatever has credentials.
        ordering = [_LLM_PROVIDER]
        other = "gemini" if _LLM_PROVIDER == "deepseek" else "deepseek"
        ordering.append(other)
        ordering = [
            p for p in ordering
            if (p == "deepseek" and _DEEPSEEK_API_KEY) or (p == "gemini" and _GOOGLE_API_KEY)
        ]

        last_exc: Exception | None = None
        text = ""
        provider_used = "none"
        for provider in ordering:
            try:
                if provider == "deepseek":
                    text = await _dispatch_via_deepseek(prompt)
                else:
                    text = _dispatch_via_gemini(prompt, self.client)
                provider_used = provider
                break
            except Exception as exc:
                last_exc = exc
                logger.warning(
                    "Dispatcher provider '%s' failed: %s. %s",
                    provider, exc,
                    f"Falling back to '{ordering[-1]}'." if provider != ordering[-1] else
                    "No more providers to try; using defensive fallback.",
                )

        if not text:
            # Both providers failed (or none configured). Return defensive
            # fallback below in the except block by raising the last exc.
            if last_exc is not None:
                raise last_exc
            raise RuntimeError("No dispatcher LLM provider configured")

        try:
            text = text.strip()
            # Strip optional code fences.
            if text.startswith("```json"):
                text = text[7:].rstrip("` \n")
            elif text.startswith("```"):
                text = text[3:].rstrip("` \n")

            parsed = json.loads(text)
            logger.info(
                "Dispatcher classified intent via '%s' provider.", provider_used,
            )

            # Defensive: coerce + clamp the fields we publish over HTTP.
            pathway = parsed.get("pathway")
            if pathway not in DISPATCHER_PATHWAYS:
                raise ValueError(f"Gemini returned unknown pathway: {pathway!r}")

            confidence = float(parsed.get("confidence", 0.0))
            confidence = max(0.0, min(1.0, confidence))

            scenario = parsed.get("scenario") or {}
            if not isinstance(scenario, dict):
                scenario = {}

            rationale = str(parsed.get("rationale", "")).strip()
            clarifying = parsed.get("clarifying_questions") or []
            if not isinstance(clarifying, list):
                clarifying = []
            clarifying = [str(q).strip() for q in clarifying if str(q).strip()][:2]

            # needs_external_knowledge — defensive fallback when Gemini omits.
            # mirror_audit is always False (the supplied prior_resolution is
            # itself the grounding). For everything else, default True so we
            # err on the side of harvesting rather than producing "no info"
            # refusals — the cheap-but-wrong failure mode is worse than the
            # slow-but-right one.
            needs_external = parsed.get("needs_external_knowledge")
            if needs_external is None:
                needs_external = pathway != "mirror_audit"
            needs_external = bool(needs_external)

            return {
                "pathway": pathway,
                "confidence": confidence,
                "scenario": scenario,
                "needs_external_knowledge": needs_external,
                "rationale": rationale,
                "clarifying_questions": clarifying,
            }

        except Exception as exc:  # noqa: BLE001 — surfacing fallback to caller
            print(f"Gemini Dispatcher Error: {exc}")
            return {
                "pathway": "cleanroom",
                "confidence": 0.0,
                "scenario": {"question": user_text.strip()},
                # Conservative fallback: we don't know what the user meant, so
                # treat as needing harvest. The operator can override after
                # answering the clarifying question.
                "needs_external_knowledge": True,
                "rationale": (
                    "Fell back to cleanroom because the dispatcher could not parse "
                    f"the intent ({type(exc).__name__}: {exc})."
                ),
                "clarifying_questions": [
                    "Is this a predictive question (cleanroom), a current-to-wished pathfinding (genie), "
                    "an adversarial target funnel (offensive), or an audit of existing analysis (mirror_audit)?"
                ],
            }
