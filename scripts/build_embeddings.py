import json
import os
import time
import traceback
from collections import defaultdict

import numpy as np
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
from tqdm import tqdm

load_dotenv()

from app.config.paths import PROCESSED_DIR, LOG_DIR

# Load model
print("[+] Loading embedding model...")
model = SentenceTransformer(os.getenv("EMBEDDING_MODEL"), trust_remote_code=True)

# Input file
print("[+] Loading data...")
with open(PROCESSED_DIR / "all_chunks.json", "r", encoding="utf-8") as f:
    data = json.load(f)

print(f"[+] Total chunks to process: {len(data):,}")

# Checkpoint file for resume
checkpoint_file = LOG_DIR / "embedding_checkpoint.json"
start_idx = 0
if os.path.exists(checkpoint_file):
    with open(checkpoint_file, "r") as f:
        start_idx = json.load(f).get("last_processed", 0)
    print(f"[+] Resuming from index: {start_idx:,}")

# Group embeddings by law_id
grouped = defaultdict(list)  # law_id → list of (embedding, metadata)
error_count = 0
attempted_count = 0
# Error handling thresholds (configurable via env)
# Either set EMBEDDING_MAX_ERRORS (absolute) or EMBEDDING_ERROR_THRESHOLD (fraction 0-1)
MAX_ERRORS = int(os.getenv("EMBEDDING_MAX_ERRORS", "0"))
ERROR_THRESHOLD = float(os.getenv("EMBEDDING_ERROR_THRESHOLD", "0.05"))
abort_processing = False

# Process in batches with progress bar
batch_size = 100  # Process 100 items at a time
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

    # Prepare sentences for the batch
    sentences = []
    batch_items = []

    for item in batch_data:
        attempted_count += 1
        try:
            if item["chunk"]["khoan"] is None:
                sentence = f"passage: {item['meta']['title']} {item['chunk']['chuong']} {item['chunk']['tieu_de']} {item['chunk']['noi_dung']}"
                sentences.append(sentence)
                batch_items.append(item)
            else:
                list_khoan = []
                for khoan in item["chunk"]["khoan"]:
                    noi_dung_khoan = f"khoản {khoan['khoan']} {khoan['noi_dung']} "
                    list_khoan.append(noi_dung_khoan)
                    all_khoan = "".join(list_khoan)

                sentence = f"passage: {item['meta']['title']} {item['chunk']['chuong']} {item['chunk']['tieu_de']} {item['chunk']['noi_dung']} {all_khoan}"
                sentences.append(sentence)
                batch_items.append(item)
        except Exception as e:
            error_count += 1
            with open(
                LOG_DIR / "embedding_error.log", "a", encoding="utf-8"
            ) as log_f:
                log_f.write(f"Lỗi: {e}\n")
                log_f.write(
                    f"Lỗi khi chuẩn bị data - Index: {actual_start + len(batch_items)}\n"
                )
                log_f.write(f"Item: {item}\n")
                log_f.write(traceback.format_exc())
                log_f.write("\n" + "=" * 80 + "\n")

            # Check thresholds and abort if error rate or absolute errors exceed limits
            if (MAX_ERRORS and error_count >= MAX_ERRORS) or (
                attempted_count > 0 and error_count / attempted_count > ERROR_THRESHOLD
            ):
                with open(LOG_DIR / "embedding_error.log", "a", encoding="utf-8") as lf:
                    lf.write(
                        f"[FATAL] Error threshold exceeded: errors={error_count}, attempts={attempted_count}, threshold={ERROR_THRESHOLD}, max_errors={MAX_ERRORS}\n"
                    )
                print(f"[FATAL] Error threshold exceeded: {error_count}/{attempted_count} (>{ERROR_THRESHOLD}). Aborting.")
                # save checkpoint so we can resume
                try:
                    with open(checkpoint_file, "w") as cf:
                        json.dump({"last_processed": actual_start}, cf)
                except Exception:
                    pass
                abort_processing = True
                break

    # If we flagged abort during per-item processing, stop outer loop
    if abort_processing:
        break

    # Embed whole batch if there are sentences
    if sentences:
        try:
            embeddings = model.encode(sentences, batch_size=256, show_progress_bar=False)

            for embedding, item in zip(embeddings, batch_items):
                law_id = item["meta"]["law_id"]
                grouped[law_id].append((embedding, item["meta"]))

        except Exception as e:
            # This batch failed to embed — count failures as number of items in the batch
            batch_failures = len(batch_items) if batch_items else 1
            error_count += batch_failures
            with open(
                LOG_DIR / "embedding_error.log", "a", encoding="utf-8"
            ) as log_f:
                log_f.write(f"Lỗi: {e}\n")
                log_f.write(
                    f"Lỗi khi embedding batch - Index: {actual_start}-{actual_end}\n"
                )
                log_f.write(traceback.format_exc())
                log_f.write("\n" + "=" * 80 + "\n")

            # Check thresholds and abort if necessary
            if (MAX_ERRORS and error_count >= MAX_ERRORS) or (
                attempted_count > 0 and error_count / attempted_count > ERROR_THRESHOLD
            ):
                with open(LOG_DIR / "embedding_error.log", "a", encoding="utf-8") as lf:
                    lf.write(
                        f"[FATAL] Error threshold exceeded during embedding: errors={error_count}, attempts={attempted_count}, threshold={ERROR_THRESHOLD}, max_errors={MAX_ERRORS}\n"
                    )
                print(f"[FATAL] Error threshold exceeded during embedding: {error_count}/{attempted_count} (>{ERROR_THRESHOLD}). Aborting.")
                try:
                    with open(checkpoint_file, "w") as cf:
                        json.dump({"last_processed": actual_start}, cf)
                except Exception:
                    pass
                abort_processing = True
                break

    # Save checkpoint for 10 batches
    if batch_idx % (10 * batch_size) == 0:
        with open(checkpoint_file, "w") as f:
            json.dump({"last_processed": actual_end}, f)

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

if abort_processing:
    print(f"\n[!] Embedding aborted early due to error threshold. Total groups so far: {len(grouped)}")
    print(f"[!] Total errors: {error_count}, attempts: {attempted_count}")
else:
    print(f"\n[+] Embedding completed! Total groups: {len(grouped)}")
    print(f"[+] Total errors: {error_count}")

# Save each group of embeddings to a .npy file
print("[+] Saving embeddings ...")
for law_id, embeds_and_meta in tqdm(grouped.items(), desc="Saving files"):
    try:
        embeddings = [e for e, _ in embeds_and_meta]
        metadata = embeds_and_meta[0][1]  # Use shared metadata (VD: title, date,...)

        # Save embeddings
        # ensure embeddings dir exists
        (PROCESSED_DIR / "embeddings").mkdir(parents=True, exist_ok=True)
        np.save(
            PROCESSED_DIR / "embeddings" / f"{law_id}.npy", np.array(embeddings)
        )

        print(f"[+] Saved: {law_id}.npy ({len(embeddings)} chunks)")

    except Exception as e:
        with open(LOG_DIR / "embedding_error.log", "a", encoding="utf-8") as log_f:
            log_f.write(f"Lỗi: {e}\n")
            log_f.write(f"Lỗi khi lưu file cho law_id: {law_id}\n")
            log_f.write(traceback.format_exc())
            log_f.write("\n" + "=" * 80 + "\n")

# Delete checkpoint file after completion
if os.path.exists(checkpoint_file):
    os.remove(checkpoint_file)
    print("[+] Checkpoint file cleaned up") 

total_time = time.time() - start_time
print(f"\n[✓] All done! Total time: {total_time/60:.1f} minutes")
print(f"[✓] Average speed: {len(data)/total_time:.1f} items/second")
print(f"[✓] Total law groups: {len(grouped)}")
print(f"[✓] Total errors: {error_count}")
