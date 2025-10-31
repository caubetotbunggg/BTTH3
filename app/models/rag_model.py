from pydantic import BaseModel

from app.models.retrieve_model import RetrieveResponse

class RAGRequest(BaseModel):
    user_input: str
    k: int = 5

class RAGResponse(BaseModel):
    answer: str
    chunks: RetrieveResponse
