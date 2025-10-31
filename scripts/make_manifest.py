import csv
import os
from app.config.paths import RAW_DIR


def get_ids(folder, extension):
    list_ids = []
    for f in os.listdir(folder):
        if f.endswith(extension):
            list_ids.append(os.path.splitext(f)[0])
    return list_ids


html_folder = RAW_DIR / "html"
parsed_folder = RAW_DIR / "parsed"
manifest_path = RAW_DIR / "manifest.csv"

html_ids = set(get_ids(html_folder, ".html"))
parsed_ids = set(get_ids(parsed_folder, ".json"))

all_ids = html_ids.union(parsed_ids)

RAW_DIR.mkdir(parents=True, exist_ok=True)

with open(manifest_path, "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(["law_id", "html_exists", "parsed_exists", "status"])

    for id in sorted(all_ids):
        has_html = id in html_ids
        has_parsed = id in parsed_ids

        if has_html and has_parsed:
            status = "ok"
        elif has_html:
            status = "missing_parsed"
        elif has_parsed:
            status = "missing_html"
        else:
            status = "missing_both"

        writer.writerow([id, has_html, has_parsed, status])
