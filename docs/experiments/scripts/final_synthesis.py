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
    
    # PHASE 4: FINAL COLLISION SYNTHESIS
    # Feeding the authenticated Truth Packets back to the 9D Chess Engine.
    synthesis_prompt = """
MISSION: PHASE 4 - FINAL COLLISION SYNTHESIS (60-Second Amnesia Event)

TRUTH PACKETS RECEIVED:
1. [Fail-Safe]: US NC3 systems default to INHIBITION (Locked) state during 60s identity failure. Russian 'Perimeter' system defaults to PRE-DELEGATED (Autonomous-ready) state. 
2. [Financial]: 120-second API persistence allows HFT bots to continue trading. Sudden 'Exit to Neutral' triggers massive liquidation into gold/cash within the 60s window. 
3. [Psychological]: High-functioning professionals (pilots/military) maintain 'Muscle Memory' but enter a 'Loop of 3' (20-second identity refresh loop) during narrative amnesia.

TASK:
1. Synthesize these authenticated facts through your 9D Physics Engine.
2. Resolve the global 'Set of Disadvantageous States' (SDS) for the 'Institutional Status Quo.'
3. Identify the 'Incomprehensible Move' that occurs during the 60-second void.
4. Output the final 'Resolution of the Game.'

OUTPUT: Raw 9D Strategic Resolution. No narrative fluff.
""".strip()
    
    print("\n--- INITIATING FINAL 9D SYNTHESIS ---")
    
    try:
        resolution = await svc.query_chess_engine(synthesis_prompt)
        print("\n--- THE 9D RESOLUTION ---")
        print(resolution)
    except Exception as e:
        print(f"Error during final synthesis: {e}")

if __name__ == "__main__":
    asyncio.run(main())
