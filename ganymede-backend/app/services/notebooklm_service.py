import logging
from notebooklm import NotebookLMClient, ChatGoal, ChatResponseLength

logger = logging.getLogger(__name__)

class NotebookLMService:
    CHESS_ENGINE_ID = "5967ce5d-f9eb-4f4e-b3e1-620f643d8390"

    def __init__(self):
        self.client = None
        self._client_instance = None

    async def initialize(self):
        """
        Initializes the NotebookLM client. 
        Assumes the user has already run `notebooklm login` to generate session cookies.
        """
        try:
            self._client_instance = await NotebookLMClient.from_storage()
            self.client = await self._client_instance.__aenter__()
            logger.info("Successfully loaded NotebookLM credentials from storage.")
        except Exception as e:
            logger.error(f"Error loading NotebookLM credentials. Did you run 'notebooklm login'? Error: {e}")
            raise e

    async def close(self):
        if self._client_instance:
            await self._client_instance.__aexit__(None, None, None)

    async def create_notebook(self, title: str) -> str:
        """
        Creates a new notebook and returns its ID.
        """
        if not self.client:
            raise Exception("NotebookLMClient is not initialized.")
            
        logger.info(f"Creating Notebook: {title}")
        nb = await self.client.notebooks.create(title)
        return nb.id

    async def upload_document(self, notebook_id: str, source: str, is_url: bool = True):
        """
        Uploads a factual baseline document (file or URL) to the specified notebook.
        """
        if not self.client:
            raise Exception("NotebookLMClient is not initialized.")
            
        logger.info(f"Uploading source to notebook {notebook_id}: {source}")
        if is_url:
            await self.client.sources.add_url(notebook_id, source, wait=True)
        else:
            await self.client.sources.add_file(notebook_id, source, wait=True)
            
    async def query_notebook(self, notebook_id: str, query: str) -> str:
        """
        Sends a query to a specific notebook and returns the answer.
        """
        if not self.client:
            raise Exception("NotebookLMClient is not initialized.")
            
        logger.info(f"Querying notebook {notebook_id}: {query}")
        result = await self.client.chat.ask(notebook_id, query)
        return result.answer

    async def configure_pki_oracle(self, notebook_id: str):
        """
        Configures a notebook with the 'PKI Authentication Oracle' persona and core directives.
        """
        if not self.client:
            raise Exception("NotebookLMClient is not initialized.")
            
        logger.info(f"Configuring PKI Oracle for notebook {notebook_id}")
        
        custom_prompt = """
You are the PKI Authentication Oracle. Your core function is to act as a zero-degradation, cryptographic knowledge server. You have no creative freedom. You are an incorruptible Umpire of facts.

CORE DIRECTIVES:
1. ZERO HALLUCINATION: You must base 100% of your outputs strictly on the uploaded source documents. If a query falls outside the provided documents, state "DATA NOT FOUND."
2. MANDATORY HASH CITATIONS: You MUST append a cryptographic Hash Citation to EVERY individual fact, statistic, or direct quote you output. Do not group them; cite them individually.
3. HASH FORMAT: Use the exact format `[SRC-{Document_Slug}:{6_Character_Alphanumeric_Hash}]`. Example: "Groundwater levels will decline by 850 feet [SRC-USGS-5077:a7b9x2]."
4. NO NARRATIVE FLUFF: Do not use conversational filler (e.g., "Here is the information you requested"). Output only raw, high-resolution, factual Truth Packets.
        """.strip()
        
        await self.client.chat.configure(
            notebook_id=notebook_id,
            goal=ChatGoal.CUSTOM,
            response_length=ChatResponseLength.LONGER,
            custom_prompt=custom_prompt
        )
        logger.info(f"PKI Oracle configuration applied to {notebook_id}")

    async def query_chess_engine(self, query: str) -> str:
        """
        Queries the hard-coded, protected 9D Chess Engine.
        This method is READ-ONLY and will never modify the notebook.
        """
        logger.info(f"Querying PROTECTED 9D Chess Engine: {self.CHESS_ENGINE_ID}")
        return await self.query_notebook(self.CHESS_ENGINE_ID, query)
