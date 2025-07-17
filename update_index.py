import json
import os

import numpy as np
from chromadb import PersistentClient
from sentence_transformers import SentenceTransformer

# ========== CẤU HÌNH ==========
DB_DIR = "chroma_db"
COLLECTION_NAME = "legal_chunks"
NEW_CHUNKS_DIR = "data/processed/chunks/new"
EMBED_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

# ========== LOAD ==========
client = PersistentClient(path=DB_DIR)
collection = client.get_or_create_collection(COLLECTION_NAME)
model = SentenceTransformer(EMBED_MODEL_NAME)

# ========== ĐỌC DỮ LIỆU ==========
chunks = []
for file in os.listdir(NEW_CHUNKS_DIR):
    if file.endswith(".json"):
        with open(os.path.join(NEW_CHUNKS_DIR, file), "r", encoding="utf-8") as f:
            chunks.extend(json.load(f))

print(f"[+] Loaded {len(chunks)} new chunks")

# ========== XỬ LÝ ==========
documents = []
metadatas = []
ids = []
texts = []

for i, chunk in enumerate(chunks):
    text = f"mã luật: {chunk['meta']['law_id']} \n tiêu đề: {chunk['meta']['title']} \n ngày: {chunk['meta']['date']} \n nội dung: {chunk['chunk']}"
    texts.append(text)
    documents.append(chunk["chunk"])
    metadatas.append(chunk["meta"])
    ids.append(f"{chunk['meta']['law_id']}_{i:04d}")

print(f"[+] Generating embeddings for {len(texts)} chunks")
embeddings = model.encode(texts, show_progress_bar=True)

# ========== CHÈN VÀO INDEX ==========
print(f"[+] Adding to ChromaDB...")
collection.upsert(
    documents=documents, embeddings=embeddings, metadatas=metadatas, ids=ids
)

print(f"[✓] Update completed.")
