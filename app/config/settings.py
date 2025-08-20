import logging
import os

import weaviate
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
from weaviate.classes.init import AdditionalConfig, Timeout

from FlagEmbedding import FlagReranker

load_dotenv()

# Logging config
logging.basicConfig(
    filename="logs/retrieve_info.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    encoding="utf-8",
)
logger = logging.getLogger(__name__)

# Models
embedding_model = SentenceTransformer(os.getenv("EMBEDDING_MODEL"))
reranker_model = FlagReranker(os.getenv("RERANKING_MODEL"), use_fp16=False)

# Weaviate client
client = weaviate.connect_to_local(
    host=os.getenv("WEAVIATE_HOST", "localhost"),
    port=int(os.getenv("WEAVIATE_PORT", 8080)),
    additional_config=AdditionalConfig(timeout=Timeout(query=60)),
)
collection = client.collections.get("Document")
