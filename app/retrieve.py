from fastapi import APIRouter, FastAPI, Query
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer
import chromadb

router = APIRouter()

# Load embedding model
model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

# Initialize ChromaDB client and collection
client = chromadb.PersistentClient(path="chroma_db")
collection = client.get_or_create_collection("legal_chunks")


# Response schema
class ChunkResponse(BaseModel):
    chunk_id: str
    text: str
    score: float
    meta: dict

class SearchResponse(BaseModel):
    chunks: list[ChunkResponse]

@router.post("/search", response_model=SearchResponse)
def search(user_input: str = Query(..., description="Câu hỏi hoặc truy vấn người dùng")):
    # Embed truy vấn
    embedding = model.encode(user_input).tolist()

    # Truy vấn ChromaDB (top 5)
    results = collection.query(
        query_embeddings=[embedding],
        n_results=5,
        include=["documents", "distances", "metadatas"]
    )

    response_chunks = []
    documents = results["documents"][0]
    distances = results["distances"][0]
    metadatas = results["metadatas"][0]

    for i, (doc, score, meta) in enumerate(zip(documents, distances, metadatas)):
        response_chunks.append({
            "chunk_id": str(i),
            "text": doc,
            "score": round(score, 4),
            "meta": {
                "law_id": meta.get("law_id", "unknown"),
                "section_title": meta.get("title", "unknown"),
                "date": meta.get("date", "unknown")
            }
        })

    return {"chunks": response_chunks}