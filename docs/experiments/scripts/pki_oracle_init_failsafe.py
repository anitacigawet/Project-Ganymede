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
    
    subject_name = "High-Security FailSafe"
    nb_name = f"PKI_{subject_name.replace(' ', '_')}"
    nb_hash = hashlib.sha256(nb_name.encode()).hexdigest()[:8]
    full_nb_name = f"{nb_name}_{nb_hash}"
    
    print(f"\n--- PHASE 2: INITIALIZING ORACLE [{full_nb_name}] ---")
    
    try:
        nb_id = await svc.create_notebook(full_nb_name)
        print(f"Notebook Created: ID={nb_id}")
        
        await svc.configure_pki_oracle(nb_id)
        print("Persona Locked: PKI Authentication Oracle.")
        
        # Umpire's Refactored Prompt 1
        surgical_prompt = """
Conduct a deep research dive into the 'Fail-Safe' and 'Dead Hand' protocols of the major global nuclear and strategic command systems (specifically the USA, Russia, and China). 

I require specific, unclassified documentation on how these systems handle a total 'Identity Verification Failure' at the highest command levels. 

Specifically, identify whether automated systems default to a 'Locked' state or a 'Pre-Delegated' operational state when a human commander cannot provide identity-authenticated confirmation for a 60-to-120 second window.

NOTE: Use your internal deep research capabilities to find the most current and verified data. Output only raw, high-resolution facts with source hashes.
""".strip()
        
        print("\nTriggering Deep Research Session...")
        result = await svc.query_notebook(nb_id, surgical_prompt)
        
        print("\n--- ORACLE RESPONSE ---")
        print(result)
        
    except Exception as e:
        print(f"Error during Oracle initialization: {e}")

if __name__ == "__main__":
    asyncio.run(main())
