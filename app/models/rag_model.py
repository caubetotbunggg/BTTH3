from pydantic import BaseModel

from app.models.retrieve_model import RetrieveResponse

class RAGRequest(BaseModel):
    user_input: str
    k: int = 5

from pydantic import BaseModel
from typing import List, Dict, Any

class ChunkMeta(BaseModel):
    metadata: str

class Chunk(BaseModel):
    chunk_id: str
    text: str
    meta: ChunkMeta

class RAGResponse(BaseModel):
    answer: str
    chunks: Dict[str, List[Chunk]]

