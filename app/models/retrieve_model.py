from pydantic import BaseModel

class RetrieveRequest(BaseModel):
    user_input: str
    k: int = 5

class ChunkResponse(BaseModel):
    chunk_id: str
    text: str
    score: float
    meta: dict


class RetrieveResponse(BaseModel):
    chunks: list[ChunkResponse]
