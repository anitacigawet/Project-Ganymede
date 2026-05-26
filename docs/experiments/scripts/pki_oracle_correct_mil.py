import asyncio
import logging
import sys
from app.services.notebooklm import NotebookLMService

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

logging.basicConfig(level=logging.INFO)

async def main():
    svc = NotebookLMService()
    await svc.initialize()
    
    nb_id = "100477d3-6031-4951-bb84-7f50334ae298"
    
    print(f"\n--- PHASE 2: SENDING CORRECTED SURGICAL PROMPT TO ORACLE [{nb_id}] ---")
    
    try:
        # Surgical Plain-Language Prompt
        corrected_prompt = """
Conduct deep research into the Standard Operating Procedures (SOPs) of the United States, Chinese, and Russian militaries regarding Positioning, Navigation, and Timing (PNT) signal loss (specifically GPS, Beidou, and GLONASS outages). 

Look for unclassified reports on 'EMCON' (Emission Control) procedures, celestial navigation backups, and inertial navigation system (INS) reliability during electronic warfare exercises. 

Document any recorded instances of 'escalation risks' or 'procedural confusion' identified during PNT-denied training exercises in the South China Sea or Eastern Europe.

NOTE: Use your internal deep research capabilities to find the most current and verified data. Output only raw, high-resolution facts with source hashes.
""".strip()
        
        print("Sending corrected prompt and waiting for research offer...")
        result = await svc.query_notebook(nb_id, corrected_prompt)
        
        print("\n--- ORACLE RESPONSE (CORRECTED) ---")
        print(result)
        
    except Exception as e:
        print(f"Error during Oracle correction: {e}")

if __name__ == "__main__":
    asyncio.run(main())
