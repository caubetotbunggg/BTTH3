# 🧰 Agent Tools & API Contract

## 🎯 Mục đích

Tài liệu này định nghĩa rõ ràng 3 công cụ (tools) mà Agent sử dụng để thực hiện chuỗi xử lý (pipeline). Mỗi công cụ sẽ có mô tả chức năng, input/output schema và định nghĩa bằng Pydantic model để dễ dàng tích hợp vào hệ thống hoặc sử dụng với OpenAI Function / Gemini Tool Call.

---

## 📌 Tổng quan các Tools

| Tool Name         | Input                | Output       | Mục đích chính                                          |
| ----------------- | -------------------- | ------------ | ------------------------------------------------------- |
| `retrieve_laws`   | `question`, `top_k`  | List\[Chunk] | Truy vấn thông tin liên quan từ bộ luật                 |
| `generate_answer` | `question`, `chunks` | str          | Sinh câu trả lời dựa trên câu hỏi và các đoạn liên quan |
| `format_citation` | `answer`, `chunks`   | str          | Trích dẫn rõ nguồn của từng phần trong câu trả lời      |

---

## 🔍 1. Tool: `retrieve_laws`

### Mô tả:

Tìm các đoạn văn bản luật (chunks) phù hợp với câu hỏi.

### Input Schema:

```python
from pydantic import BaseModel

class RetrieveLawsInput(BaseModel):
    question: str
    top_k: int = 5  # Số lượng chunk muốn lấy ra
```

### Output Schema:

```python
class ChunkMetadata(BaseModel):
    doc_id: str
    section_title: str
    article_number: str
    url: str

class Chunk(BaseModel):
    text: str
    meta: ChunkMetadata
```

### Output type:

```python
List[Chunk]
```

---

## ✍️ 2. Tool: `generate_answer`

### Mô tả:

Sinh câu trả lời phù hợp dựa trên câu hỏi và các đoạn luật liên quan.

### Input Schema:

```python
class GenerateAnswerInput(BaseModel):
    question: str
    chunks: List[Chunk]
```

### Output Schema:

```python
class GenerateAnswerOutput(BaseModel):
    answer: str
```

---

## 📚 3. Tool: `format_citation`

### Mô tả:

Tạo trích dẫn rõ ràng trong câu trả lời, để người dùng biết thông tin đến từ đâu.

### Input Schema:

```python
class FormatCitationInput(BaseModel):
    answer: str
    chunks: List[Chunk]
```

### Output Schema:

```python
class FormatCitationOutput(BaseModel):
    cited_answer: str  # Ví dụ: "Theo [Điều 5, Luật Giao thông 2008], ..."
```

---

## ✅ Tổng kết

Tài liệu này định nghĩa cách Agent giao tiếp với các công cụ nội bộ một cách rõ ràng, nhằm phục vụ các use-case như:

* Tích hợp LLM function call
* Thay thế tool độc lập khi cần
* Debug, log hoặc trace dễ dàng qua schema

---

