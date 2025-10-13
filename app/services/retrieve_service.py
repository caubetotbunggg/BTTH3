from gradio_client import Client
import time
from operator import itemgetter

from weaviate.classes.query import MetadataQuery
from weaviate.classes.query import Filter

from app.config.settings import (
    DOCUMENT_COLLECTION,
    SEARCH_CONFIG,
    setup_logger,
)
from app.models.retrieve_model import ChunkResponse, RetrieveResponse

logger = setup_logger("retrieve", "../BTTH3/log/retrieve_info.log")


class RetrieveService:
    @staticmethod
    def retrieve(user_input: str, k: int):
        logger.info(f"Starting retrieval for question='{user_input}' with top_k={k}")

        start_retrieve = time.perf_counter()

        start_embedding = time.perf_counter()

        # client = Client("caubetotbunggg/api")
        # embedding = client.predict(
        #         text=f"query: {user_input}",
        #         api_name="/embed_text"
        # )
        embedding_time = time.perf_counter() - start_embedding

        start_hybrid_query = time.perf_counter()

        # results = DOCUMENT_COLLECTION.query.hybrid(
        #     query=user_input,
        #     vector=embedding,
        #     alpha=SEARCH_CONFIG["ALPHA"],
        #     return_metadata=MetadataQuery(score=True, explain_score=True),
        #     limit=k,
        # )

        from elysia import configure
        import os
        from dotenv import load_dotenv
        load_dotenv()
        WEAVIATE_URL = os.getenv("WEAVIATE_URL")
        WEAVIATE_API_KEY = os.getenv("WEAVIATE_API_KEY")
        GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
        configure(
            base_model="gemini-2.0-flash-lite",
            base_provider="gemini",
            complex_model="gemini-2.0-flash",
            complex_provider="gemini",
            gemini_api_key=GEMINI_API_KEY,# replace with your API key
            wcd_url= WEAVIATE_URL, # replace with your WCD_URL
            wcd_api_key= WEAVIATE_API_KEY, # replace with your WCD_API_KEY
        )
        from elysia import Tree
        tree = Tree()
        response, objects = tree(user_input)   # ✅ tách tuple ra
        print(response)
        print(objects)
        # query_time = time.perf_counter() - start_hybrid_query

        # batch_pairs, texts, metas = [], [], []
        # for obj in objects:
        #     doc = obj.properties["text"]
        #     meta = obj.properties["metadata"]
        #     batch_pairs.append([user_input, doc])
        #     texts.append(doc)
        #     metas.append(meta)

        # start_rerank = time.perf_counter()
        # scores = [obj.metadata.score for obj in objects]
        # rerank_time = time.perf_counter() - start_rerank

        # scored_results = [
        #     (i, score, texts[i], metas[i], objects[i].metadata.explain_score)
        #     for i, score in enumerate(scores)
        #     if score >= SEARCH_CONFIG["THRESHOLD"]
        # ]

        # top_results = sorted(scored_results, key=itemgetter(1), reverse=True)[:k]
        # retrieve_time = time.perf_counter() - start_retrieve
        # print(
        #     f"retrieve_time={retrieve_time:.2f}, embedding_time={embedding_time:.2f}, "
        #     f"query_time={query_time:.2f}, rerank_time={rerank_time:.2f}"
        # )
        # logger.info(
        #         f"retrieve_time={retrieve_time:.2f}, embedding_time={embedding_time:.2f}, "
        #         f"query_time={query_time:.2f}, rerank_time={rerank_time:.2f}"
        # )
        
        response_chunks = []
        #for i, score, doc, meta, explain_score in top_results:
        for i, obj in enumerate(objects):
            doc = obj["text"]
            meta = obj["metadata"]
            response_chunks.append(
                ChunkResponse(
                    chunk_id=str(i),
                    text=doc,
                    meta=meta,
                )
            )
            #print(f"Result {i}: score={score}, law_id={meta}")
            #logger.info(f"Result {i}: score={score}, " f"law_id={meta}")
        if not response_chunks:
            return RetrieveResponse(chunks=[])

        return RetrieveResponse(chunks=response_chunks)
