import logging
import os

import weaviate
from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer
from weaviate.classes.init import AdditionalConfig, Timeout
from weaviate.classes.query import MetadataQuery

from FlagEmbedding import FlagReranker

load_dotenv()


# Configure logging
logging.basicConfig(
    filename="../BTTH3/log/retrieve_info.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    encoding="utf-8",
)
logger = logging.getLogger(__name__)

router = APIRouter()

# Load embedding and reranking model
model = SentenceTransformer(os.getenv("EMBEDDING_MODEL"))
reranker = FlagReranker(os.getenv("RERANKING_MODEL"), use_fp16=False)

# Connect to Weaviate
client = weaviate.connect_to_local(
    host="localhost",
    port=8080,
    additional_config=AdditionalConfig(timeout=Timeout(query=60)),
)
# Get the created collection
collection = client.collections.get("Document")


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

    embedding = model.encode(f"query: {user_input}").tolist()

    try:
        # Query ChromaDB (top 5)
        results = collection.query.hybrid(
            query=user_input,
            vector=embedding,
            alpha=0.6,  # Weight for BM25
            return_metadata=MetadataQuery(score=True, explain_score=True),
            limit=10,
        )

        from operator import itemgetter

        batch_pairs = []
        metas = []
        texts = []

        for i, obj in enumerate(results.objects, start=1):
            doc = obj.properties["text"]
            meta = obj.properties["metadata"]

            batch_pairs.append([user_input, doc])
            texts.append(doc)
            metas.append(meta)

        # Use reranker to compute scores
        scores = reranker.compute_score(batch_pairs, normalize=True)

        # Select results with score >= 0.7
        scored_results = [
            (i, score, texts[i], metas[i], results.objects[i].metadata.explain_score)
            for i, score in enumerate(scores)
            if score >= 0.7
        ]

        # Sort results by score and limit to top k
        top_results = sorted(scored_results, key=itemgetter(1), reverse=True)[:k]

        # Prepare response
        response_chunks = []
        for i, score, doc, meta, explain_score in top_results:
            response_chunks.append(
                ChunkResponse(
                    chunk_id=str(i),
                    text=doc,
                    score=round(score, 4),
                    meta={
                        "law_id": meta.get("law_id", "unknown"),
                        "section_title": meta.get("title", "unknown"),
                        "date": meta.get("date", "unknown"),
                    },
                )
            )
            logger.info(
                f"Result {i}: score={score}, law_id={meta.get('law_id', 'unknown')}, "
                f"title={meta.get('title', 'unknown')}, "
                f"Explain Score: {explain_score}"
            )

        if not response_chunks:
            logger.warning("No results found for the query")
            raise HTTPException(status_code=204, detail="No results found")
        return {"chunks": response_chunks}

    except Exception as e:
        logger.exception("Vector search failed")
        raise HTTPException(status_code=500, detail=f"Vector search failed: {str(e)}")
