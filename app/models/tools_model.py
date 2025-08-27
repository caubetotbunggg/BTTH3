from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Union

# Retrieve models
class ChunkResponse(BaseModel):
    chunk_id: str
    text: str
    score: float
    meta: dict

class RetrieveResponse(BaseModel):
    chunks: List[ChunkResponse]

class RetrieveRequest(BaseModel):
    user_input: str
    k: int = 5

# RAG request model
class RAG_Request_tool(BaseModel):
    user_input: str
    chunks: Optional[RetrieveResponse] = None

class RAG_Response_tool(BaseModel):
    answer: str
    chunks: Optional[RetrieveResponse] = None

# Format response model
class Format_Response_tool(BaseModel):
    formatted_answer: str

class Format_Request_tool(BaseModel):
    user_input: str
    context: Optional[RetrieveResponse] = None