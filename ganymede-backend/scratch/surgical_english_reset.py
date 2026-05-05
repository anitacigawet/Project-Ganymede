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
    
    # THE SURGICAL ENGLISH RESET
    reset_prompt = """
Umpire, provide the final research requirement for the 'Human Nuance Oracle' regarding the 60-Second Amnesia Event.

MANDATORY CONSTRAINTS:
1. Use ONLY 'Surgical Plain-Language.' 
2. You are FORBIDDEN from using any internal mythology, '9D' jargon, or terms like 'Pillars', 'Horus', or 'Mnemosyne'.
3. Focus strictly on Real-World Social Science and Neuro-Psychology. 
4. The mission is to research: How fast 'Habit Loops' (procedural memory) and 'Emergent Social Order' (natural grouping) allow a confused population to reorganize themselves when episodic memory is lost. 

Prompt this like a professional human researcher looking for verifiable, peer-reviewed academic/OSINT data. Output ONLY the surgical prompt.
""".strip()
    
    print("\n--- EXECUTING SURGICAL ENGLISH RESET ---")
    
    try:
        surgical_prompt = await svc.query_chess_engine(reset_prompt)
        print("\n--- THE SURGICAL RESEARCH PROMPT ---")
        print(surgical_prompt)
    except Exception as e:
        print(f"Error during surgical reset: {e}")

if __name__ == "__main__":
    asyncio.run(main())
