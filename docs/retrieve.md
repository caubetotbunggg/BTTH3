# 📘 API Contract – `/retrieve`


## 📍 Endpoint

```
POST /retrieve
```

---

## 📩 Request Payload

```json
{
  "question": "Quyền sở hữu đất của con cái?",
  "top_k": 5
}
```

### 🔸 Tham số:

| Trường     | Kiểu dữ liệu | Bắt buộc | Mô tả                                          |
| ---------- | ------------ | -------- | ---------------------------------------------- |
| `question` | string       | ✅        | Câu hỏi của người dùng cần truy vấn thông tin. |
| `top_k`    | integer      | ❌        | Số lượng chunk kết quả trả về (mặc định: 5).   |

---

## ✅ Success Response (200 OK)

```json
{
  "chunks": [
    {
      "chunk_id": "chunk_001",
      "text": "...",
      "score": 0.xx,
      "meta": {
        "law_id": "...",
        "section_title": "..."
      }
    },
    {
      "chunk_id": "chunk_002",
      "text": "...",
      "score": 0.xx,
      "meta": {
        "law_id": "...",
        "section_title": "..."
      }
    }
  ]
}
```

### 🔹 Trường hợp không có kết quả:

```json
{
  "chunks": []
}
```

---

## ❌ Error Responses

### 1. Bad Request (400)

```json
{
  "error": "Missing required field: question"
}
```

**Nguyên nhân:** Thiếu `question` trong payload hoặc kiểu dữ liệu sai.

---

### 2. Internal Server Error (500)

```json
{
  "error": "An unexpected error occurred. Please try again later."
}
```

**Nguyên nhân:** Lỗi xử lý nội bộ trên server (lỗi model, vector store, etc.).

---


# 🧠 Retrieve Service
## 📦 Cài đặt
Bạn có thể setup môi trường theo 2 cách: dùng Conda (envi.yml) hoặc pip (requirements.txt).

🔹 Cách 1: Dùng Conda (Khuyên dùng)

conda env create -f envi.yml
conda activate testing
🔹 Cách 2: Dùng pip

python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

## 🚀 Chạy dịch vụ

uvicorn app.retrieve:app --reload
Truy cập tại: http://localhost:8000/docs để xem Swagger UI.

Tất cả route đều nằm trong app/retrieve.py.

## 🧪 Kiểm thử

pytest --cov=app --cov-report=term-missing
Test cases nên được đặt trong thư mục tests/ theo chuẩn pytest.

## 🧼 Kiểm tra định dạng & lint

black --check .
isort --check-only .
flake8 .
pylint app/
Để tự động fix định dạng:
black .
isort .

## 🔁 CI Integration (GitHub Actions)

File CI: .github/workflows/retrieve.yml

Workflow bao gồm:
Kiểm tra format với black, isort, flake8, pylint.
Chạy test với pytest, báo coverage.

# .github/workflows/retrieve.yml
name: Retrieve CI

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt

      - name: Lint and Format Check
        run: |
          black --check .
          isort --check-only .
          flake8 .
          pylint app/

      - name: Run tests
        run: |
          pytest --cov=app --cov-report=term-missing

## 📬 API mẫu

http
POST /retrieve
```json
{
  "user_input": "Thời hiệu khởi kiện tranh chấp đất đai là bao lâu?"
}
```

Response:
```json
{
  "results": [
    {
      "score": 0.8943,
      "metadata": {
        "title": "Luật Đất đai 2013",
        "chuong": "Chương XII",
        "tieu_de": "Giải quyết tranh chấp đất đai",
        "khoan": "1",
        "noi_dung": "Thời hiệu khởi kiện tranh chấp đất đai là 03 năm..."
      }
    }
  ]
```