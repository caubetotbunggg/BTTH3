import json
import chromadb

# Configuration
PERSIST_DIRECTORY = "chroma_db"
COLLECTION_NAME = "legal_chunks"
EMBEDDING_DIMENSION = 384
METRIC = "cosine"


# Initialize Chroma client
try:
    client = chromadb.PersistentClient(path=PERSIST_DIRECTORY)
except Exception as e:
    print(f"[ERROR] Failed to initialize Chroma client: {e}")
    exit(1)

# Create or check collection
try:
    existing_collections = [c.name for c in client.list_collections()]
    if COLLECTION_NAME in existing_collections:
        print(f"[!] Collection '{COLLECTION_NAME}' already exists.")
    else:
        client.get_or_create_collection(
            name=COLLECTION_NAME, metadata={"hnsw:space": METRIC}
        )
        print(f"[+] Created collection '{COLLECTION_NAME}'")
except Exception as e:
    print(f"[ERROR] Failed to create/check collection: {e}")
    exit(1)

# Save configuration
config = {
    "collection_name": COLLECTION_NAME,
    "embedding_dimension": EMBEDDING_DIMENSION,
    "metric": METRIC,
    "persist_directory": PERSIST_DIRECTORY,
}
try:
    with open("index_config.json", "w") as f:
        json.dump(config, f, indent=4)
        print("[+] Saved index_config.json")
except Exception as e:
    print(f"[ERROR] Failed to save config file: {e}")
    exit(1)
