from pydantic import BaseModel
from typing import List, Dict

class RAGRequest(BaseModel):
    user_input: str
    k: int = 5

class RAGResponse(BaseModel):
    answer: str
    used_chunks: List[Dict]
