from pydantic import BaseModel


class ChunkResponse(BaseModel):
    chunk_id: str
    text: str
    score: float
    meta: str


class RetrieveResponse(BaseModel):
    chunks: list[ChunkResponse] | None
