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
    
    # THE TOKENIZED LAND RESOLUTION: CONVERGENCE THEOREM
    master_truth_packet = """
--- CONSOLIDATED TRUTH PACKET: TOKENIZED LAND GAMBIT ---

PILLAR 1: SOVEREIGN DEBT & IMF (D8/D5)
- Tokenization = "Structural Waiver" of sovereign immunity via commercial activity exception.
- Assets subject to private-law commercial transaction enforcement.
- Integration into IMF SDR framework triggers Article XIX, Section 2(c).

PILLAR 2: RWA & NATURAL CAPITAL (D7)
- Market Cap: $35B-$50B. 
- Liquidity Engines: KlimaDAO, Uniswap AMMs (200-300x capital efficiency).
- Valuation: TEV (Total Economic Value) + InVEST spatial algorithms + 2% Social Discount Rate.

PILLAR 3: NATIONAL LAND SENTIMENT (D1/D5)
- Argentina Loss Aversion: 2.54x (losses weighed heavier than gains).
- Territorial disputes = "Certain Loss" leading to aggressive risk-acceptance.
- Malvinas Trauma: Territorial defense is a non-negotiable constitutional objective.
- Hostility toward "Soiled Sovereignty" (foreign land control).

PILLAR 4: DIGITAL FORECLOSURE (D6/D4)
- Self-executing smart contracts (ERC-4337) divert revenue automatically.
- Autonomous "Liquidator Agents" execute foreclosure without human intervention.
- Conservation Easements: Permanent legal encumbrance (in rem anchor).
- Shift toward Decentralized Justice Systems (DJS) for dispute resolution.
""".strip()

    synthesis_prompt = f"""
SYSTEM ALIGNMENT: NUANCE PRIME
CONTEXT: THE TOKENIZED LAND GAMBIT (Ω)

Architect, you are provided with the Consolidated Truth Packet from the Master Silo. 

TASK:
1. Apply the Convergence Theorem to these facts. 
2. Identify the 'Strategic Lasso': The point where the 'Autonomous Liquidator Agents' (D4/D7) and the 'Nationalist Loss Aversion' (D1/D8) create a forced resolution.
3. Identify the 'Incomprehensible Move': What is the strategic outcome that both the Nation and the IMF are currently blind to?
4. Resolve the Simulation: Does the nation achieve 'Sovereign Rebirth' or 'Functional Obsolescence'? 

Output the Final 9D Resolution. Use Surgical Plain-Language.
""".strip()
    
    print("\n--- EXECUTING FINAL SYNTHESIS ---")
    
    try:
        final_resolution = await svc.query_chess_engine(master_truth_packet + "\n\n" + synthesis_prompt)
        print("\n--- THE FINAL 9D RESOLUTION ---")
        print(final_resolution)
    except Exception as e:
        print(f"Error during final synthesis: {e}")

if __name__ == "__main__":
    asyncio.run(main())
