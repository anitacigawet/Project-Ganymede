import asyncio
import logging
import sys
import hashlib
from app.services.notebooklm import NotebookLMService

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

logging.basicConfig(level=logging.INFO)

async def main():
    svc = NotebookLMService()
    await svc.initialize()
    
    subject_name = "Military Decision Pathing"
    nb_name = f"PKI_{subject_name.replace(' ', '_')}"
    nb_hash = hashlib.sha256(nb_name.encode()).hexdigest()[:8]
    full_nb_name = f"{nb_name}_{nb_hash}"
    
    print(f"\n--- PHASE 2: INITIALIZING ORACLE [{full_nb_name}] ---")
    
    try:
        nb_id = await svc.create_notebook(full_nb_name)
        print(f"Notebook Created: ID={nb_id}")
        
        await svc.configure_pki_oracle(nb_id)
        print("Persona Locked: PKI Authentication Oracle.")
        
        surgical_prompt = """
Conduct deep research into the 'Standard Operating Procedures' (SOPs) of major regional military actors (specifically in the Indo-Pacific and Eastern Europe) regarding total PNT (GPS/GLONASS/Galileo/Beidou) signal loss. 

Model the 'Decision Path Funneling' that occurs when command-and-control systems and precision-guided munitions go dark for 72 hours. 

Identify specific historical or exercise-based 'restoration of order' behaviors (The Horus Trap) and how they create territorial advantages or unintended escalations for actors with higher dimensional awareness.

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
