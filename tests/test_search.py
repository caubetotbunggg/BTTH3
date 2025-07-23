import json
import os
import random
import sys
from datetime import datetime

import chromadb
import numpy as np

CONFIG_PATH = "../BTTH3/index_config.json"
EMBED_DIR = "../BTTH3/data/processed/embeddings"
OUTPUT_MD = "../BTTH3/docs/search_results.md"

TOP_K = 5
NUM_SAMPLES = 5


def load_config():
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def init_chroma_client(config):
    client = chromadb.PersistentClient(path=config["persist_directory"])
    return client.get_collection(config["collection_name"])


def load_random_embeddings(n=NUM_SAMPLES):
    files = [f for f in os.listdir(EMBED_DIR) if f.endswith(".npy")]
    samples = []

    for file in random.sample(files, min(n, len(files))):
        vecs = np.load(os.path.join(EMBED_DIR, file))
        vec = vecs[random.randint(0, len(vecs)-1)]
        chunk_id = f"{file.replace('.npy','')}_{random.randint(0,999)}"
        samples.append((chunk_id, vec.tolist()))
    return samples


def query_and_report(collection, samples, k=TOP_K):
    os.makedirs(os.path.dirname(OUTPUT_MD), exist_ok=True)
    with open(OUTPUT_MD, "w", encoding="utf-8") as f:
        f.write(f"# Kết quả tìm kiếm mẫu (Top {k})\n\n")

        for i, (chunk_id, vec) in enumerate(samples, 1):
            f.write(f"## {i}. Query ID: `{chunk_id}`\n")
            res = collection.query(
                query_embeddings=[vec],
                n_results=k,
                include=["documents", "distances", "metadatas"],
            )
            docs = res["documents"][0]
            scores = res["distances"][0]
            metas = res["metadatas"][0]

            for rank, (doc, score, meta) in enumerate(zip(docs, scores, metas), 1):
                law = meta.get("law_id", "unknown")
                title = meta.get("title", "unknown")
                sim = 1 - score
                f.write(f"- **{rank}. Luật:** {law}, *{title}*, Sim: `{sim:.4f}`\n")

            f.write("\n---\n\n")

    print(f" Đã lưu kết quả tại: {OUTPUT_MD}")


def main():
    config = load_config()
    collection = init_chroma_client(config)
    samples = load_random_embeddings()
    query_and_report(collection, samples)


if __name__ == "__main__":
    main()
