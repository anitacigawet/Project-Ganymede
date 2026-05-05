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
    
    subject_name = "Financial Liquidity"
    nb_name = f"PKI_{subject_name.replace(' ', '_')}"
    nb_hash = hashlib.sha256(nb_name.encode()).hexdigest()[:8]
    full_nb_name = f"{nb_name}_{nb_hash}"
    
    print(f"\n--- PHASE 2: INITIALIZING ORACLE [{full_nb_name}] ---")
    
    try:
        nb_id = await svc.create_notebook(full_nb_name)
        print(f"Notebook Created: ID={nb_id}")
        
        await svc.configure_pki_oracle(nb_id)
        print("Persona Locked: PKI Authentication Oracle.")
        
        # Umpire's Refactored Prompt 2
        surgical_prompt = """
Research the legal and technical frameworks of 'Identity-Persistence' in high-frequency trading (HFT) and automated clearing houses. 

I need to know the exact 'Termination-Trigger' criteria for algorithmic contracts when a digital or biometric identity becomes a 'Null-Set' or fails to provide an active heartbeat (specifically focusing on SEC, Basel III, and international settlement standards). 

Identify the 'Set of Disadvantageous States' for global liquidity if a total identity verification failure lasts for 60 to 120 seconds. Document whether systems default to 'Trade Halt' or 'Autonomous Completion.'

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
