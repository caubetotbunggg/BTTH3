import json
import os

from bs4 import BeautifulSoup

with open("../BTTH3/data/unstructured/file_need_debug.json", "r", encoding="utf-8") as f:
    file_need_debug = json.load(f)
for file in file_need_debug:
    with open(os.path.join("../BTTH3/data/raw/html", file), "r", encoding="utf-8") as f:
        html_content = f.read()
        soup = BeautifulSoup(html_content, "html.parser")
        base_name = os.path.splitext(file)[0]
        out_path = os.path.join("../BTTH3/data/processed/text", f"{base_name}.txt")
        with open(out_path, "w", encoding="utf-8") as out_f:
            out_f.write(soup.get_text(strip=True, separator="\n"))
