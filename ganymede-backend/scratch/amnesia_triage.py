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
    
    # PHASE 1: THE AMNESIA TRIAGE
    triage_prompt = """
MISSION: PHASE 1 - THE AMNESIA TRIAGE

SITUATION: 
At exactly 12:00 UTC, every human on Earth simultaneously forgets who they are for exactly 60 seconds. They retain basic motor skills and language, but lose all personal identity, history, and loyalty. At 12:01 UTC, the memory returns perfectly.

TASK:
Break down this 'Identity Liquidation' across the 9D map. 
1. Identify the 'Gravity Wells' (Critical Failure Points) created during those 60 seconds (specifically regarding Military Command, Financial Markets, and Social Contracts).
2. Identify the top 3 'Critical Subjects' that our PKI Oracle Swarm must research to validate the 'Temporal Damage' of this event.
3. Model the 'Set of Disadvantageous States' (SDS) for a world that has experienced a total 'Un-Observation' of its own history.

OUTPUT: Raw 9D Strategic Breakdown. No narrative fluff.
""".strip()
    
    print("\n--- INITIATING THE AMNESIA TRIAGE (PHASE 1) ---")
    
    try:
        breakdown = await svc.query_chess_engine(triage_prompt)
        print("\n--- THE AMNESIA TRIAGE BREAKDOWN ---")
        print(breakdown)
    except Exception as e:
        print(f"Error during amnesia triage: {e}")

if __name__ == "__main__":
    asyncio.run(main())
