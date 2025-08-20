from operator import itemgetter

from weaviate.classes.query import MetadataQuery

from app.config.settings import collection, embedding_model, logger, reranker_model
from app.models.retrieve_models import ChunkResponse


def retrieve_chunks(user_input: str, k: int = 5) -> list[ChunkResponse]:
    embedding = embedding_model.encode(f"query: {user_input}").tolist()

    results = collection.query.hybrid(
        query=user_input,
        vector=embedding,
        alpha=0.6,
        return_metadata=MetadataQuery(score=True, explain_score=True),
        limit=10,
    )

    batch_pairs, texts, metas = [], [], []
    for obj in results.objects:
        doc = obj.properties["text"]
        meta = obj.properties["metadata"]
        batch_pairs.append([user_input, doc])
        texts.append(doc)
        metas.append(meta)

    # rerank
    scores = reranker_model.compute_score(batch_pairs, normalize=True)

    # filter + sort
    scored_results = [
        (i, score, texts[i], metas[i], results.objects[i].metadata.explain_score)
        for i, score in enumerate(scores)
        if score >= 0.7
    ]
    top_results = sorted(scored_results, key=itemgetter(1), reverse=True)[:k]

    # build response
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
            f"Result {i}: score={score}, law_id={meta.get('law_id')}, "
            f"title={meta.get('title')}, Explain Score: {explain_score}"
        )
    return response_chunks
