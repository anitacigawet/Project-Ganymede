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
    
    subject_name = "JIT Logistics Terminal Failure"
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
Conduct deep research into the 'Strategic Funnel' points of global Just-in-Time (JIT) logistics, specifically in the maritime and semiconductor sectors. 

Identify the exact 'Time-to-Terminal-Failure' (TTF) for major ports (Singapore, Rotterdam, Long Beach) when automated container tracking and GPS-dependent port management systems are disabled for 72 hours. 

Document verified 'recovery thresholds'—the point after which a supply chain cannot be restored without a total system reset.

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
