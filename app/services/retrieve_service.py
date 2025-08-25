import logging
from operator import itemgetter
import time

from fastapi.responses import Response
from weaviate.classes.query import MetadataQuery

from app.config.settings import (
    DOCUMENT_COLLECTION,
    EMBEDDING_MODEL,
    setup_logger,
    RERANKING_MODEL,
    SEARCH_CONFIG,
)
from app.constants.http import HTTP_STATUS
from app.models.retrieve_model import ChunkResponse

logger = setup_logger("retrieve", "../BTTH3/log/retrieve_info.log")


class RetrieveService:
    @staticmethod
    def retrieve(user_input: str, k: int):
        logger.info(f"Starting retrieval for question='{user_input}' with top_k={k}")
        
        start_retrieve = time.perf_counter()
        
        start_embedding = time.perf_counter()
        embedding = EMBEDDING_MODEL.encode(f"query: {user_input}").tolist()
        embedding_time = time.perf_counter() - start_embedding

        start_hybrid_query = time.perf_counter()
        results = DOCUMENT_COLLECTION.query.hybrid(
            query=user_input,
            vector=embedding,
            alpha=SEARCH_CONFIG["ALPHA"],
            return_metadata=MetadataQuery(score=True, explain_score=True),
            limit=k,    #SEARCH_CONFIG["LIMIT"],
        )
        query_time = time.perf_counter() - start_hybrid_query

        batch_pairs, texts, metas = [], [], []
        for obj in results.objects:
            doc = obj.properties["text"]
            meta = obj.properties["metadata"]
            batch_pairs.append([user_input, doc])
            texts.append(doc)
            metas.append(meta)

        start_rerank = time.perf_counter()
        #scores = RERANKING_MODEL.compute_score(batch_pairs, normalize=True)
        scores = [obj.metadata.score for obj in results.objects]
        rerank_time = time.perf_counter() - start_rerank

        scored_results = [
            (i, score, texts[i], metas[i], results.objects[i].metadata.explain_score)
            for i, score in enumerate(scores)
            if score >= SEARCH_CONFIG["THRESHOLD"]
        ]

        top_results = sorted(scored_results, key=itemgetter(1), reverse=True)[:k]
        retrieve_time = time.perf_counter() - start_retrieve
        
        logger.info(
            f"retrieve_time={retrieve_time:.2f}, embedding_time={embedding_time:.2f}, "
            f"query_time={query_time:.2f}, rerank_time={rerank_time:.2f}"
        )
        
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
                f"Result {i}: score={score}, "
                f"law_id={meta.get('law_id')}."
            )
        if not response_chunks:
            return {"chunks": []}

        return {"chunks": response_chunks}
