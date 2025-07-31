### **`docs/api_search.md` – API Contract cho `/search`**

```md
# API Contract – `/search`

## 📍 Endpoint

```

POST /search

````

---

## Request Payload

```json
{
  "user_input": "Quyền sở hữu đất của con cái?",
  "k": 5
}
````

### 🔸 Tham số:

| Trường       | Kiểu dữ liệu | Bắt buộc | Mô tả                                          |
| ------------ | ------------ | -------- | ---------------------------------------------- |
| `user_input` | string       | ✅        | Câu hỏi hoặc truy vấn của người dùng           |
| `k`          | integer      | ❌        | Số lượng kết quả trả về (top-k). Mặc định là 5 |

---

## Success Response (200 OK)

```json
{
  "chunks": [
    {
      "chunk_id": "0",
      "text": "Nội dung luật hoặc đoạn trích...",
      "score": 0.421,
      "meta": {
        "law_id": "LD2013",
        "section_title": "Chương XII - Giải quyết tranh chấp đất đai",
        "date": "2013-11-29"
      }
    },
    {
      "chunk_id": "1",
      "text": "Nội dung khác...",
      "score": 0.5032,
      "meta": {
        "law_id": "GD2005",
        "section_title": "Điều 14 - Quản lý nhà nước về giáo dục",
        "date": "2005-06-14"
      }
    }
  ]
}
```

### 🔹 Trường hợp không có kết quả phù hợp:

```json
{
  "chunks": []
}
```

---

## Error Responses

### 1. Bad Request (400)

```json
{
  "error": "Missing required field: user_input"
}
```

**Nguyên nhân:** Không cung cấp `user_input` hoặc sai kiểu dữ liệu.

---

### 2. No Results (200, nhưng detail)

```json
{
  "detail": "No results found"
}
```

**Nguyên nhân:** Không có đoạn văn bản nào có độ tương đồng cao (score > 0.6).

---

### 3. Internal Server Error (500)

```json
{
  "error": "Vector search failed: [Chi tiết lỗi nội bộ]"
}
```

**Nguyên nhân:** Lỗi truy vấn ChromaDB, lỗi embedding, hoặc lỗi hệ thống.

---


### Cài đặt môi trường

```bash
conda env create -f envi.yml
conda activate testing
```


### Chạy dịch vụ

```bash
uvicorn app.retrieve:app --reload
```

* Truy cập tại: [http://localhost:8000/docs](http://localhost:8000/docs) để thử nghiệm trên Swagger UI.
* Tất cả logic chính nằm trong `app/retrieve.py`.

---

### Kiểm thử

```bash
pytest --cov=app --cov-report=term-missing
```

* Test nên được đặt tại `tests/`.

---

### Format & Lint

```bash
black --check .
isort --check-only .
flake8 .
pylint app/
```

* Để tự động fix:

```bash
black .
isort .
```


## Ví dụ API mẫu

```http
POST /search
```

### Body:

```json
{
  "user_input": "Thời hiệu khởi kiện tranh chấp đất đai là bao lâu?",
  "k": 5
}
```

### Response:

```json
{
  "chunks": [
    {
      "chunk_id": "0",
      "text": "Thời hiệu khởi kiện tranh chấp đất đai là 03 năm kể từ ngày phát sinh tranh chấp...",
      "score": 0.435,
      "meta": {
        "law_id": "LD2013",
        "section_title": "Giải quyết tranh chấp đất đai",
        "date": "2013-11-29"
      }
    }
  ]
}
```

```

