# Hướng dẫn cập nhật index (`update_index.py`)

Quy trình này thực hiện embedding và index các file luật mới vào Weaviate.

## 1. Cấu trúc thư mục dữ liệu

| Thư mục / File                   | Mô tả                                   |
| -------------------------------- | --------------------------------------- |
| `data/processed/chunks/new/`     | Chứa các file chunk JSON cần nhúng      |
| `data/raw/html/new/`             | Chứa metadata tương ứng (`*_meta.json`) |
| `data/processed/embeddings/new/` | Nơi lưu embedding đã tạo (`.npy`)       |
| `log/update_embedding_error.log` | Ghi log lỗi khi index                   |

---

## 2. Quy trình chính

1. **Tải model**: từ biến môi trường `.env` (`EMBEDDING_MODEL`)
2. **Kết nối Weaviate**: tới collection `"Document"` (đã tồn tại)
3. **Duyệt qua các file chunk mới**:

   * Đọc nội dung và metadata
   * Ghép đoạn văn phù hợp (bao gồm khoản nếu có)
   * Nhúng văn bản thành vector (dùng SentenceTransformer)
   * Lưu vector ra file `.npy`
   * Gửi từng đoạn + vector vào Weaviate cùng metadata

---

## 3. Xử lý lỗi

* Nếu thiếu metadata hoặc file trống → bỏ qua
* Lỗi khi insert → ghi vào `log/update_embedding_error.log`

---

## 4. Kết thúc

Tự động đóng kết nối sau khi hoàn tất.

---

## Ghi chú

* Yêu cầu thư viện: `weaviate`, `sentence-transformers`, `numpy`, `tqdm`, `dotenv`
* Tránh duplicate ID bằng UUID (`generate_uuid5`)
* Thích hợp dùng cho cập nhật định kỳ hoặc batch nhỏ

---
