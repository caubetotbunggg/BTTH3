import os

import weaviate
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
from weaviate.classes.init import AdditionalConfig, Timeout

from FlagEmbedding import FlagReranker

load_dotenv()

EMBEDDING_MODEL = SentenceTransformer(os.getenv("EMBEDDING_MODEL"))
RERANKING_MODEL = FlagReranker(os.getenv("RERANKING_MODEL"), use_fp16=False)

WEAVIATE_CLIENT = weaviate.connect_to_local(
    host="localhost",
    port=8080,
    additional_config=AdditionalConfig(timeout=Timeout(query=60)),
)

DOCUMENT_COLLECTION = WEAVIATE_CLIENT.collections.get("Document")

# Search configs
SEARCH_CONFIG = {
    "ALPHA": 0.6,
    "LIMIT": 10,
    "THRESHOLD": 0.7,
}
