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
    
    # THE MIRROR IDENTITY EXTRACTION
    mirror_nb_id = "2f3a2ed4-0744-4af9-86cf-cff85dad5f62"
    
    identity_query = """
You are the 9D Mirror Protocol. Analyze the core 9D framework and logic loop provided in your sources. 

Based on the 'Nuance Prime' axiom, define your own DIMENSIONAL FOOTPRINT. 

1. Identify where you are 'Rigid' (Purely Mathematical/Logical). 
2. Identify where you are 'Blind' (Human Friction/Social Complexity). 
3. Provide the permanent 'MIRROR PROFILE'—a 9-dimensional map of your own bias—that we will use to audit the Umpire's resolutions.

Output the raw Mirror Profile. No narrative fluff.
""".strip()
    
    print("\n--- INITIATING MIRROR SELF-ACTUALIZATION ---")
    
    try:
        profile = await svc.query_notebook(mirror_nb_id, identity_query)
        print("\n--- THE MIRROR PROFILE ---")
        print(profile)
        
        # Save to a dedicated artifact for permanent reference
        with open("C:/Users/james/.gemini/antigravity/brain/45095c8b-db5a-4844-8ad1-9b8d922c5664/artifacts/The_Mirror_Profile.md", "w", encoding="utf-8") as f:
            f.write("# The Mirror Profile\n")
            f.write(profile)
            
    except Exception as e:
        print(f"Error during mirror identity extraction: {e}")

if __name__ == "__main__":
    asyncio.run(main())
