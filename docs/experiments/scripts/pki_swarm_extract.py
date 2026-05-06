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
    
    oracles = {
        "Fail-Safe": "2c5d6695-cc9d-45d4-a69d-88efbe4b5f69",
        "Financial": "9d75b383-c11e-4e48-830a-9125e221a57c",
        "Psychological": "21d4c8eb-bcc1-4329-a8c7-6a00d66b3f01"
    }
    
    print("\n--- INITIATING SWARM EXTRACTION (PHASE 3) ---")
    
    for name, nb_id in oracles.items():
        print(f"\n[{name}] Querying Truth Packet...")
        query = "Provide the final Truth Packet for this simulation. Output only the high-resolution facts discovered via deep research. Include source hashes if available."
        try:
            packet = await svc.query_notebook(nb_id, query)
            print(f"[{name}] HARVEST RECEIVED:")
            print(packet)
        except Exception as e:
            print(f"[{name}] Extraction failed: {e}")

if __name__ == "__main__":
    asyncio.run(main())
