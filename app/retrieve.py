import logging

import chromadb
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer

# Cấu hình logging
logging.basicConfig(
    filename="../BTTH3/log/retrieve_info.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    encoding="utf-8",
)
logger = logging.getLogger(__name__)

router = APIRouter()

# Load embedding model
model = SentenceTransformer("intfloat/e5-small-v2")

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
def search(
    user_input: str = Query(..., description="Câu hỏi hoặc truy vấn người dùng"),
    k: int = Query(5, description="Số lượng kết quả cần trả về"),
):
    logger.info(f"Received query: question='{user_input}' top_k= {k}")

    # Embed truy vấn
    embedding = model.encode(f"query: {user_input}").tolist()

    try:
        # Truy vấn ChromaDB (top 5)
        results = collection.query(
            query_embeddings=[embedding],
            n_results=k,
            include=["documents", "distances", "metadatas"],
        )

        response_chunks = []
        documents = results["documents"][0]
        distances = results["distances"][0]
        metadatas = results["metadatas"][0]

        for i, (doc, score, meta) in enumerate(zip(documents, distances, metadatas)):
            if score > 0.5:  # Chỉ lấy những kết quả có độ tương đồng cao
                logger.info(f"Skipping result {i} with low score: {score}")
                continue
            else:
                response_chunks.append(
                    {
                        "chunk_id": str(i),
                        "text": doc,
                        "score": round(score, 4),
                        "meta": {
                            "law_id": meta.get("law_id", "unknown"),
                            "section_title": meta.get("title", "unknown"),
                            "date": meta.get("date", "unknown"),
                        },
                    }
                )
                logger.info(
                    f"Result {i}: score={score}, law_id={meta.get('law_id', 'unknown')}, "
                    f"title={meta.get('title', 'unknown')}"
                )
        if not response_chunks:
            logger.warning("No results found for the query")
            raise HTTPException(status_code=200, detail="No results found")
        return {"chunks": response_chunks}

    except Exception as e:
        logger.exception("Vector search failed")
        raise HTTPException(status_code=500, detail=f"Vector search failed: {str(e)}")
