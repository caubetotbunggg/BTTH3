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


