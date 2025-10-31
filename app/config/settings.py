import logging
import os
import sys

from groq import Groq
import weaviate
from dotenv import load_dotenv
from weaviate.classes.init import Auth, AdditionalConfig, Timeout

load_dotenv()

# Weaviate client setup
# --- Validate required environment variables ---
REQUIRED_ENV_VARS = [
    "WEAVIATE_URL",
    "WEAVIATE_API_KEY",
    "GEMINI_API_KEY",
]

missing_vars = [var for var in REQUIRED_ENV_VARS if not os.getenv(var)]
if missing_vars:
    missing = ", ".join(missing_vars)
    print(f"❌ Missing required environment variables: {missing}")
    sys.exit(1)

# --- Load environment variables ---
WEAVIATE_URL = os.getenv("WEAVIATE_URL")
WEAVIATE_API_KEY = os.getenv("WEAVIATE_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# --- Weaviate client setup ---
try:
    WEAVIATE_CLIENT = weaviate.connect_to_weaviate_cloud(
        cluster_url=WEAVIATE_URL,
        auth_credentials=Auth.api_key(WEAVIATE_API_KEY),
        additional_config=AdditionalConfig(timeout=Timeout(query=60)),
    )
    DOCUMENT_COLLECTION = WEAVIATE_CLIENT.collections.get("Document")

except Exception as e:
    print(f"❌ Failed to connect to Weaviate: {e}")
    sys.exit(1)

# LLM configs
LLM_MODEL = "openai/gpt-oss-120b"

# Tree configs
WEAVIATE_URL = os.getenv("WEAVIATE_URL")
WEAVIATE_API_KEY = os.getenv("WEAVIATE_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
BASE_MODEL = "gemini-2.5-flash-lite"
COMPLEX_MODEL = "gemini-2.5-flash"

# Search configs
SEARCH_CONFIG = {
    "ALPHA": 0.6,
    "LIMIT": 5,
    "THRESHOLD": 0.5,
}

# Groq configs
GROQ_CLIENT = Groq(
    api_key=os.getenv("GROQ_API_KEY")
)
GROQ_CLIENT_B = Groq(
    api_key=os.getenv("GROQ_API_KEY_B")
)

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