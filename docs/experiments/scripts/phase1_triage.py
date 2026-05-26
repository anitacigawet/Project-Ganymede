import asyncio
import logging
import sys
from app.services.notebooklm import NotebookLMService

# Force UTF-8 for printing to avoid encoding errors on Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

logging.basicConfig(level=logging.INFO)

async def main():
    svc = NotebookLMService()
    await svc.initialize()
    
    scenario = "The sudden, absolute failure of all satellite-based GPS systems globally for 72 hours."
    
    prompt = f"""
SITUATION INGESTION: {scenario}

MISSION: 
Perform a 9D Strategic Breakdown of this situation. Identify the core subjects, entities, and dimensions involved.

RESTRICTION:
You must generate a "Strategic Hit List" of research subjects for our PKI Oracle swarm. 
To prevent system sprawl, LIMIT this list to the top 3-5 most critical, high-impact subjects that require factual verification to understand the cascading failure points. 

Output the Breakdown and the Hit List clearly.
""".strip()
    
    print("\n--- PHASE 1: TRIAGE START ---")
    
    try:
        analysis = await svc.query_chess_engine(prompt)
        print("\n--- UMPIRE ANALYSIS RECEIVED ---")
        print(analysis)
    except Exception as e:
        print(f"Error during triage: {e}")

if __name__ == "__main__":
    asyncio.run(main())
