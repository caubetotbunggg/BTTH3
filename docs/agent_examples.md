````markdown
# Agent Endpoint Examples

## Happy Path

**Request:**

```bash
curl -X POST "http://localhost:8000/agent" \
  -H "Content-Type: application/json" \
  -d '{
        "user_input": "Điều luật về giáo dục hòa nhập là gì?",
        "k": 3,
        "max_steps": 3,
        "timeout_sec": 10
      }'
````

**Response:**

```json
{
  "status": "ok",
  "steps_executed": [
    {"step": 1, "result": ["laws"]},
    {"step": 2, "result": ["answer", "laws"]},
    {"step": 3, "result": ["formatted", "laws", "answer"]}
  ],
  "laws": {
    "chunks": {
      "chunks": [
        {
          "chunk_id": "c1",
          "text": "Điều 1: Quy định chung về giáo dục hòa nhập",
          "score": 0.95,
          "meta": {
            "law_id": "L01",
            "title": "Điều 1",
            "date": "2020-01-01"
          }
        }
      ]
    }
  },
  "answer": {
    "answer": "Giáo dục hòa nhập là..."
  },
  "formatted": {
    "formatted_answer": "Giáo dục hòa nhập là...\n\nCác luật được trích dẫn:\n- Điều 1 - 2020-01-01 \nĐiều 1: Quy định chung về giáo dục hòa nhập"
  }
}
```

## Timeout Example

**Request:**

```bash
curl -X POST "http://localhost:8000/agent" \
  -H "Content-Type: application/json" \
  -d '{
        "user_input": "Một câu hỏi rất dài",
        "k": 3,
        "max_steps": 3,
        "timeout_sec": 1
      }'
```

**Response:**

```json
{
  "error": "Step 2 timed out after 1s"
}
```


