import json
import os
import re
from email.mime import text


def chunk_by_chapter_and_article(text):
    # where X can be a Roman numeral or Arabic numeral
    chapter_matches = list(re.finditer(r"(?im)^\s*chương\s+[\divxlcdm]+\.?", text))
    chunks = []

    for idx, match in enumerate(chapter_matches):
        chapter_title = match.group(0).strip()
        start_pos = match.end()
        end_pos = (
            chapter_matches[idx + 1].start()
            if idx + 1 < len(chapter_matches)
            else len(text)
        )
        chapter_text = text[start_pos:end_pos].strip()

        raw_chunks = re.split(r"(?=Điều\s+\d+\.)", chapter_text)
        for chunk in raw_chunks:
            match_dieu = re.match(r"(Điều\s+\d+\..*)", chunk.strip())
            if not match_dieu:
                continue
            tieu_de = match_dieu.group(1)
            noi_dung = chunk.strip()[len(tieu_de) :].strip()

            
            khoan_list = []
            khoan_chunks = re.split(r"(?m)^\s*(\d+[\.\-\)])", noi_dung)
            for j in range(1, len(khoan_chunks), 2):
                khoan_so = khoan_chunks[j].strip()
                khoan_noi_dung = (
                    khoan_chunks[j + 1].strip() if j + 1 < len(khoan_chunks) else ""
                )
                khoan_list.append({"khoan": khoan_so, "noi_dung": khoan_noi_dung})

            if khoan_list:
                noi_dung = ""

            chunks.append(
                {
                    "chuong": chapter_title,
                    "tieu_de": tieu_de,
                    "noi_dung": noi_dung,
                    "khoan": khoan_list if khoan_list else None,
                }
            )

    return chunks


def process_all_files():
    from app.config.paths import PROCESSED_DIR, DATA_DIR

    input_dir = PROCESSED_DIR / "text"
    output_dir = PROCESSED_DIR / "chunks"
    output_dir.mkdir(parents=True, exist_ok=True)
    failed_files = []
    for filename in os.listdir(input_dir):
        if filename.endswith(".txt"):
            law_id = filename.replace(".txt", "")
            input_path = input_dir / filename
            output_path = output_dir / f"{law_id}_chunks.json"
            with open(input_path, "r", encoding="utf-8") as f:
                text = f.read()
                chunks = chunk_by_chapter_and_article(text)
                if not chunks:
                    failed_files.append(filename)
                    continue
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(chunks, f, ensure_ascii=False, indent=2)
    if failed_files:
        # Save list of failed files to JSON
        unstructured_dir = DATA_DIR / "unstructured"
        unstructured_dir.mkdir(parents=True, exist_ok=True)
        failed_path = unstructured_dir / "failed_regex.json"
        with open(failed_path, "w", encoding="utf-8") as f:
            json.dump(failed_files, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    process_all_files()
