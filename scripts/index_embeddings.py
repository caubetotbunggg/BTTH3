import json
import os

import numpy as np
import weaviate
import weaviate.classes.config as wvcc
from weaviate.classes.config import DataType, Property
from weaviate.classes.data import DataObject
from weaviate.util import generate_uuid5

import weaviate
from weaviate.classes.init import Auth
import os
from dotenv import load_dotenv

load_dotenv()

# Best practice: store your credentials in environment variables
weaviate_url = os.getenv("WEAVIATE_URL")
weaviate_api_key = os.getenv("WEAVIATE_API_KEY")

client = weaviate.connect_to_weaviate_cloud(
    cluster_url=weaviate_url,
    auth_credentials=Auth.api_key(weaviate_api_key),
)

print(client.is_ready())  # Should print: `True`

# CREATE COLLECTION
try:
    client.collections.create(
        name="Document",
        vector_config=wvcc.VectorConfig.self_provided(),
        properties=[
            Property(name="text", data_type=DataType.TEXT),
            Property(
                name="metadata", data_type=DataType.JSON
            ),  # Metadata field in JSON format
        ],
    )
    print("Collection 'Document' created successfully")
except Exception as e:
    print(f"Collection creation error (might already exist): {e}")

# ==== Data paths ====
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

    # Check if metadata exists
    if not os.path.exists(meta_path):
        print(f"[!] Skipping {file_id}: missing metadata")
        continue

    # Load vectors and metadata
    vectors_np = np.load(embedding_path)
    if len(vectors_np.shape) == 1:
        vectors = [vectors_np.tolist()]
    else:
        vectors = vectors_np.tolist()

    with open(meta_path, "r", encoding="utf-8") as f:
        metadata = json.load(f)

    # Create necessary fields
    chunk_ids = [f"{file_id}_{i}" for i in range(len(vectors))]
    if not os.path.exists(chunk_path):
        print(f"[!] Skipping {file_id}: missing chunk data")
        continue
    else:
        with open(chunk_path, "r", encoding="utf-8") as f:
            chunk_data = json.load(f)

    if len(chunk_data) != len(vectors):
        print(f"[!] Skipping {file_id}: number of chunks does not match vectors")
        print(f"  - Vectors: {len(vectors)}, Chunks: {len(chunk_data)}")
        continue

    documents = []

    for item in chunk_data:
        tieu_de = item.get("tieu_de", "")
        noi_dung = item.get("noi_dung", "")
        khoan_list = item.get("khoan", [])

        if khoan_list:
            # Join khoan text
            khoan_text = "\n".join(
                [f"Khoản {k['khoan']} {k['noi_dung']}" for k in khoan_list]
            )
            text = f"Tiêu đề: {tieu_de}\nNội dung: {noi_dung}\n{khoan_text}"
        else:
            text = f"Tiêu đề: {tieu_de}\nNội dung: {noi_dung}"

        documents.append(text)

    metadatas = [metadata] * len(vectors)  # Assuming same metadata for all vectors

    collection = client.collections.get("Document")

    try:

        # Insert data into Weaviate
        collection.data.insert_many(
            [
                DataObject(
                    uuid=generate_uuid5(f"{file_id}_{i}"),
                    properties={"text": text, "metadata": metadata["title"]},
                    vector=vector,
                )
                for i, (text, vector, metadata) in enumerate(
                    zip(documents, vectors, metadatas)
                )
            ]
        )

        print(f"[✓] Indexed {len(chunk_ids)} chunks from {file_id}")
        total_chunks += len(chunk_ids)
    except Exception as e:
        print(f"[!] Error inserting {file_id}: {e}")

print(f"\nTotal indexed: {total_chunks} chunks.")

# Close connection
client.close()
