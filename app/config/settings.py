import logging
import os

import weaviate
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
from weaviate.classes.init import AdditionalConfig, Timeout
from google import genai

load_dotenv()

# Model configs
EMBEDDING_MODEL = SentenceTransformer(os.getenv("EMBEDDING_MODEL"))

# Database configs
WEAVIATE_HOST = os.getenv("WEAVIATE_HOST", "weaviate")
WEAVIATE_PORT = int(os.getenv("WEAVIATE_PORT", 8080))

WEAVIATE_CLIENT = weaviate.connect_to_local(
    host=WEAVIATE_HOST,
    port=WEAVIATE_PORT,
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
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    logger = logging.getLogger(name)
    logger.setLevel(LOGGING_CONFIG["level"])
    logger.propagate = False

    if not logger.handlers:
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        formatter = logging.Formatter(LOGGING_CONFIG["format"])
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger