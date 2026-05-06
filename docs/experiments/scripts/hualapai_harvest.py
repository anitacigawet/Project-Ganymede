import asyncio
import os
from app.services.notebooklm_service import NotebookLMService

async def main():
    svc = NotebookLMService()
    try:
        await svc.initialize()
        # Use the notebook we created or a new one. Let's use the ID from the previous successful run if possible, 
        # but for simplicity in this script, I'll create a fresh one to be sure.
        nb_id = await svc.create_notebook("Hualapai_Visualization_Strategy")
        
        file_path = "baseline.txt"
        with open(file_path, "w") as f:
            f.write("Hualapai Valley Basin: Groundwater depletion 2.4ft/year. Legislation HB-2041 restricts pumping by 15%. Industrial permit for semiconductor plant requires 400k gal/day. Protests from farmers.")
        
        await svc.upload_document(nb_id, file_path, is_url=False)
        await asyncio.sleep(20)
        
        # New Query: Factual Analysis + Visualization Strategy
        query = """
        1. Perform a 9D Strategic Analysis on the Hualapai water crisis. 
        2. Based on this analysis, what is the best way to visualize this scenario in a 3D topological simulation? 
           Describe the 'Gravity Well' (SDS), the tension between nodes, and how the grid should warp to accurately represent the point of system failure.
        """
        
        print("Querying Umpire for Analysis and Visualization Strategy...")
        response = await svc.query_notebook(nb_id, query)
        
        print("\n=== COMPOSITE TRUTH PACKET ===\n" + response + "\n==============================\n")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if os.path.exists("baseline.txt"): os.remove("baseline.txt")
        await svc.close()

if __name__ == "__main__":
    asyncio.run(main())
