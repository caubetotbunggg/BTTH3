import os
import random

import numpy as np
import weaviate
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
from weaviate.classes.init import AdditionalConfig, Timeout
from weaviate.classes.query import MetadataQuery

# =================== 0. Configuration ====================
load_dotenv()

EMBED_DIR = "../BTTH3/data/processed/embeddings"
OUTPUT_MD = "../BTTH3/docs/search_results.md"
TOP_K = 5
NUM_SAMPLES = 10
MODEL_NAME = os.getenv("EMBEDDING_MODEL")

# =================== 1. Connect to Weaviate ====================
client = weaviate.connect_to_local(
    host="localhost",
    port=8080,
    additional_config=AdditionalConfig(timeout=Timeout(query=60)),
)

collection = client.collections.get("Document")

# =================== 2. Load model embed ====================
model = SentenceTransformer(MODEL_NAME)


# =================== 3. Load sample vector ====================
def load_random_embeddings(n=NUM_SAMPLES):
    files = [f for f in os.listdir(EMBED_DIR) if f.endswith(".npy")]
    samples = []

    for file in random.sample(files, min(n, len(files))):
        vecs = np.load(os.path.join(EMBED_DIR, file))
        vec = vecs[random.randint(0, len(vecs) - 1)]
        chunk_id = f"{file.replace('.npy', '')}_{random.randint(0, 999)}"
        samples.append((chunk_id, vec.tolist()))
    return samples


# =================== 4. Query and report results ====================
def query_and_report(collection, samples, k=TOP_K):
    os.makedirs(os.path.dirname(OUTPUT_MD), exist_ok=True)
    with open(OUTPUT_MD, "w", encoding="utf-8") as f:
        f.write(f"# Search Results (Top {k})\n\n")

        for i, (chunk_id, vec) in enumerate(samples, 1):
            f.write(f"## {i}. Query ID: `{chunk_id}`\n")

            res = collection.query.near_vector(
                near_vector=vec, limit=k, 
                return_metadata=MetadataQuery(distance=True)
            )

            for rank, obj in enumerate(res.objects, 1):
                meta = obj.properties or {}
                distance = obj.metadata.distance
                sim = 1 - distance
                law = meta["metadata"].get("law_id", "unknown")
                title = meta["metadata"].get("title", "unknown")
                f.write(f"- **{rank}. Luật:** {law}, *{title}*, Sim: `{sim:.4f}`\n")
            f.write("\n---\n\n")

    print(f"✅ Search results saved to: {OUTPUT_MD}")


# =================== 5. Run the program ====================
def main():
    samples = load_random_embeddings()
    query_and_report(collection, samples)
    client.close()


if __name__ == "__main__":
    main()
