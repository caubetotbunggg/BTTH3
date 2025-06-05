import json
import logging
import os

import requests
from bs4 import BeautifulSoup

with open("../BTTH3/data/raw/law_links.json", "r", encoding="utf-8") as f:
    data = json.load(f)

# Lọc bỏ dự thảo
filtered_data = [url for url in data if "du-thao" not in url]

# Cấu hình headers
headers = {
    "User-Agent": "Mozilla/5.0 ...",
    "Referer": "https://luatvietnam.vn/",
    "Origin": "https://luatvietnam.vn",
    "Cookie": "MUID=...",
}

# Cấu hình log fail
logging.basicConfig(filename="failed_access_links.log", level=logging.ERROR)

for url in filtered_data:
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code != 200:
            logging.error(f"Lỗi truy cập: {url} - {response.status_code}")
            continue

        html = response.text
        soup = BeautifulSoup(html, "html.parser")

        # Lấy metadata từ application/ld+json
        metadata_raw = soup.find("script", type="application/ld+json")
        if metadata_raw is None:
            logging.error(f"Không tìm thấy metadata: {url}")
            continue

        metadata_string = metadata_raw.string
        metadata_json = json.loads(metadata_string)

        law_id_raw = metadata_json.get("legislationIdentifier")
        if not law_id_raw:
            logging.error(f"Không có law_id: {url}")
            continue
        law_id = law_id_raw.replace("/", "-")

        # Lấy title, date
        title = metadata_json.get("name", "")
        date = metadata_json.get("legislationDate", "")

        os.makedirs("../BTTH3/data/raw/html", exist_ok=True)
        html_path = f"../BTTH3/data/raw/html/{law_id}.html"
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html)

        meta_path = f"../BTTH3/data/raw/html/{law_id}_meta.json"
        metadata_to_save = {"law_id": law_id, "title": title, "date": date}
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(metadata_to_save, f, ensure_ascii=False, indent=2)

    except Exception as e:
        logging.error(f"Lỗi xử lý {url}: {e}")
