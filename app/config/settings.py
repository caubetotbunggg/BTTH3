import logging
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
    "LIMIT": 5,
    "THRESHOLD": 0.7,
}

GEMINI_CLIENT = genai.Client()

RAG_CONFIG = {
    "MODEL_NAME": "gemini-2.5-flash"
}

# Logging config
LOGGING_CONFIG = {
    "level": logging.INFO,
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
}

def setup_logger(name: str, log_file: str) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(LOGGING_CONFIG["level"])
    logger.propagate = False

    if not logger.handlers:
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        formatter = logging.Formatter(LOGGING_CONFIG["format"])
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger