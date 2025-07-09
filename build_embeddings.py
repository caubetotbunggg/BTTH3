import json
import os
import time
import traceback

import numpy as np
from sentence_transformers import SentenceTransformer

# Load model một lần
model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")


def embed_chunk(chunk: dict):
    sentences = f"mã luật: {chunk['meta']['law_id']} \n tiêu đề: {chunk['meta']['title']} \n ngày: {chunk['meta']['date']} \n nội dung: {chunk['chunk']}"
    embedding = model.encode(sentences)
    return embedding


# Đọc 100 chunk đầu tiên
with open("../BTTH3/data/processed/all_chunks.json", "r", encoding="utf-8") as f:
    data = json.load(f)
for item in data[:100]:
    try:
        output_path = f"../BTTH3/data/processed/embeddings/{item['meta']['law_id']}.npy"
        if os.path.exists(output_path):
            continue

        # Embed và lưu
        embeddings = embed_chunk(item)
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        np.save(output_path, embeddings)

    except Exception as e:
        # Ghi log lỗi
        with open("../BTTH3/log/embedding_error.log", "a", encoding="utf-8") as log_f:
            log_f.write(f"Lỗi khi xử lý law_id: {item.get('law_id', 'UNKNOWN')}\n")
            log_f.write(traceback.format_exc())
            log_f.write("\n" + "=" * 80 + "\n")
        print(f" Lỗi với law_id: {item.get('law_id', 'UNKNOWN')}, đã ghi log.")
