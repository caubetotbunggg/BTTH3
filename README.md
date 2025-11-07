# README: API service (thư mục `app/`)

Mục tiêu: tài liệu này mô tả rõ ràng service API nằm trong `app/` — kiến trúc, luồng xử lý RAG, các công nghệ dùng, cấu hình cần thiết và cách chạy/debug.

## 1) Kiến trúc tổng quan

- Entry point: `app/main.py` — tạo FastAPI app, register router, lifecycle startup/shutdown và (tuỳ cấu hình) mount Gradio demo.
- Controllers (HTTP layer): `app/controllers/*.py` — nhận request, validate qua Pydantic, chuyển tiếp tới services, trả response.
- Services (business logic): `app/services/*.py` — xử lý retrieval, prompt-building, gọi LLM, và trả kết quả đã normalize.
- Models (DTOs): `app/models/*.py` — Pydantic models cho request/response (ví dụ: `RAGRequest`, `RAGResponse`, chunk schema).
- Config: `app/config/*.py` — `settings.py` (API keys, timeouts), `paths.py` (ROOT/DATA dirs), `tree_config.py` (chiến lược chọn chunk/tool sequence).
- Prompts: `app/prompts/*.txt` — template prompt dùng để feed LLM.

Thư mục cần chú ý: `app/services/retrieve_service.py` (tương tác với Weaviate / embedding), `app/services/rag_service.py` (tổng hợp retrieval + LLM), `app/controllers/rag_controller.py` (endpoint chính cho RAG flow).

## 2) Công nghệ chính

- Python 3.10 — runtime.
- FastAPI — framework HTTP, auto OpenAPI docs.
- Pydantic — validation/typing cho request & response.
- Weaviate — vector database cho nearest-neighbor/hybrid search.
- Embedding model (ví dụ `BGE-m3`) — tạo vector cho văn bản.
- LLM provider (cấu hình trong `app/config/settings.py`) — gọi model để sinh câu trả lời.
- Gradio — (tuỳ chọn) UI demo nếu mount trong `main.py`.

Phụ trợ: pytest cho testing. `app/requirements.txt` liệt kê các dependency cần cài.

## 3) Luồng logic chính (RAG flow) — step-by-step

1) Người dùng gửi yêu cầu tới endpoint RAG (ví dụ `POST /rag`) với payload chứa query + tuỳ chọn (top_k, temperature, ...).
2) `rag_controller` nhận request và validate bằng Pydantic model (`RAGRequest`).
3) `rag_service` thực hiện luồng:
   - Lấy cấu hình retrieval từ `tree_config.py` (quy tắc chọn tool, số lượng chunk, weights).
   - Gọi `retrieve_service.query(query, k, ...)` để lấy top-k candidate chunks từ Weaviate (vector + metadata + score). `retrieve_service` đảm bảo vector được truyền là object (không phải coroutine) và normalize kết quả.
   - Chọn & lọc chunks (dedupe, min-score threshold) theo config.
   - Xây prompt: chèn template từ `prompts/llm_prompt.txt`, chèn chunks đã lọc, và chèn user query + instruction.
   - Gọi LLM client với timeout và xử lý response an toàn: kiểm tra `choices` tồn tại, fallback nếu rỗng, và log raw output cho debug.
   - Tạo `RAGResponse` có trường: `answer` (string), `used_chunks` (list metadata), `sources` (citations), optional `debug` (raw LLM output, scores).
4) `rag_controller` trả response cho client (HTTP 200) hoặc lỗi chi tiết (4xx/5xx) khi cần.

Lưu ý vận hành: service đã có một số defensive checks để tránh lỗi như "list index out of range" khi LLM trả `choices=[]`. Nếu lỗi này tái diễn, khuyến nghị bật retry với exponential backoff trong hàm gọi LLM.

## 4) Endpoints chính (tổng quan)

- GET `/health` — health checks (gọi `health_service`).
- POST `/retrieve` — trả về candidate chunks (vector search result).
- POST `/rag` — endpoint chính: input `RAGRequest`, output `RAGResponse`.

Chi tiết schema: xem `app/models/rag_model.py`.

## 5) Biến môi trường & cấu hình quan trọng

Các biến thường dùng (có thể nằm trong `.env`):
- `WEAVIATE_URL` — URL Weaviate (host:port hoặc cloud host).
- `WEAVIATE_API_KEY` — API key cho Weaviate.
- `EMBEDDING_MODEL` — tên model embedding (nếu dùng remote/local encoder).
- `LLM_API_KEY` / `GROQ_API_KEY` / `GEMINI_API_KEY` — keys cho provider LLM.
- Timeout/settings có thể điều chỉnh trong `app/config/settings.py`.

Quan trọng: không commit API keys vào Git. Sử dụng secret store trong CI/CD.

## 6) Cách chạy (developer)

1) Cài dependency:

```bash
conda activate btth3
pip install -r app/requirements.txt
```

2) Bật dịch vụ phụ trợ (Weaviate) — ví dụ Docker Compose:

```bash
docker compose -f docker-compose-config.yaml up -d
```

3) Export biến môi trường cần thiết (ví dụ):

```bash
export WEAVIATE_URL="http://localhost:8080"
export WEAVIATE_API_KEY="..."
export EMBEDDING_MODEL="BGEm3"
export LLM_API_KEY="..."
```

4) Chạy FastAPI:

```bash
uvicorn app.main:app --reload
# OpenAPI: http://localhost:8000/docs
```

## 7) Kiểm tra & debugging nhanh

- Kiểm tra cú pháp trên `app/`:

```bash
python -m py_compile $(find app -name "*.py")
```

- Chạy tests liên quan:

```bash
pytest tests/test_rag.py -q
```

- Nếu LLM trả `choices=[]`:
  - Kiểm tra thời gian chờ (timeout) và logs raw LLM output trong `rag_service`.
  - Thêm retry/backoff cho gọi LLM.

## 8) Operational notes & cải tiến đề xuất

- Thêm exponential backoff & retry cho LLM calls trong `rag_service`.
- Viết integration tests mock cho Weaviate + LLM để chạy trong CI (nhanh, xác thực flow).
- Thêm monitoring/metrics (latency, error rate, LLM empty-response count).
