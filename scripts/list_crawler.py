import json
import logging
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests
from bs4 import BeautifulSoup
from app.config.paths import RAW_DIR, LOG_DIR


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

        urls = []
        tag_counter = 0
        for product in entries:
            a_tag = product.find("a")
            if a_tag:
                full_url = base_url + a_tag.get("href")
                urls.append(full_url)
                tag_counter += 1
        return urls
    except Exception as e:
        logging.error(f"Lỗi khi request {page_url}: {e}")
        return []


def main():
    global headers, base_url, search_url_template, num_of_page, batch_size, concurrency_limit, rate_limit_delay
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36",
        "Referer": "https://luatvietnam.vn/",
        "Origin": "https://luatvietnam.vn",
        "Cookie": "MUID=...",
    }

    logging.basicConfig(filename=LOG_DIR / "failed_links.log", level=logging.ERROR)

    base_url = "https://luatvietnam.vn"
    search_url_template = (
        "https://luatvietnam.vn/van-ban/ajax/searchajax?"
        "Keywords=&DocTypeIds=58&DocTypeIds=10&SearchOptions=1&RowAmount=20&PageIndex="
    )

    num_of_page = 41  # total pages to crawl
    batch_size = 15  # pages per batch
    concurrency_limit = 10  # max thread/batch
    rate_limit_delay = 10  # delay seconds between requests

    all_urls = set()
    total = 0
    # Split into batches
    batches = []
    for i in range(1, num_of_page + 1, batch_size):
        batch = list(range(i, min(i + batch_size, num_of_page + 1)))
        batches.append(batch)

    # Fetch pages in batches

    MAX_RETRY = 3

    def fetch_with_retry(page_num):
        for attempt in range(1, MAX_RETRY + 1):
            try:
                result = fetch_page(page_num)
                if result and len(result) > 0:
                    return result
                else:
                    print(f"Page {page_num} attempt {attempt} ra 0, thử lại...")
            except Exception as e:
                print(f"Lỗi page {page_num} attempt {attempt}: {e}")
            time.sleep(2)  # retry delay
        print(f"Bỏ qua page {page_num} sau {MAX_RETRY} lần thử thất bại")
        return []


    for batch_index, batch_pages in enumerate(batches, 1):
        with ThreadPoolExecutor(max_workers=concurrency_limit) as executor:
            futures = {executor.submit(fetch_with_retry, i): i for i in batch_pages}
            batch_results = []
            for future in as_completed(futures):
                page_num = futures[future]
                try:
                    result = future.result()
                    print(f"Page {page_num}: {len(result)} links")
                    batch_results.append(result)
                except Exception as e:
                    print(f"Hoàn toàn fail page {page_num}: {e}")

            for result in batch_results:
                total += len(result)
                all_urls.update(result)

        print(f"  - Đã thu thập tổng cộng {total} result, {len(all_urls)} links trong batch {batch_index}")
        time.sleep(10)

    # Save to JSON file
    all_urls_list = list(all_urls)
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    with open(RAW_DIR / "law_links.json", "w", encoding="utf-8") as f:
        json.dump(all_urls_list, f, ensure_ascii=False, indent=2)

    print(f"Tổng thu được: {total}, Sau khi bỏ trùng: {len(all_urls)}")



if __name__ == "__main__":
    main()
