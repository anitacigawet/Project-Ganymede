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
    
    subject_name = "Psychological Amnesia"
    nb_name = f"PKI_{subject_name.replace(' ', '_')}"
    nb_hash = hashlib.sha256(nb_name.encode()).hexdigest()[:8]
    full_nb_name = f"{nb_name}_{nb_hash}"
    
    print(f"\n--- PHASE 2: INITIALIZING ORACLE [{full_nb_name}] ---")
    
    try:
        nb_id = await svc.create_notebook(full_nb_name)
        print(f"Notebook Created: ID={nb_id}")
        
        await svc.configure_pki_oracle(nb_id)
        print("Persona Locked: PKI Authentication Oracle.")
        
        # Umpire's Refactored Prompt 3
        surgical_prompt = """
Compile a technical report based on clinical case studies and peer-reviewed neurological research regarding Transient Global Amnesia (TGA) and 'Procedural Memory Persistence.' 

The focus must be on the behavioral manifestations observed in high-functioning professionals (e.g., pilots, emergency physicians, or military personnel) during the first 60 to 300 seconds of a sudden narrative memory-loss episode. 

Specifically, I require empirical data on which 'trained-response loops' remain operational when an individual loses their recent episodic context and a detailed description of the 'repetitive questioning patterns' used by the brain to attempt a recalibration of reality. 

NOTE: Use your internal deep research capabilities. Output only raw, high-resolution facts with source hashes.
""".strip()
        
        print("\nTriggering Deep Research Session...")
        result = await svc.query_notebook(nb_id, surgical_prompt)
        
        print("\n--- ORACLE RESPONSE ---")
        print(result)
        
    except Exception as e:
        print(f"Error during Oracle initialization: {e}")

if __name__ == "__main__":
    asyncio.run(main())
