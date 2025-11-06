from pydantic import BaseModel
from typing import Optional

class RAGRequest(BaseModel):
    user_input: str
    k: int = 5

class ChunkMeta(BaseModel):
    metadata: str

class Chunk(BaseModel):
    chunk_id: str
    text: str
    meta: ChunkMeta

class RAGResponse(BaseModel):
    answer: str
    reasoning: Optional[str] = None

