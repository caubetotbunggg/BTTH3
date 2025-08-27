from operator import itemgetter
import time
from weaviate.classes.query import MetadataQuery

from app.config.settings import (
    DOCUMENT_COLLECTION,
    EMBEDDING_MODEL,
    setup_logger,
    RERANKING_MODEL,
    SEARCH_CONFIG,
)
from app.models.retrieve_model import ChunkResponse, RetrieveRequest, RetrieveResponse

logger = setup_logger("retrieve", "../BTTH3/log/retrieve_info.log")


class RetrieveService:
    @staticmethod
    def retrieve(request: RetrieveRequest) -> RetrieveResponse:
        logger.info(
            f"Starting retrieval for question='{request.user_input}' with top_k={request.k}"
        )

        start_retrieve = time.perf_counter()

        # --- Step 1: Embedding ---
        start_embedding = time.perf_counter()
        embedding = EMBEDDING_MODEL.encode(f"query: {request.user_input}").tolist()
        embedding_time = time.perf_counter() - start_embedding

        # --- Step 2: Query ---
        start_hybrid_query = time.perf_counter()
        results = DOCUMENT_COLLECTION.query.hybrid(
            query=request.user_input,
            vector=embedding,
            alpha=SEARCH_CONFIG["ALPHA"],
            return_metadata=MetadataQuery(score=True, explain_score=True),
            limit=request.k,
        )
        query_time = time.perf_counter() - start_hybrid_query

        # --- Step 3: Collect docs ---
        batch_pairs, texts, metas = [], [], []
        for obj in results.objects:
            doc = obj.properties["text"]
            meta = obj.properties["metadata"]
            batch_pairs.append([request.user_input, doc])
            texts.append(doc)
            metas.append(meta)

        # --- Step 4: Rerank (nếu cần) ---
        start_rerank = time.perf_counter()
        scores = [obj.metadata.score for obj in results.objects]
        rerank_time = time.perf_counter() - start_rerank

        scored_results = [
            (i, score, texts[i], metas[i], results.objects[i].metadata.explain_score)
            for i, score in enumerate(scores)
            if score >= SEARCH_CONFIG["THRESHOLD"]
        ]

        top_results = sorted(scored_results, key=itemgetter(1), reverse=True)[: request.k]
        retrieve_time = time.perf_counter() - start_retrieve

        logger.info(
            f"retrieve_time={retrieve_time:.2f}, embedding_time={embedding_time:.2f}, "
            f"query_time={query_time:.2f}, rerank_time={rerank_time:.2f}"
        )

        # --- Step 5: Convert to BaseModel ---
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
            logger.info(f"Result {i}: score={score}, law_id={meta.get('law_id')}.")

        return RetrieveResponse(chunks=response_chunks)
