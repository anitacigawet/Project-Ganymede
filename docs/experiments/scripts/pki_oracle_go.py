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
    
    nb_id = "67fbf8e2-66a5-4474-b83a-7426ec9fdc50"
    
    print(f"\n--- PHASE 2: SENDING 'GO' SIGNAL TO ORACLE [{nb_id}] ---")
    
    try:
        # The GO Signal
        go_prompt = "YES. PROCEED. Execute the deep research now and extract the Truth Packet. Focus strictly on the eLoran, Chayka, and STL operational readiness."
        
        print("Sending signal and waiting for research to initiate...")
        result = await svc.query_notebook(nb_id, go_prompt)
        
        print("\n--- ORACLE CONFIRMATION RECEIVED ---")
        print(result)
        
    except Exception as e:
        print(f"Error during Oracle 'GO' signal: {e}")

if __name__ == "__main__":
    asyncio.run(main())
