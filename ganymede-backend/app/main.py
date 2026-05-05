from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from app.services.notebooklm_service import NotebookLMService
import logging

app = FastAPI(title="Project Ganymede Backend")
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

notebooklm_svc = NotebookLMService()

class OrchestrateRequest(BaseModel):
    query: str
    notebook_id: str
    
class OrchestrateResponse(BaseModel):
    status: str
    structured_prompt: str

@app.on_event("startup")
async def startup_event():
    # Initialize the NotebookLM client from local storage / auth
    try:
        await notebooklm_svc.initialize()
        logger.info("NotebookLM client initialized successfully.")
    except Exception as e:
        logger.error(f"Failed to initialize NotebookLM client: {e}")

@app.on_event("shutdown")
async def shutdown_event():
    await notebooklm_svc.close()

@app.post("/api/orchestrate", response_model=OrchestrateResponse)
async def orchestrate(req: OrchestrateRequest):
    """
    Agent-Driven Workflow Pivot:
    1. Query the NotebookLM Umpire.
    2. Retrieve the 9D analysis.
    3. Format that analysis into a Structured Prompt Block.
    """
    try:
        # 1. Query NotebookLM Umpire for Analysis + Visualization Strategy
        query = """
        1. Perform a 9D Strategic Analysis on this scenario.
        2. Based on this analysis, what is the best way to visualize this scenario in a 3D topological simulation? 
           Describe the 'Gravity Well' (SDS), the tension between nodes, and how the grid should warp to accurately represent the point of system failure.
        """
        composite_analysis = await notebooklm_svc.query_notebook(req.notebook_id, query)
        
        # 2 & 3. Format the analysis into a Master Workflow Prompt for the Gemini Compiler
        structured_prompt = f"""
# SYSTEM DIRECTIVE
You are the Ganymede Compiler. Your task is to visualize and model the strategic landscape based on the following factual 9D analysis and the suggested visualization parameters from the Umpire.

# UMPIRE COMPOSITE DATA (Analysis & Strategy)
{composite_analysis.strip()}

# OUTPUT INSTRUCTION
Based on the specific strategy above, provide the final simulation parameters in our standardized JSON format for the Ganymede frontend:
```json
{{
  "stress": <number 0-100>,
  "blindness": <number 0-100>,
  "description": "<detailed summary of how the topology is warping based on the Umpire's strategy>"
}}
```
"""
        return OrchestrateResponse(
            status="success",
            structured_prompt=structured_prompt.strip()
        )
    except Exception as e:
        logger.error(f"Failed during NotebookLM query: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/health")
async def health_check():
    return {"status": "healthy"}
