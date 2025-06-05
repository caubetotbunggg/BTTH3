import json
import logging
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests
from bs4 import BeautifulSoup

headers = {
    "User-Agent": "Mozilla/5.0 ...",
    "Referer": "https://luatvietnam.vn/",
    "Origin": "https://luatvietnam.vn",
    "Cookie": "MUID=...",
}

logging.basicConfig(filename="failed_links.log", level=logging.ERROR)

base_url = "https://luatvietnam.vn"
search_url_template = "https://luatvietnam.vn/van-ban/ajax/searchajax?"
"Keywords=&DocTypeIds=58&DocTypeIds=10&SearchOptions=1&RowAmount=20&PageIndex="

num_of_page = 38
batch_size = 15
concurrency_limit = 10  # tối đa 10 thread/batch
rate_limit_delay = 1.5  # delay mỗi request

all_urls = set()


def fetch_page(page_index):
    time.sleep(rate_limit_delay)
    page_url = f"{search_url_template}{page_index}"
    try:
        response = requests.get(page_url, headers=headers, timeout=10)
        if response.status_code != 200:
            logging.error(f"{page_url} - {response.status_code}")
            return []

        soup = BeautifulSoup(response.text, "html.parser")
        entries = soup.find_all("div", class_="post-type-doc")
        print(f" Page {page_index} có {len(entries)} văn bản.")

        urls = []
        for product in entries:
            a_tag = product.find("a")
            if a_tag:
                full_url = base_url + a_tag.get("href")
                urls.append(full_url)
        return urls
    except Exception as e:
        logging.error(f" Lỗi khi request {page_url}: {e}")
        return []


# Chia batch
batches = []
for i in range(1, num_of_page + 1, batch_size):
    batch = list(range(i, min(i + batch_size, num_of_page + 1)))
    batches.append(batch)


for batch_index, batch_pages in enumerate(batches, 1):
    with ThreadPoolExecutor(max_workers=concurrency_limit) as executor:
        futures = [executor.submit(fetch_page, i) for i in batch_pages]
        for future in as_completed(futures):
            result = future.result()
            all_urls.update(result)

# Ghi file JSON
all_urls_list = list(all_urls)
os.makedirs("../BTTH3/data/raw", exist_ok=True)
with open("../BTTH3/data/raw/law_links.json", "w", encoding="utf-8") as f:
    json.dump(all_urls_list, f, ensure_ascii=False, indent=2)

print(f"\n Đã lưu {len(all_urls_list)} URL")
