import json
import os

import chromadb
import numpy as np
from chromadb.config import Settings

# ==== Load config ====
with open("index_config.json") as f:
    config = json.load(f)

# Tạo thư mục nếu chưa có
os.makedirs(config["persist_directory"], exist_ok=True)

# Khởi tạo client với cách mới
client = chromadb.PersistentClient(path=config["persist_directory"])

collection = client.get_or_create_collection(config["collection_name"])

# ==== Đường dẫn dữ liệu ====
embedding_dir = "data/processed/embeddings"
meta_dir = "data/raw/html"
chunk_data_dir = "data/processed/chunks"

files = [f for f in os.listdir(embedding_dir) if f.endswith(".npy")]
total_chunks = 0

for file in files:
    file_id = file.replace(".npy", "")
    embedding_path = os.path.join(embedding_dir, file)
    meta_path = os.path.join(meta_dir, f"{file_id}_meta.json")
    chunk_path = os.path.join(chunk_data_dir, f"{file_id}_chunks.json")

    # Kiểm tra metadata có tồn tại không
    if not os.path.exists(meta_path):
        print(f"[!] Bỏ qua {file_id}: thiếu metadata")
        continue

    # Load vectors và metadata
    vectors_np = np.load(embedding_path)
    if len(vectors_np.shape) == 1:
        vectors = [vectors_np.tolist()]
    else:
        vectors = vectors_np.tolist()

    with open(meta_path, "r", encoding="utf-8") as f:
        metadata = json.load(f)

    # Tạo các trường cần thiết
    chunk_ids = [f"{file_id}_{i}" for i in range(len(vectors))]
    if not os.path.exists(chunk_path):
        print(f"[!] Bỏ qua {file_id}: thiếu chunk data")
        continue
    else:
        with open(chunk_path, "r", encoding="utf-8") as f:
            chunk_data = json.load(f)

    if len(chunk_data) != len(vectors):
        print(f"[!] Bỏ qua {file_id}: số lượng chunk không khớp với vectors")
        print(f"  - Vectors: {len(vectors)}, Chunks: {len(chunk_data)}")
        continue
    documents = [
        f"Tiêu đề: {item['tieu_de']} - Nội dung: {item['noi_dung']} - Khoản: {item['khoan']}"
        for item in chunk_data
    ]
    metadatas = [metadata] * len(
        vectors
    )  # Giả sử metadata giống nhau cho tất cả chunks

    # Thêm vào Chroma
    collection.upsert(
        ids=chunk_ids, embeddings=vectors, documents=documents, metadatas=metadatas
    )

    print(f"[✓] Đã index {len(chunk_ids)} chunks từ {file_id}")
    total_chunks += len(chunk_ids)

print(f"\n Tổng cộng đã index: {total_chunks} chunks.")
