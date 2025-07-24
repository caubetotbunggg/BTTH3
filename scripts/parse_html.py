import json
import os

from bs4 import BeautifulSoup


def extract_loai_van_ban_va_linh_vuc(soup):
    docitem = soup.find("div", class_="docitem-13")
    if not docitem:
        return None, None

    p_tags = docitem.find_all("p")
    if len(p_tags) >= 2:
        loai_van_ban = p_tags[0].get_text(strip=True)
        linh_vuc = p_tags[1].get_text(strip=True)
        return loai_van_ban, linh_vuc
    elif len(p_tags) == 1:
        loai_van_ban = p_tags[0].get_text(strip=True)
        return loai_van_ban, None
    else:
        return None, None


def parse_luat_html(soup):
    parsed = []
    current_chuong = None
    current_dieu = None
    current_content = []
    waiting_for_docitem11 = False

    for tag in soup.find_all(class_=["docitem-2", "docitem-5", "docitem-11"]):
        if "docitem-2" in tag["class"]:
            if current_dieu:
                parsed.append(
                    {
                        "chuong": current_chuong,
                        "dieu": current_dieu,
                        "noi_dung": "\n".join(current_content).strip(),
                    }
                )
                current_dieu = None
                current_content = []
                waiting_for_docitem11 = False

            current_chuong = tag.get_text(strip=True)

        elif "docitem-5" in tag["class"]:
            if current_dieu:
                parsed.append(
                    {
                        "chuong": current_chuong,
                        "dieu": current_dieu,
                        "noi_dung": "\n".join(current_content).strip(),
                    }
                )
                current_content = []
                waiting_for_docitem11 = False

            current_dieu = tag.get_text(strip=True).split("\n")[0].strip()

            # Kiểm tra nếu tag này có <br> -> nội dung nằm ngay trong điều
            if tag.find("br"):
                parts = [s.strip() for s in tag.stripped_strings]
                if len(parts) > 1:
                    current_content = parts[1:]  # Bỏ tiêu đề điều
                    waiting_for_docitem11 = False
                else:
                    current_content = []
                    waiting_for_docitem11 = False
            else:
                current_content = []
                waiting_for_docitem11 = True

        elif "docitem-11" in tag["class"] and waiting_for_docitem11:
            current_content.append(tag.get_text(strip=True))

    # Flush điều cuối cùng nếu còn
    if current_dieu:
        parsed.append(
            {
                "chuong": current_chuong,
                "dieu": current_dieu,
                "noi_dung": "\n".join(current_content).strip(),
            }
        )

    return parsed


def main():
    # Đường dẫn đến thư mục chứa các file HTML và metadata
    html_dir = "../BTTH3/data/raw/html"
    meta_dir = "../BTTH3/data/raw/meta"

    # Tạo thư mục parsed nếu chưa tồn tại
    parsed_dir = "../BTTH3/data/raw/parsed"
    os.makedirs(parsed_dir, exist_ok=True)

    # Lặp qua từng file HTML trong thư mục
    for filename in os.listdir(html_dir):
        if filename.endswith(".html"):
            law_id = filename.replace(".html", "")

            html_path = os.path.join(html_dir, f"{law_id}.html")
            meta_path = os.path.join(meta_dir, f"{law_id}_meta.json")
            output_path = os.path.join(parsed_dir, f"{law_id}.json")

            if not os.path.exists(meta_path):
                print(f"Không tìm thấy metadata cho {law_id}")
                continue

            with open(meta_path, "r", encoding="utf-8") as f:
                metadata = json.load(f)

            # Trích loại văn bản, lĩnh vực và nội dung
            with open(html_path, "r", encoding="utf-8") as f:
                soup = BeautifulSoup(f, "html.parser")
            loai_van_ban, linh_vuc = extract_loai_van_ban_va_linh_vuc(soup)
            parsed_noi_dung = parse_luat_html(soup)

            # Gộp metadata và nội dung đã parse
            combined = {
                **metadata,
                "loai_van_ban": loai_van_ban or "None",
                "linh_vuc": linh_vuc or "None",
                "noi_dung": parsed_noi_dung,
            }

            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(combined, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()
