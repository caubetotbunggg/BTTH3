import os

import weaviate
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
from weaviate.classes.init import AdditionalConfig, Timeout
from weaviate.classes.query import MetadataQuery

load_dotenv()  # Tự động đọc file .env ở cùng thư mục

# =================== 1. Kết nối tới Weaviate ====================
client = weaviate.connect_to_local(
    host="localhost",
    port=8080,
    additional_config=AdditionalConfig(timeout=Timeout(query=60)),
)

# =================== 2. Load model để encode ====================
model = SentenceTransformer(os.getenv("EMBEDDING_MODEL"))

# =================== 3. Nhập truy vấn người dùng ====================
query = "Tội không cứu giúp người đang ở trong tình trạng nguy hiểm đến tính mạng"
# Encode đảm bảo đầu ra là list of floats
vector = model.encode(query, normalize_embeddings=True)
vector = vector.tolist() if hasattr(vector, "tolist") else list(vector)

# =================== 4. Lấy collection đã tạo ====================
collection = client.collections.get("Document")

# =================== 5. Truy vấn Dense + Hybrid ====================
try:
    # DENSE ONLY
    res_dense = collection.query.near_vector(
        near_vector=vector,  # your query vector goes here
        limit=3,
        return_metadata=MetadataQuery(distance=True),
    )

    # HYBRID (BM25 + VECTOR)
    res_hybrid = collection.query.hybrid(
        query=query, vector=vector, alpha=0.6, limit=3  # Trọng số cho BM25
    )

    # ======= Kết quả Dense ========
    print("🔍 [Dense Only Results]")
    for i, obj in enumerate(res_dense.objects, start=1):
        print(f"{i}. {obj.properties['text'][:200].strip()}...")
        print(f"Distance: {obj.metadata.distance:.4f}")
        print(
            f"Luật: {obj.properties['metadata'].get('law_id', 'unknown')}, Title: {obj.properties['metadata'].get('title', 'unknown')}"
        )

    # ======= Kết quả Hybrid ========
    print("🔀 [Hybrid Results (alpha=0.6)]")
    for i, obj in enumerate(res_hybrid.objects, start=1):
        print(f"{i}. {obj.properties['text'][:200].strip()}...")


except Exception as e:
    print(f"[!] Truy vấn lỗi: {e}")

# =================== 6. Đóng kết nối ====================
client.close()
