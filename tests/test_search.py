import os
import random

import numpy as np
import weaviate
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
from weaviate.classes.init import AdditionalConfig, Timeout
from weaviate.classes.query import MetadataQuery

# =================== 0. Cấu hình ====================
load_dotenv()

EMBED_DIR = "../BTTH3/data/processed/embeddings"
OUTPUT_MD = "../BTTH3/docs/search_results.md"
TOP_K = 5
NUM_SAMPLES = 10
MODEL_NAME = os.getenv("EMBEDDING_MODEL")

# =================== 1. Kết nối tới Weaviate ====================
client = weaviate.connect_to_local(
    host="localhost",
    port=8080,
    additional_config=AdditionalConfig(timeout=Timeout(query=60)),
)

collection = client.collections.get("Document")

# =================== 2. Load model embed ====================
model = SentenceTransformer(MODEL_NAME)


# =================== 3. Hàm chọn sample vector ====================
def load_random_embeddings(n=NUM_SAMPLES):
    files = [f for f in os.listdir(EMBED_DIR) if f.endswith(".npy")]
    samples = []

    for file in random.sample(files, min(n, len(files))):
        vecs = np.load(os.path.join(EMBED_DIR, file))
        vec = vecs[random.randint(0, len(vecs) - 1)]
        chunk_id = f"{file.replace('.npy', '')}_{random.randint(0, 999)}"
        samples.append((chunk_id, vec.tolist()))
    return samples


# =================== 4. Hàm truy vấn và ghi kết quả ====================
def query_and_report(collection, samples, k=TOP_K):
    os.makedirs(os.path.dirname(OUTPUT_MD), exist_ok=True)
    with open(OUTPUT_MD, "w", encoding="utf-8") as f:
        f.write(f"# Kết quả tìm kiếm mẫu (Top {k})\n\n")

        for i, (chunk_id, vec) in enumerate(samples, 1):
            f.write(f"## {i}. Query ID: `{chunk_id}`\n")

            # Truy vấn near_vector
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

    print(f"✅ Đã lưu kết quả tại: {OUTPUT_MD}")


# =================== 5. Chạy chương trình ====================
def main():
    samples = load_random_embeddings()
    query_and_report(collection, samples)
    client.close()


if __name__ == "__main__":
    main()
