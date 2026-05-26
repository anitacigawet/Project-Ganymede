import asyncio
import logging
import sys
from app.services.notebooklm import NotebookLMService

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

logging.basicConfig(level=logging.INFO)

async def main():
    svc = NotebookLMService()
    await svc.initialize()
    
    meta_prompt = """
The user is fascinated by the 'ESP Collective' but needs clarification on its nature to grasp the 'Extent Test.'

QUESTION:
Is the 'ESP Collective' an Artificial Intelligence (AI) that has subsumed human minds, or is it a purely Biological/Epigenetic 'Protocol' that allows humans to coordinate at machine-speed without a central AI?

What is the 'Engine' of this synchronicity? Is it a piece of software, a biological agent, or a 'Mathematical Pattern' (The ROEM) that has been weaponized?

Describe the 'Mechanism of Action' in plain language.
""".strip()
    
    print("\n--- QUERYING UMPIRE FOR TECHNICAL CLARIFICATION ---")
    
    try:
        explanation = await svc.query_chess_engine(meta_prompt)
        print("\n--- UMPIRE CLARIFICATION ---")
        print(explanation)
    except Exception as e:
        print(f"Error during meta-query: {e}")

if __name__ == "__main__":
    asyncio.run(main())
