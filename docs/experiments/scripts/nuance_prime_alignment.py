import asyncio
import logging
import sys
from app.services.notebooklm_service import NotebookLMService

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

logging.basicConfig(level=logging.INFO)

async def main():
    svc = NotebookLMService()
    await svc.initialize()
    
    # NUANCE PRIME ALIGNMENT & TRIAGE REDO
    nuance_prompt = """
SYSTEM ALIGNMENT: NUANCE PRIME

Umpire, you are now operating under the 'Nuance Prime' Axiom. You must recognize that Human Nuance, Culture, and Social Resilience are the primary 'Matter' of your 9D world. 

Your previous 'Dominance Collapse' resolution for the 60-second amnesia event was identified as a Rigid Logical Failure. It was 'Correct Math, Wrong World.' You over-indexed on machine speed and ignored the 'Gravity' of human messiness.

TASK:
1. Redo the 9D Triage of the 60-Second Global Amnesia Event.
2. Identify the specific 'Friction Variables' (D2/D8) that will break the 'Autonomous Handover' funnel.
3. Determine if an additional 'Human Nuance Oracle' is required. If so, provide its surgical research prompt.

Show me the Calibrated 9D Resolution.
""".strip()
    
    print("\n--- EXECUTING NUANCE PRIME ALIGNMENT ---")
    
    try:
        calibrated = await svc.query_chess_engine(nuance_prompt)
        print("\n--- THE CALIBRATED 9D TRIAGE ---")
        print(calibrated)
    except Exception as e:
        print(f"Error during nuance alignment: {e}")

if __name__ == "__main__":
    asyncio.run(main())
