# CONNECT - Fixed connection method for newer Weaviate version
import json
import os

import numpy as np
import weaviate
import weaviate.classes.config as wvcc
from weaviate.classes.config import DataType, Property
from weaviate.classes.init import AdditionalConfig, Timeout
from weaviate.util import generate_uuid5

# =================== 1. Kết nối tới Weaviate ====================
client = weaviate.connect_to_local(
    host="localhost",
    port=8080,
    additional_config=AdditionalConfig(
        timeout=Timeout(
            query=60, insert=60
        )  # Use Timeout object with query and insert timeouts
    ),
)

# =================== 2. Kiểm tra và tạo collection ====================
client.collections.delete("Document")  # Xóa collection nếu đã tồn tại
# CREATE COLLECTION
try:
    client.collections.create(
        name="Document",
        vector_config=wvcc.VectorConfig.self_provided(),
        properties=[
            Property(name="text", data_type=DataType.TEXT),
            Property(
                name="metadata", data_type=DataType.JSON
            ),  # Metadata lưu dưới dạng JSON
        ],
    )
    print("Collection 'Document' created successfully")
except Exception as e:
    print(f"Collection creation error (might already exist): {e}")

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

    documents = []

    for item in chunk_data:
        tieu_de = item.get("tieu_de", "")
        noi_dung = item.get("noi_dung", "")
        khoan_list = item.get("khoan", [])

        if khoan_list:
            # Nối tất cả các khoản thành văn bản
            khoan_text = "\n".join(
                [f"Khoản {k['khoan']} {k['noi_dung']}" for k in khoan_list]
            )
            text = f"Tiêu đề: {tieu_de}\nNội dung: {noi_dung}\n{khoan_text}"
        else:
            text = f"Tiêu đề: {tieu_de}\nNội dung: {noi_dung}"

        documents.append(text)

    metadatas = [metadata] * len(
        vectors
    )  # Giả sử metadata giống nhau cho tất cả chunks

    collection = client.collections.get("Document")

    try:
        from weaviate.classes.data import DataObject

        collection.data.insert_many(
            [
                DataObject(
                    uuid=generate_uuid5(f"{file_id}_{i}"),
                    properties={"text": text, "metadata": metadata},
                    vector=vector,
                )
                for i, (text, vector, metadata) in enumerate(
                    zip(documents, vectors, metadatas)
                )
            ]
        )

        print(f"[✓] Đã index {len(chunk_ids)} chunks từ {file_id}")
        total_chunks += len(chunk_ids)
    except Exception as e:
        print(f"[!] Lỗi khi insert {file_id}: {e}")

print(f"\n Tổng cộng đã index: {total_chunks} chunks.")

# ---------------------------------------------------------------
# Close connection
client.close()
