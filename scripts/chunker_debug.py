import json
import os
import re


def chunk_text(text):
    # where X can be a Roman numeral or Arabic numeral
    chapter_matches = list(re.finditer(r"(?im)^\s*chương\s+[\divxlcdm]+\.?", text))
    chunks = []

    if chapter_matches:
        
        for idx, match in enumerate(chapter_matches):
            chapter_title = match.group(0).strip()
            start_pos = match.end()
            end_pos = (
                chapter_matches[idx + 1].start()
                if idx + 1 < len(chapter_matches)
                else len(text)
            )
            chapter_text = text[start_pos:end_pos].strip()

            
            chunks.extend(chunk_by_article(chapter_text, chapter_title))
    else:
        
        chunks.extend(chunk_by_article(text, chapter_title=None))

    return chunks


def chunk_by_article(text, chapter_title=None):
    raw_chunks = re.split(r"(?=Điều\s+\d+\.?)", text)
    result = []

    for chunk in raw_chunks:
        match_dieu = re.match(r"(Điều\s+\d+\.?.*)", chunk.strip())
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

        result.append(
            {
                "chuong": chapter_title,
                "tieu_de": tieu_de,
                "noi_dung": noi_dung,
                "khoan": khoan_list if khoan_list else None,
            }
        )
    return result


def process_failed_files():
    from app.config.paths import PROCESSED_DIR, DATA_DIR

    input_dir = PROCESSED_DIR / "text"
    output_dir = PROCESSED_DIR / "chunks"
    failed_json_path = DATA_DIR / "unstructured" / "failed_regex.json"

    output_dir.mkdir(parents=True, exist_ok=True)

    with open(failed_json_path, "r", encoding="utf-8") as f:
        failed_files = json.load(f)

    re_failed = []

    for filename in failed_files:
        law_id = filename.replace(".txt", "")
        input_path = input_dir / filename
        output_path = output_dir / f"{law_id}_chunks.json"

        if not input_path.exists():
            continue
        with open(input_path, "r", encoding="utf-8") as f:
            text = f.read()
            chunks = chunk_text(text)
            if not chunks:
                re_failed.append(filename)
                continue

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(chunks, f, ensure_ascii=False, indent=2)

    if re_failed:
        with open(failed_json_path, "w", encoding="utf-8") as f:
            json.dump(re_failed, f, ensure_ascii=False, indent=2)
        print(f"{len(re_failed)} file vẫn không parse được.")


if __name__ == "__main__":
    process_failed_files()
