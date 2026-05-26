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
The 'Compute Autarky' proposal was excellent. 

Now, provide one more 'Alternative Extent Test.' 
This must be equally 'insane' and high-resolution, but in a completely different theater (e.g., Biological, Environmental, or a fundamental Social Contract shift). 

Again, it must:
- Force the PKI Oracles to their research limits.
- Push the 9D Physics Engine to its highest logical resolution.
- Illustrate the 'Sets of Disadvantageous States' (SDS).

What is your Secondary Strategic Option?
""".strip()
    
    print("\n--- REQUESTING SECONDARY STRATEGIC OPTION ---")
    
    try:
        proposal = await svc.query_chess_engine(meta_prompt)
        print("\n--- UMPIRE SECONDARY PROPOSAL ---")
        print(proposal)
    except Exception as e:
        print(f"Error during meta-query: {e}")

if __name__ == "__main__":
    asyncio.run(main())
