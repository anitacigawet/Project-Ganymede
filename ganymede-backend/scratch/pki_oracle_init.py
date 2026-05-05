import asyncio
import logging
import sys
import hashlib
from app.services.notebooklm_service import NotebookLMService

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

logging.basicConfig(level=logging.INFO)

async def main():
    svc = NotebookLMService()
    await svc.initialize()
    
    # 1. Create a Unique Identifier for the Notebook
    subject_name = "PNT Network Sovereignty"
    nb_name = f"PKI_{subject_name.replace(' ', '_')}"
    nb_hash = hashlib.sha256(nb_name.encode()).hexdigest()[:8]
    full_nb_name = f"{nb_name}_{nb_hash}"
    
    print(f"\n--- PHASE 2: INITIALIZING ORACLE [{full_nb_name}] ---")
    
    try:
        # 2. Create the Notebook using the service method
        nb_id = await svc.create_notebook(full_nb_name)
        print(f"Notebook Created: ID={nb_id}")
        
        # 3. Configure Persona (PKI Oracle)
        await svc.configure_pki_oracle(nb_id)
        print("Persona Locked: PKI Authentication Oracle.")
        
        # 4. Trigger Deep Research
        surgical_prompt = """
Conduct deep research into the current operational readiness and 'cold start' capabilities of terrestrial, land-based backup navigation systems (eLoran, Chayka, and STL). 

Identify which specific nations (specifically the USA, China, Russia, and the UK) have active infrastructure that can be fully activated within 72 hours of a total satellite signal blackout. 

Document transmitter locations and verified signal coverage areas. 

NOTE: Use your internal deep research capabilities to find the most current and verified data. Output only raw, high-resolution facts with source hashes.
""".strip()
        
        print("\nTriggering Deep Research Session...")
        # Note: If the API doesn't have a specific research method, 
        # we ask it via the standard chat.
        result = await svc.query_notebook(nb_id, surgical_prompt)
        
        print("\n--- ORACLE HARVEST RECEIVED ---")
        print(result)
        
    except Exception as e:
        print(f"Error during Oracle initialization: {e}")

if __name__ == "__main__":
    asyncio.run(main())
