import json
import os


def main():
    input_dir = "data/processed/chunks"
    meta_dir = "data/raw/html"
    output_path = "data/processed/all_chunks.json"
    all_chunks = []

    for filename in os.listdir(input_dir):
        if filename.endswith("_chunks.json"):
            chunk_path = os.path.join(input_dir, filename)
            base_name = filename.replace("_chunks.json", "")
            meta_path = os.path.join(meta_dir, f"{base_name}_meta.json")

            # Load chunk
            with open(chunk_path, "r", encoding="utf-8") as f:
                chunks = json.load(f)

            # Load meta (if exists)
            if os.path.exists(meta_path):
                with open(meta_path, "r", encoding="utf-8") as meta_f:
                    meta = json.load(meta_f)
                    print(f"Loaded meta for {base_name} from {meta_path}")
            else:
                meta = {}

            # Group each chunk with meta
            for chunk in chunks:
                all_chunks.append({"meta": meta, "chunk": chunk})

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(all_chunks, f, ensure_ascii=False, indent=2)
    print(f" Saved {len(all_chunks)} chunk to {output_path}")


if __name__ == "__main__":
    main()
