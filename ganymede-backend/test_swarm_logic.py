import asyncio
import os
import tempfile
from app.services.notebooklm_service import NotebookLMService

async def main():
    print("Initializing NotebookLM Service...")
    svc = NotebookLMService()
    await svc.initialize()
    
    print("\nCreating Test Notebook: 'Ganymede_Alpha_Test'...")
    nb_id = await svc.create_notebook("Ganymede_Alpha_Test")
    print(f"Notebook created with ID: {nb_id}")
    
    print("\nInjecting Factual Baseline...")
    scenario_data = "Scenario Data: The Hualapai Valley Basin currently has a groundwater depletion rate of 2.4 feet per year. Local legislation is pending to restrict industrial pumping by 15%."
    
    # Write the raw string to a temporary text file so the service can upload it
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
        f.write(scenario_data)
        temp_path = f.name
        
    try:
        await svc.upload_document(nb_id, temp_path, is_url=False)
        print("Factual Baseline Injected. Waiting for indexing...")
        await asyncio.sleep(10)
        
        print("\nQuerying the Umpire...")
        query = "Based on the provided data, identify the primary 'Gravity Well' (SDS) for a new industrial startup in this region."
        response = await svc.query_notebook(nb_id, query)
        
        print("\n=== Umpire Response ===")
        print(response)
        print("=======================\n")
    except Exception as e:
        print(f"\n[ERROR] An error occurred during the test: {e}")
    finally:
        # Clean up the temporary file
        if os.path.exists(temp_path):
            os.remove(temp_path)
        await svc.close()

if __name__ == "__main__":
    asyncio.run(main())
