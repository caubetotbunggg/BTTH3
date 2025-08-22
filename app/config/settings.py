import os

import weaviate
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
from weaviate.classes.init import AdditionalConfig, Timeout
from google import genai
from FlagEmbedding import FlagReranker

load_dotenv()

# Model configs
EMBEDDING_MODEL = SentenceTransformer(os.getenv("EMBEDDING_MODEL"))
RERANKING_MODEL = FlagReranker(os.getenv("RERANKING_MODEL"), use_fp16=False)

# Database configs
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

GEMINI_CLIENT = genai.Client()

RAG_CONFIG = {
    "MODEL_NAME": "gemini-2.5-flash"
}

# Logging config
LOGGING_CONFIG = {
    "LEVEL": "INFO",
    "FORMAT": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    "ENCODING": "utf-8"
}