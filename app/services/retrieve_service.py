import logging
from operator import itemgetter

from fastapi.responses import Response
from weaviate.classes.query import MetadataQuery

from app.config.settings import (
    DOCUMENT_COLLECTION,
    EMBEDDING_MODEL,
    RERANKING_MODEL,
    SEARCH_CONFIG,
)
from app.constants.http import HTTP_STATUS
from app.models.retrieve_model import ChunkResponse

logger = logging.getLogger(__name__)


class RetrieveService:
    @staticmethod
    def retrieve(user_input: str, k: int):
        embedding = EMBEDDING_MODEL.encode(f"query: {user_input}").tolist()

        results = DOCUMENT_COLLECTION.query.hybrid(
            query=user_input,
            vector=embedding,
            alpha=SEARCH_CONFIG["ALPHA"],
            return_metadata=MetadataQuery(score=True, explain_score=True),
            limit=SEARCH_CONFIG["LIMIT"],
        )

        batch_pairs, texts, metas = [], [], []
        for obj in results.objects:
            doc = obj.properties["text"]
            meta = obj.properties["metadata"]
            batch_pairs.append([user_input, doc])
            texts.append(doc)
            metas.append(meta)

        scores = RERANKING_MODEL.compute_score(batch_pairs, normalize=True)

        scored_results = [
            (i, score, texts[i], metas[i], results.objects[i].metadata.explain_score)
            for i, score in enumerate(scores)
            if score >= SEARCH_CONFIG["THRESHOLD"]
        ]

        top_results = sorted(scored_results, key=itemgetter(1), reverse=True)[:k]

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
                f"law_id={meta.get('law_id')}, "
                f"explain={explain_score}"
            )

        if not response_chunks:
            return Response(
                status_code=HTTP_STATUS.NO_CONTENT, content="No results found"
            )

        return {"chunks": response_chunks}
