import os
import json

def main():
    input_dir = "data/processed/chunks"
    output_path = "data/processed/all_chunks.json"
    all_chunks = []

    for filename in os.listdir(input_dir):
        if filename.endswith("_chunks.json"):
            file_path = os.path.join(input_dir, filename)
            with open(file_path, "r", encoding="utf-8") as f:
                chunks = json.load(f)
                all_chunks.extend(chunks)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(all_chunks, f, ensure_ascii=False, indent=2)
    print(f"Đã lưu {len(all_chunks)} chunk vào {output_path}")

if __name__ == "__main__":
    main()