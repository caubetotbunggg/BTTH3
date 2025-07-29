import json
import os
import time
import traceback
from collections import defaultdict
from multiprocessing import Pool, cpu_count

import numpy as np
from tqdm import tqdm

import psutil

def estimate_safe_processes(mem_per_process_gb):
    total_ram = psutil.virtual_memory().available / (1024 ** 3)  # GB
    safe_processes = int(total_ram // mem_per_process_gb)
    return min(cpu_count(), max(1, safe_processes))


def process_batch(batch_data):
    # Import model trong từng process
    from sentence_transformers import SentenceTransformer

    model = SentenceTransformer("intfloat/multilingual-e5-small")
    result = []
    errors = []

    for item in batch_data:
        try:
            if item["chunk"]["khoan"] is None:
                sentence = f"passage: {item['meta']['title']} {item['chunk']['chuong']} {item['chunk']['tieu_de']} {item['chunk']['noi_dung']}"
            else:
                list_khoan = [
                    f"khoản {k['khoan']} {k['noi_dung']}" for k in item["chunk"]["khoan"]
                ]
                all_khoan = " ".join(list_khoan)
                sentence = f"passage: {item['meta']['title']} {item['chunk']['chuong']} {item['chunk']['tieu_de']} {item['chunk']['noi_dung']} {all_khoan}"

            embedding = model.encode(sentence, show_progress_bar=False)
            law_id = item["meta"]["law_id"]
            result.append((law_id, embedding, item["meta"]))
        except Exception as e:
            errors.append({
                "error": str(e),
                "item": item,
                "trace": traceback.format_exc()
            })

    return result, errors


def main():
    # === Chuẩn bị thư mục, dữ liệu ===
    os.makedirs("../BTTH3/data/processed/embeddings", exist_ok=True)
    os.makedirs("../BTTH3/data/raw/html", exist_ok=True)
    os.makedirs("../BTTH3/log", exist_ok=True)

    print("[+] Loading data...")
    with open("../BTTH3/data/processed/all_chunks.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    print(f"[+] Total chunks to process: {len(data):,}")

    checkpoint_file = "../BTTH3/log/embedding_checkpoint.json"
    start_idx = 0
    if os.path.exists(checkpoint_file):
        with open(checkpoint_file, "r") as f:
            start_idx = json.load(f).get("last_processed", 0)
        print(f"[+] Resuming from index: {start_idx:,}")

    data = data[start_idx:]
    batch_size = 100
    batches = [data[i:i + batch_size] for i in range(0, len(data), batch_size)]

    # === Chạy multiprocessing ===
    start_time = time.time()
    print(f"[+] Starting multiprocessing with {cpu_count()} workers...")
    print(f"[+] Memory of local machine: {psutil.virtual_memory().total / (1024 ** 3):.2f} GB")
    safe_processes = estimate_safe_processes(1.5)  # Giả sử mỗi process cần 1.5 GB RAM
    print(f"[+] Estimated safe processes: {safe_processes}")
    with Pool(processes=safe_processes) as pool:
        all_results = list(tqdm(pool.imap(process_batch, batches), total=len(batches)))

    # === Gom kết quả ===
    grouped = defaultdict(list)
    error_count = 0

    current_index = start_idx
    for (batch_result, batch_errors), batch in zip(all_results, batches):
        for law_id, emb, meta in batch_result:
            grouped[law_id].append((emb, meta))

        if batch_errors:
            error_count += len(batch_errors)
            with open("../BTTH3/log/embedding_error.log", "a", encoding="utf-8") as log_f:
                for err in batch_errors:
                    log_f.write(f"Lỗi: {err['error']}\n")
                    log_f.write(f"Item: {err['item']}\n")
                    log_f.write(err["trace"])
                    log_f.write("\n" + "=" * 80 + "\n")

        # Cập nhật checkpoint sau mỗi batch
        current_index += len(batch)
        with open(checkpoint_file, "w") as f:
            json.dump({"last_processed": current_index}, f)

    # === Lưu kết quả ===
    print("[+] Saving embeddings and metadata...")
    for law_id, embeds_and_meta in tqdm(grouped.items(), desc="Saving files"):
        try:
            embeddings = [e for e, _ in embeds_and_meta]
            metadata = embeds_and_meta[0][1]

            np.save(f"../BTTH3/data/processed/embeddings/{law_id}.npy", np.array(embeddings))
            with open(f"../BTTH3/data/raw/html/{law_id}_meta.json", "w", encoding="utf-8") as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2)
        except Exception as e:
            with open("../BTTH3/log/embedding_error.log", "a", encoding="utf-8") as log_f:
                log_f.write(f"Lỗi khi lưu file cho law_id {law_id}: {e}\n")
                log_f.write(traceback.format_exc())
                log_f.write("\n" + "=" * 80 + "\n")

    # === Kết thúc ===
    if os.path.exists(checkpoint_file):
        os.remove(checkpoint_file)

    total_time = time.time() - start_time
    print(f"\n[✓] All done! Total time: {total_time/60:.1f} minutes")
    print(f"[✓] Average speed: {len(data)/total_time:.1f} items/second")
    print(f"[✓] Total law groups: {len(grouped)}")
    print(f"[✓] Total errors: {error_count}")


if __name__ == "__main__":
    from multiprocessing import freeze_support
    freeze_support()
    main()
