import json
import os
import re


def chunk_text(text):
    # Tìm chương (chấp nhận số thường/số La Mã, có hoặc không có dấu chấm)
    chapter_matches = list(re.finditer(r"(?im)^\s*chương\s+[\divxlcdm]+\.?", text))
    chunks = []

    if chapter_matches:
        # Có chương: tách theo Chương -> Điều -> Khoản
        for idx, match in enumerate(chapter_matches):
            chapter_title = match.group(0).strip()
            start_pos = match.end()
            end_pos = (
                chapter_matches[idx + 1].start()
                if idx + 1 < len(chapter_matches)
                else len(text)
            )
            chapter_text = text[start_pos:end_pos].strip()

            # Tách theo Điều
            chunks.extend(chunk_by_article(chapter_text, chapter_title))
    else:
        # Không có chương: chỉ tách theo Điều
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
        noi_dung = chunk.strip()[len(tieu_de):].strip()

        # Tách khoản: 1. hoặc 1- hoặc 1)
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
    input_dir = "../BTTH3/data/processed/text"
    output_dir = "../BTTH3/data/processed/chunks"
    failed_json_path = "../BTTH3/data/unstructured/failed_regex.json"

    os.makedirs(output_dir, exist_ok=True)

    with open(failed_json_path, "r", encoding="utf-8") as f:
        failed_files = json.load(f)

    re_failed = []

    for filename in failed_files:
        law_id = filename.replace(".txt", "")
        input_path = os.path.join(input_dir, filename)
        output_path = os.path.join(output_dir, f"{law_id}_chunks.json")

        if not os.path.exists(input_path):
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
