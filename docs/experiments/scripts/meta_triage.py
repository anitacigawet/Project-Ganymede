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
    
    # Meta-Query to the Umpire
    meta_prompt = """
SITREP: 
We have successfully institutionalized the 'Universal Logic Loop' Protocol. 
We have:
1. A 3D GSS (Ganymede Strategic Schema) Physics Visualizer for topological output.
2. A swarm of dynamic PKI Oracles acting as high-fidelity 'Research Extenders' with deep research capabilities.
3. A Recursive Dialogue Protocol for increasing strategic resolution.

MISSION: 
As the Master Logic Engine (Umpire), you are being asked to architect the next simulation. 
We need a scenario or an 'Entity Collision' that demonstrates the absolute MAXIMUM EXTENT of this 9D system. 

It should be a situation that:
- Forces the PKI Oracles to their research limits.
- Pushes the 9D Physics Engine to its highest logical resolution.
- Illustrates the 'Sets of Disadvantageous States' (SDS) in a way that is visceral and undeniable.

What scenario do you propose for our next 'Extent Test'?
""".strip()
    
    print("\n--- CONSULTING THE MASTER LOGIC ENGINE (PHASE 0) ---")
    
    try:
        proposal = await svc.query_chess_engine(meta_prompt)
        print("\n--- UMPIRE STRATEGIC PROPOSAL ---")
        print(proposal)
    except Exception as e:
        print(f"Error during meta-query: {e}")

if __name__ == "__main__":
    asyncio.run(main())
