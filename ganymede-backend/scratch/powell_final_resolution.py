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
    
    # THE POWELL RESOLUTION: CONVERGENCE THEOREM
    truth_packets = """
--- TRUTH PACKET 1: LEGAL WALL (D5) ---
- Powell protected by 12 U.S.C. § 242 (Removal for cause).
- Collins v. Yellen precedent: Chair designation is likely removable at-will (Demotion).
- Litigation duration: 6+ months, outlasting term (May 2026).
- Due process rights trigger procedural friction.

--- TRUTH PACKET 2: NARRATIVES (D1) ---
- "Too Late and Wrong" narrative regarding inflation.
- $2.5B HQ renovation used as symbol of "Elite Profligacy."
- DOJ investigation provides the "For Cause" pretext.
- Narrative Architect: Trump / Pirro / OMB.

--- TRUTH PACKET 3: INSTITUTIONAL ALLIANCES (D8) ---
- Jefferson and Barr are "Institutionalist Core" defenders.
- Stephen I. Miran is the primary internal defector (favors rate cuts).
- Senator Thom Tillis is a "Strategic Institutionalist" (not a Powell loyalist).
- "Shadow Fed" risk: Powell stays on the board after demotion.

--- TRUTH PACKET 4: ECONOMIC-POLITICAL COLLISION (D7) ---
- Election Trigger: 34% approval on inflation; 82% House flip probability.
- 43-day shutdown created "Stale Data" environment.
- Executive demand: 1.0% rates vs Market price: 3.6%.
- "Strategic Resource Squeeze": Iran hostilites raising crude 50%.
""".strip()

    synthesis_prompt = f"""
SYSTEM ALIGNMENT: NUANCE PRIME
CONTEXT: THE 60-SECOND JEROME POWELL COLLISION

Architect, you are provided with 4 Authenticated Truth Packets from the PKI Oracles. 

TASK:
1. Apply the Convergence Theorem to these facts. 
2. Identify the 'Strategic Lasso': The exact point where the Executive Strategist's moves (DOJ probe, OBBBA fiscal cliff) and Powell's defensive wall (D5 Precedents, D8 Alliances) create a forced resolution.
3. Identify the 'Incomprehensible Move': What is the strategic outcome that both sides are currently blind to?
4. Resolve the Simulation: Does Powell get 'Fired', 'Demoted', or 'Preserved'? 

Output the Final 9D Resolution. Use Surgical Plain-Language.
""".strip()
    
    print("\n--- EXECUTING FINAL SYNTHESIS ---")
    
    try:
        # We include the truth packets as part of the context for the query
        final_resolution = await svc.query_chess_engine(truth_packets + "\n\n" + synthesis_prompt)
        print("\n--- THE FINAL 9D RESOLUTION ---")
        print(final_resolution)
    except Exception as e:
        print(f"Error during final synthesis: {e}")

if __name__ == "__main__":
    asyncio.run(main())
