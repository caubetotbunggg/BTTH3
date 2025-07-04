import os

from bs4 import BeautifulSoup


def extract_text(html):
    soup = BeautifulSoup(html, "html.parser")
    soup = soup.find("div", class_="the-document-body ndthaydoi noidungtracuu")
    if not soup:
        return ""
    return soup.get_text(strip=True, separator="\n")


if __name__ == "__main__":
    os.makedirs("../BTTH3/data/processed/text", exist_ok=True)
    html_dir = "../BTTH3/data/raw/html"
    for file in os.listdir(html_dir):
        if file.endswith(".html"):
            with open(os.path.join(html_dir, file), "r", encoding="utf-8") as f:
                html_content = f.read()
                extracted = extract_text(html_content)
                base_name = os.path.splitext(file)[0]
                out_path = os.path.join(
                    "../BTTH3/data/processed/text", f"{base_name}.txt"
                )
                with open(out_path, "w", encoding="utf-8") as out_f:
                    out_f.write(extracted)
