import os
from google import genai
from google.genai import types
import json

# The four pathways the dispatcher classifies intent into. Kept here as a
# string list (rather than importing the Pathway enum from app.contracts) so
# this service stays a thin LLM wrapper with no orchestrator dependencies.
DISPATCHER_PATHWAYS = ("cleanroom", "genie", "offensive", "mirror_audit")


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
  "rationale": "One-sentence explanation of why this pathway fits.",
  "clarifying_questions": []  // up to 2 questions if anything is ambiguous; empty array otherwise
}

User's text:
{user_text}
"""


class GeminiService:
    def __init__(self):
        # The client automatically picks up GOOGLE_API_KEY from environment variables
        self.client = genai.Client()

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
              "rationale":            str,
              "clarifying_questions": list[str],
            }

        On any LLM / parsing failure this returns a best-effort fallback
        (``cleanroom`` with the user's text as ``question``, low confidence,
        and an explanatory clarifying question) rather than raising. The
        caller is expected to surface the result to the operator for review
        before the heavy 3-stroke loop fires.
        """
        prompt = DISPATCHER_PROMPT.replace("{user_text}", user_text.strip())

        try:
            response = self.client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
            )
            text = (response.text or "").strip()
            # Strip optional code fences.
            if text.startswith("```json"):
                text = text[7:].rstrip("` \n")
            elif text.startswith("```"):
                text = text[3:].rstrip("` \n")

            parsed = json.loads(text)

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

            return {
                "pathway": pathway,
                "confidence": confidence,
                "scenario": scenario,
                "rationale": rationale,
                "clarifying_questions": clarifying,
            }

        except Exception as exc:  # noqa: BLE001 — surfacing fallback to caller
            print(f"Gemini Dispatcher Error: {exc}")
            return {
                "pathway": "cleanroom",
                "confidence": 0.0,
                "scenario": {"question": user_text.strip()},
                "rationale": (
                    "Fell back to cleanroom because the dispatcher could not parse "
                    f"the intent ({type(exc).__name__}: {exc})."
                ),
                "clarifying_questions": [
                    "Is this a predictive question (cleanroom), a current-to-wished pathfinding (genie), "
                    "an adversarial target funnel (offensive), or an audit of existing analysis (mirror_audit)?"
                ],
            }
