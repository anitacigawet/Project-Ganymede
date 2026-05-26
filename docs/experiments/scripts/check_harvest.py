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
    
    nb_id = "67fbf8e2-66a5-4474-b83a-7426ec9fdc50"
    
    print(f"\n--- PHASE 2: CHECKING HARVEST STATUS FOR ORACLE [{nb_id}] ---")
    
    try:
        # Check if the research is done by asking for the Truth Packet
        harvest_prompt = """
Has the deep research into eLoran, Chayka, and STL finished? 

If so, please output the final Truth Packet (raw facts with source hashes) as requested. 

If it is still in progress, please state 'RESEARCH IN PROGRESS'.
""".strip()
        
        result = await svc.query_notebook(nb_id, harvest_prompt)
        
        print("\n--- ORACLE RESPONSE ---")
        print(result)
        
    except Exception as e:
        print(f"Error during harvest check: {e}")

if __name__ == "__main__":
    asyncio.run(main())
