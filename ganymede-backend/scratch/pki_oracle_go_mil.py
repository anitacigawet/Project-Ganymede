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
    
    nb_id = "100477d3-6031-4951-bb84-7f50334ae298"
    
    print(f"\n--- PHASE 2: SENDING 'GO' SIGNAL TO ORACLE [{nb_id}] ---")
    
    try:
        go_prompt = "YES. PROCEED. Execute the deep research now into the Military SOPs and 'Decision Path Funneling' regarding total PNT signal loss."
        
        print("Sending signal and waiting for research to initiate...")
        result = await svc.query_notebook(nb_id, go_prompt)
        
        print("\n--- ORACLE CONFIRMATION RECEIVED ---")
        print(result)
        
    except Exception as e:
        print(f"Error during Oracle 'GO' signal: {e}")

if __name__ == "__main__":
    asyncio.run(main())
