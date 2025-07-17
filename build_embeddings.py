import json
import os
import time
import traceback
from collections import defaultdict

import numpy as np
from sentence_transformers import SentenceTransformer
from tqdm import tqdm

# Tạo thư mục cần thiết
os.makedirs("../BTTH3/data/processed/embeddings", exist_ok=True)
os.makedirs("../BTTH3/data/raw/html", exist_ok=True)
os.makedirs("../BTTH3/log", exist_ok=True)

# Load model
print("[+] Loading embedding model...")
model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

# Tập tin đầu vào
print("[+] Loading data...")
with open("../BTTH3/data/processed/all_chunks.json", "r", encoding="utf-8") as f:
    data = json.load(f)

print(f"[+] Total chunks to process: {len(data):,}")

# Checkpoint file để resume
checkpoint_file = "../BTTH3/log/embedding_checkpoint.json"
start_idx = 0
if os.path.exists(checkpoint_file):
    with open(checkpoint_file, "r") as f:
        start_idx = json.load(f).get("last_processed", 0)
    print(f"[+] Resuming from index: {start_idx:,}")

# Gom embedding theo law_id
grouped = defaultdict(list)  # law_id → list of (embedding, metadata)
error_count = 0

# Xử lý với batch và progress bar
batch_size = 100  # Xử lý 100 items mỗi lần
total_batches = (len(data) - start_idx + batch_size - 1) // batch_size

print("[+] Starting embedding process...")
start_time = time.time()

for batch_idx in tqdm(
    range(0, len(data) - start_idx, batch_size),
    desc="Processing batches",
    total=total_batches,
):

    actual_start = start_idx + batch_idx
    actual_end = min(actual_start + batch_size, len(data))
    batch_data = data[actual_start:actual_end]

    # Chuẩn bị sentences cho batch
    sentences = []
    batch_items = []

    for item in batch_data:
        try:
            if item['chunk']['khoan'] is None:
                sentence = f"{item['meta']['title']} {item['chunk']['chuong']} {item['chunk']['tieu_de']} {item['chunk']['noi_dung']}"
                sentences.append(sentence)
                batch_items.append(item)
            else:
                list_khoan = []
                for khoan in item['chunk']['khoan']:
                    noi_dung_khoan = f"khoản {khoan['khoan']} {khoan['noi_dung']} "
                    list_khoan.append(noi_dung_khoan)
                    all_khoan = "".join(list_khoan)

                sentence = f"{item['meta']['title']} {item['chunk']['chuong']} {item['chunk']['tieu_de']} {item['chunk']['noi_dung']} {all_khoan}"
                sentences.append(sentence)
                batch_items.append(item)
        except Exception as e:
            error_count += 1
            with open(
                "../BTTH3/log/embedding_error.log", "a", encoding="utf-8"
            ) as log_f:
                log_f.write(
                    f"Lỗi khi chuẩn bị data - Index: {actual_start + len(batch_items)}\n"
                )
                log_f.write(f"Item: {item}\n")
                log_f.write(traceback.format_exc())
                log_f.write("\n" + "=" * 80 + "\n")

    # Embed cả batch cùng lúc
    if sentences:
        try:
            embeddings = model.encode(sentences, batch_size=32, show_progress_bar=False)

            # Gom vào grouped
            for embedding, item in zip(embeddings, batch_items):
                law_id = item["meta"]["law_id"]
                grouped[law_id].append((embedding, item["meta"]))

        except Exception as e:
            error_count += 1
            with open(
                "../BTTH3/log/embedding_error.log", "a", encoding="utf-8"
            ) as log_f:
                log_f.write(
                    f"Lỗi khi embedding batch - Index: {actual_start}-{actual_end}\n"
                )
                log_f.write(traceback.format_exc())
                log_f.write("\n" + "=" * 80 + "\n")

    # Save checkpoint mỗi 10 batches
    if batch_idx % (10 * batch_size) == 0:
        with open(checkpoint_file, "w") as f:
            json.dump({"last_processed": actual_end}, f)

        # In thống kê tiến trình
        elapsed_time = time.time() - start_time
        processed = actual_end - start_idx
        if processed > 0:
            avg_time_per_item = elapsed_time / processed
            remaining_items = len(data) - actual_end
            eta_seconds = remaining_items * avg_time_per_item
            eta_minutes = eta_seconds / 60

            print(f"\n[Progress] Processed: {processed:,}/{len(data):,} items")
            print(f"[Progress] Speed: {processed/elapsed_time:.1f} items/sec")
            print(f"[Progress] ETA: {eta_minutes:.1f} minutes")
            print(f"[Progress] Errors: {error_count}")

print(f"\n[+] Embedding completed! Total groups: {len(grouped)}")
print(f"[+] Total errors: {error_count}")

# Lưu từng nhóm embeddings thành 1 file .npy và metadata tương ứng
print("[+] Saving embeddings and metadata...")
for law_id, embeds_and_meta in tqdm(grouped.items(), desc="Saving files"):
    try:
        embeddings = [e for e, _ in embeds_and_meta]
        metadata = embeds_and_meta[0][1]  # dùng chung metadata (VD: title, date,...)

        # Lưu embeddings
        np.save(
            f"../BTTH3/data/processed/embeddings/{law_id}.npy", np.array(embeddings)
        )

        # Lưu metadata
        with open(
            f"../BTTH3/data/raw/html/{law_id}_meta.json", "w", encoding="utf-8"
        ) as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)

        print(f"[+] Saved: {law_id}.npy ({len(embeddings)} chunks)")

    except Exception as e:
        with open("../BTTH3/log/embedding_error.log", "a", encoding="utf-8") as log_f:
            log_f.write(f"Lỗi khi lưu file cho law_id: {law_id}\n")
            log_f.write(traceback.format_exc())
            log_f.write("\n" + "=" * 80 + "\n")

# Xóa checkpoint file sau khi hoàn thành
if os.path.exists(checkpoint_file):
    os.remove(checkpoint_file)
    print("[+] Checkpoint file cleaned up")

total_time = time.time() - start_time
print(f"\n[✓] All done! Total time: {total_time/60:.1f} minutes")
print(f"[✓] Average speed: {len(data)/total_time:.1f} items/second")
print(f"[✓] Total law groups: {len(grouped)}")
print(f"[✓] Total errors: {error_count}")
