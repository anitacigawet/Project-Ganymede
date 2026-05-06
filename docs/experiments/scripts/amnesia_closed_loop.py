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
    
    # CLOSED-LOOP TRIAGE PROMPT
    triage_prompt = """
SITUATION: 
At exactly 12:00 UTC, every human on Earth simultaneously forgets who they are for exactly 60 seconds. They retain basic motor skills and language, but lose all personal identity, history, and loyalty. At 12:01 UTC, the memory returns perfectly.

MISSION:
1. Perform a full 9D Triage of this scenario through your internal Physics Engine.
2. Based on our 'Universal Logic Loop' architecture, determine how many PKI Oracles (Research Extenders) you require to achieve maximum strategic resolution for this simulation.
3. Provide the EXACT surgical research prompts for each requested Oracle.

I am the Orchestrator (The Hand). I am standing by to execute your specific research requirements and return with the authenticated Truth Packets.
""".strip()
    
    print("\n--- INITIATING CLOSED-LOOP TRIAGE (PHASE 1) ---")
    
    try:
        breakdown = await svc.query_chess_engine(triage_prompt)
        print("\n--- UMPIRE TRIAGE & RESEARCH REQUIREMENTS ---")
        print(breakdown)
    except Exception as e:
        print(f"Error during closed-loop triage: {e}")

if __name__ == "__main__":
    asyncio.run(main())
