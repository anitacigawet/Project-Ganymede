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
    
    print(f"\n--- PHASE 2: EXTRACTING TRUTH PACKET FROM ORACLE [{nb_id}] ---")
    
    try:
        # Final Extraction Query
        extraction_prompt = """
Based on the 21 imported sources, provide the final Truth Packet regarding the operational readiness of eLoran, Chayka, and STL. 

Specify which nations (USA, China, Russia, UK) can achieve a 'Cold Start' (full activation) of these terrestrial backups within 72 hours of GPS failure. 

Document verified transmitter locations and coverage percentages. 

OUTPUT FORMAT: Strict raw facts, individually cited with source hashes (e.g., [SRC-PNT:abcdef]). No conversational filler.
""".strip()
        
        result = await svc.query_notebook(nb_id, extraction_prompt)
        
        print("\n--- FINAL TRUTH PACKET RECEIVED ---")
        print(result)
        
    except Exception as e:
        print(f"Error during Truth Packet extraction: {e}")

if __name__ == "__main__":
    asyncio.run(main())
