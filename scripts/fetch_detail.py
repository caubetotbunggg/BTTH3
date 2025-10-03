import json
import logging
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests
from bs4 import BeautifulSoup

MAX_RETRY = 5   # số lần thử lại nếu lỗi
RETRY_DELAY = 3 # delay sau khi fail

def process_url(url, headers):
    for attempt in range(1, MAX_RETRY + 1):
        try:
            time.sleep(rate_limit_delay)

            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code != 200:
                logging.error(f"Lỗi truy cập: {url} - {response.status_code}")
                #print(f"[FAIL] {url} - status {response.status_code}, retry {attempt}/{MAX_RETRY}")
                time.sleep(RETRY_DELAY)
                continue

            html = response.text
            soup = BeautifulSoup(html, "html.parser")

            # Extract metadata từ application/ld+json
            metadata_raw = soup.find("script", type="application/ld+json")
            if metadata_raw is None:
                logging.error(f"Không tìm thấy metadata: {url}")
                print(f"[FAIL] {url} - không có metadata, retry {attempt}/{MAX_RETRY}")
                time.sleep(RETRY_DELAY)
                continue

            metadata_json = json.loads(metadata_raw.string)

            law_id_raw = metadata_json.get("legislationIdentifier")
            if not law_id_raw:
                logging.error(f"Không có law_id: {url}")
                print(f"[FAIL] {url} - không có law_id, retry {attempt}/{MAX_RETRY}")
                time.sleep(RETRY_DELAY)
                continue

            law_id = law_id_raw.replace("/", "-")

            # Extract title, date
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

            return True  # thành công

        except Exception as e:
            logging.error(f"Lỗi xử lý {url}: {e}")
            print(f"[ERROR] {url} - {e}, retry {attempt}/{MAX_RETRY}")
            time.sleep(RETRY_DELAY)

    print(f"[GIVE UP] {url} sau {MAX_RETRY} lần thử")
    return False  # thất bại sau nhiều lần thử


def main():
    with open("../BTTH3/data/raw/law_links.json", "r", encoding="utf-8") as f:
        data = json.load(f)
        print(f"Tổng số links cần xử lý: {len(data)}")

    # Filter bỏ dự thảo
    filtered_data = [url for url in data if "du-thao" not in url]
    print(f"Số links sau khi bỏ dự thảo: {len(filtered_data)}")

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36",
        "Referer": "https://luatvietnam.vn/",
        "Origin": "https://luatvietnam.vn",
        "Cookie": "MUID=...",
    }

    logging.basicConfig(filename="../BTTH3/log/failed_access_links.log", level=logging.ERROR)

    global rate_limit_delay
    rate_limit_delay = 1.5  # delay 1.5s giữa các request

    success_count, fail_count = 0, 0

    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(process_url, url, headers): url for url in filtered_data}
        for future in as_completed(futures):
            url = futures[future]
            try:
                result = future.result()
                if result:
                    success_count += 1
                else:
                    fail_count += 1
            except Exception as e:
                logging.error(f"[EXCEPTION] {url} - {e}")
                print(f"[EXCEPTION] {url} - {e}")
                fail_count += 1

    print(f"\n✅ Hoàn tất: {success_count} thành công, {fail_count} thất bại")


if __name__ == "__main__":
    main()
