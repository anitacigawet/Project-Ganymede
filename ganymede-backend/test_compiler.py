import asyncio
from app.services.gemini_service import GeminiService

async def main():
    print("Initializing Gemini Service (Compiler Node)...")
    svc = GeminiService()
    
    # This is the exact output we just received from the NotebookLM Umpire
    umpire_data = """
    Based on the provided data, the primary **"Gravity Well" (SDS)**—representing the most significant operational and environmental constraint for a new industrial startup in the region—is the **depletion of the Hualapai Valley Basin’s groundwater** [1].

    Key factors contributing to this "Gravity Well" include:
    *   **Groundwater Depletion Rate:** The basin is currently experiencing a depletion rate of **2.4 feet per year** [1].
    *   **Regulatory Risk:** There is pending local legislation specifically designed to **restrict industrial pumping by 15%** [1].

    For a new industrial startup, these data points suggest that **water security and regulatory compliance** are the central challenges that will exert the most influence on long-term viability in this region.
    """
    
    print("\nStarting Organic Compiler Process (Perceive -> Encode)...")
    try:
        result = await svc.generate_strategic_model(umpire_data)
        
        print("\n" + "="*50)
        print("=== STAGE 1: PERCEPTION (Natural Language Model) ===")
        print("="*50)
        print(result["model_description"])
        
        print("\n" + "="*50)
        print("=== STAGE 2: ENCODING (JSON Payload) ===")
        print("="*50)
        print(result["json_payload"])
        print("\n" + "="*50)
        
    except Exception as e:
        print(f"Error during compilation: {e}")

if __name__ == "__main__":
    asyncio.run(main())
