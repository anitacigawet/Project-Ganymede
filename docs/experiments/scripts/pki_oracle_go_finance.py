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
    
    nb_id = "9d75b383-c11e-4e48-830a-9125e221a57c"
    
    print(f"\n--- PHASE 2: SENDING 'GO' SIGNAL TO ORACLE [{nb_id}] ---")
    
    try:
        go_prompt = "YES. PROCEED. Execute the deep research now into the 'Termination-Trigger' criteria for algorithmic contracts and the impact of identity-persistence failure on global liquidity."
        
        print("Sending signal and waiting for research to initiate...")
        result = await svc.query_notebook(nb_id, go_prompt)
        
        print("\n--- ORACLE CONFIRMATION RECEIVED ---")
        print(result)
        
    except Exception as e:
        print(f"Error during Oracle 'GO' signal: {e}")

if __name__ == "__main__":
    asyncio.run(main())
