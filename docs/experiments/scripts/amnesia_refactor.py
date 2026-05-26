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
    
    # REFACTOR DIRECTIVE
    refactor_prompt = """
REFACTOR REQUEST: 

The PKI Oracles (Research Extenders) do not have access to your internal 9D Jargon, Metrics, or Theorems. They are standard research engines. 

You must REFACTOR your 3 Oracle requirements into SURGICAL PLAIN-LANGUAGE PROMPTS. 

- Focus on the REAL-WORLD DATA you need to solve the 60-Second Amnesia simulation (e.g., specific military fail-safe protocols, international financial law regarding identity failure, or psychological studies on temporary global amnesia). 
- REMOVE all references to '9D', 'ROEM', 'SDS', 'D1-D9', or any Umpire-only terminology. 
- Prompt them like a professional human researcher looking for verifiable, high-fidelity OSINT data.

Provide the refactored prompts now.
""".strip()
    
    print("\n--- REQUESTING PLAIN-LANGUAGE REFACTORING FROM UMPIRE ---")
    
    try:
        refactored = await svc.query_chess_engine(refactor_prompt)
        print("\n--- REFACTORED RESEARCH PROMPTS ---")
        print(refactored)
    except Exception as e:
        print(f"Error during refactoring: {e}")

if __name__ == "__main__":
    asyncio.run(main())
