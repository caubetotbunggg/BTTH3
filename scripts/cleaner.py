import json
import os

from bs4 import BeautifulSoup


def extract_text(html):
    soup = BeautifulSoup(html, "html.parser")
    soup = soup.find("div", class_="the-document-body ndthaydoi noidungtracuu")
    if not soup:
        return ""
    return soup.get_text(strip=True, separator="\n")


if __name__ == "__main__":
    from app.config.paths import PROCESSED_DIR, RAW_DIR, DATA_DIR

    (PROCESSED_DIR / "text").mkdir(parents=True, exist_ok=True)

    html_dir = RAW_DIR / "html"
    file_need_debug = []
    for file in os.listdir(html_dir):
        if file.endswith(".html"):
            with open(html_dir / file, "r", encoding="utf-8") as f:
                html_content = f.read()
                extracted = extract_text(html_content)
                if not extracted:
                    file_need_debug.append(file)
                    continue
                base_name = os.path.splitext(file)[0]
                out_path = PROCESSED_DIR / "text" / f"{base_name}.txt"
                with open(out_path, "w", encoding="utf-8") as out_f:
                    out_f.write(extracted)

    if file_need_debug:
        (DATA_DIR / "unstructured").mkdir(parents=True, exist_ok=True)
        with open(DATA_DIR / "unstructured" / "file_need_debug.json", "w", encoding="utf-8") as f:
            json.dump(file_need_debug, f, ensure_ascii=False, indent=2)
