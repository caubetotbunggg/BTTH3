import json
import os

from bs4 import BeautifulSoup
from app.config.paths import PROCESSED_DIR, RAW_DIR, DATA_DIR

with open(DATA_DIR / "unstructured" / "file_need_debug.json", "r", encoding="utf-8") as f:
    file_need_debug = json.load(f)
for file in file_need_debug:
    with open(RAW_DIR / "html" / file, "r", encoding="utf-8") as f:
        html_content = f.read()
        soup = BeautifulSoup(html_content, "html.parser")
        base_name = os.path.splitext(file)[0]
        out_path = PROCESSED_DIR / "text" / f"{base_name}.txt"
        with open(out_path, "w", encoding="utf-8") as out_f:
            out_f.write(soup.get_text(strip=True, separator="\n"))
