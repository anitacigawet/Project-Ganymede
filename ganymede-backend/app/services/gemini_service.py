import os
from google import genai
from google.genai import types
import json

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
