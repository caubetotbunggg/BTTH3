import os
import json
import traceback
from glob import glob
from tqdm import tqdm
from dotenv import load_dotenv
import numpy as np
from sentence_transformers import SentenceTransformer
import weaviate
from weaviate.classes.config import AdditionalConfig, Timeout

# ======== Config ========
CHUNK_DIR = "data/processed/chunks/new"
META_DIR = "data/raw/html/new"
OUT_EMBED_DIR = "data/processed/embeddings/new"
LOG_FILE = "log/update_embedding_error.log"
COLLECTION_NAME = "Document"

os.makedirs(OUT_EMBED_DIR, exist_ok=True)
os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)

# ======== Load model & env ========
load_dotenv()
EMBED_MODEL_NAME = os.getenv("EMBEDDING_MODEL")
print(f"[+] Loading model: {EMBED_MODEL_NAME}")
model = SentenceTransformer(EMBED_MODEL_NAME)

# ======== Connect to Weaviate ========
print("[+] Connecting to Weaviate...")
client = weaviate.connect_to_local(
    host="localhost",
    port=8080,
    additional_config=AdditionalConfig(timeout=Timeout(query=60, insert=60)),
)
collection = client.collections.get(COLLECTION_NAME)
print(f"[✓] Connected to collection: {COLLECTION_NAME}")

# ======== Process all new chunks ========
chunk_files = glob(os.path.join(CHUNK_DIR, "*.json"))
print(f"[+] Found {len(chunk_files)} new chunk files")

for chunk_file in tqdm(chunk_files, desc="Embedding + Inserting"):
    try:
        law_id = os.path.basename(chunk_file).replace(".json", "")

        # Load chunk data
        with open(chunk_file, "r", encoding="utf-8") as f:
            chunks = json.load(f)

        if not chunks:
            print(f"[!] Skipping empty file: {law_id}")
            continue

        # Load metadata
        meta_path = os.path.join(META_DIR, f"{law_id}_meta.json")
        if not os.path.exists(meta_path):
            print(f"[!] Missing metadata for {law_id}, skipping.")
            continue

        with open(meta_path, "r", encoding="utf-8") as f:
            metadata = json.load(f)

        # Prepare sentences
        sentences = []
        for item in chunks:
            if item["chunk"].get("khoan") is None:
                sentence = f"passage: {item['meta']['title']} {item['chunk']['chuong']} {item['chunk']['tieu_de']} {item['chunk']['noi_dung']}"
            else:
                list_khoan = [
                    f"khoản {khoan['khoan']} {khoan['noi_dung']} "
                    for khoan in item["chunk"]["khoan"]
                ]
                all_khoan = "".join(list_khoan)
                sentence = f"passage: {item['meta']['title']} {item['chunk']['chuong']} {item['chunk']['tieu_de']} {item['chunk']['noi_dung']} {all_khoan}"
            sentences.append(sentence)

        # Embed
        embeddings = model.encode(sentences, batch_size=32, show_progress_bar=False)

        # Save .npy
        npy_path = os.path.join(OUT_EMBED_DIR, f"{law_id}.npy")
        np.save(npy_path, np.array(embeddings))
        print(f"[✓] Saved embeddings: {npy_path} ({len(embeddings)} vectors)")

        # Insert into Weaviate
        print(f"[→] Inserting to Weaviate: {law_id}")
        with collection.batch.dynamic() as batch:
            for embedding, text in zip(embeddings, sentences):
                batch.add_object(
                    properties={
                        "text": text,
                        "metadata": metadata
                    },
                    vector=embedding
                )

        print(f"[✓] Inserted {len(embeddings)} vectors for {law_id}")

    except Exception as e:
        with open(LOG_FILE, "a", encoding="utf-8") as log_f:
            log_f.write(f"[ERROR] {law_id}\n")
            log_f.write(f"File: {chunk_file}\n")
            log_f.write(traceback.format_exc())
            log_f.write("\n" + "=" * 80 + "\n")
        print(f"[✗] Error with {law_id}, logged.")

print("\n[✓] All done.")
