````markdown
# Agent Tools Contract

File này định nghĩa **contract** cho các công cụ (tools) nội bộ mà Agent sẽ gọi tuần tự để thực hiện pipeline:
1. **Retrieve laws** – tìm luật liên quan
2. **Generate answer** – sinh câu trả lời
3. **Format citation** – định dạng và trích dẫn

Các tools được định nghĩa như API nội bộ với input/output schemas (Pydantic models) nhằm đảm bảo dữ liệu trao đổi thống nhất.

---

## 1. Retrieve Laws

### Mô tả
Tìm và lấy ra các điều luật phù hợp nhất với câu hỏi của người dùng.

### Hàm
```python
retrieve_laws(question: str, top_k: int) -> List[Chunk]
````

### Input Schema

```python
class Retrieve_tool_request(BaseModel):
    user_input: str  # Câu hỏi từ người dùng
    k: int = 5       # Số chunks luật cần lấy (top_k)
```

### Output Schema

```python
class Chunk(BaseModel):
    text: str
    meta: Dict[str, Any]  # Ví dụ: { "section_title": "Điều 34", "date": "2019-06-14" }

class Retrieve_tool_response(BaseModel):
    chunks: List[Chunk]
```

---

## 2. Generate Answer

### Mô tả

Sinh câu trả lời tự nhiên dựa trên câu hỏi và các chunks luật đã retrieve.

### Hàm

```python
generate_answer(question: str, chunks: List[Chunk]) -> str
```

### Input Schema

```python
class Generate_answer_tool_request(BaseModel):
    user_input: str
    chunks: Retrieve_tool_response
```

### Output Schema

```python
class Generate_answer_tool_response(BaseModel):
    answer: str
```

---

## 3. Format Citation

### Mô tả

Định dạng câu trả lời kèm theo các trích dẫn luật (citation).

### Hàm

```python
format_citation(answer: str, chunks: List[Chunk]) -> str
```

### Input Schema

```python
class Format_citation_tool_request(BaseModel):
    answer: str
    chunks: Retrieve_tool_response
```

### Output Schema

```python
class Format_citation_tool_response(BaseModel):
    formatted_answer: str  # câu trả lời kèm citation
```

---

## Data Flow

Agent sẽ orchestrate theo pipeline:

1. **Step 1**: `Retrieve_tool.retrieve_laws(req)`
   → Output: `Retrieve_tool_response(chunks=[...])`

2. **Step 2**: `Generate_answer_tool.generate_answer(req)`
   (dùng input = câu hỏi + chunks từ Step 1)
   → Output: `Generate_answer_tool_response(answer=...)`

3. **Step 3**: `Format_citation.format_citation(req)`
   (dùng input = answer từ Step 2 + chunks từ Step 1)
   → Output: `Format_citation_tool_response(formatted_answer=...)`

---

## Ví dụ

### Input

```json
{
  "user_input": "Người lao động có quyền nghỉ thai sản bao lâu?",
  "k": 3
}
```

### Output cuối cùng (formatted)

```json
{
  "formatted_answer": "Người lao động nữ được nghỉ thai sản 6 tháng. 

Các luật được trích dẫn:
- Điều 34 - 2019-06-14 
Trong trường hợp sinh đôi trở lên, ngoài thời gian nghỉ thai sản quy định tại khoản 1 Điều này, từ con thứ hai trở đi, người mẹ được nghỉ thêm 01 tháng cho mỗi con."
}
```

```
```
