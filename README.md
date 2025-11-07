# README: API Service (app/ directory)

Objective: This document clearly describes the API service located in `app/` — architecture, RAG processing flow, technologies used, required configuration, and how to run/debug.

## 1) Overall Architecture

- Entry point: `app/main.py` — creates FastAPI app, registers routers, handles lifecycle startup/shutdown, and (optionally) mounts Gradio demo.
- Controllers (HTTP layer): `app/controllers/*.py` — receive requests, validate via Pydantic, forward to services, return responses.
- Services (business logic): `app/services/*.py` — handle retrieval, prompt-building, LLM calls, and return normalized results.
- Models (DTOs): `app/models/*.py` — Pydantic models for request/response (e.g., `RAGRequest`, `RAGResponse`, chunk schema).
- Config: `app/config/*.py` — `settings.py` (API keys, timeouts), `paths.py` (ROOT/DATA dirs), `tree_config.py` (chunk selection strategy/tool sequence).
- Prompts: `app/prompts/*.txt` — prompt templates used to feed LLM.

Key directories: `app/services/retrieve_service.py` (Weaviate/embedding interaction), `app/services/rag_service.py` (retrieval + LLM orchestration), `app/controllers/rag_controller.py` (main endpoint for RAG flow).

## 2) Core Technologies

- Python 3.10 — runtime.
- FastAPI — HTTP framework, auto OpenAPI docs.
- Pydantic — validation/typing for requests & responses.
- Weaviate — vector database for nearest-neighbor/hybrid search.
- Embedding model (e.g., `BGE-m3`) — creates vectors for text.
- LLM provider (configured in `app/config/settings.py`) — calls model to generate answers.
- Gradio — (optional) demo UI if mounted in `main.py`.

Supporting tools: pytest for testing. `app/requirements.txt` lists all dependencies.

## 3) Main Logic Flow (RAG flow) — Step-by-step

1) User sends request to RAG endpoint (e.g., `POST /rag`) with payload containing query + options (top_k, temperature, ...).
2) `rag_controller` receives request and validates using Pydantic model (`RAGRequest`).
3) `rag_service` executes the flow:
   - Gets retrieval config from `tree_config.py` (tool selection rules, chunk count, weights).
   - Calls `retrieve_service.query(query, k, ...)` to get top-k candidate chunks from Weaviate (vector + metadata + score). `retrieve_service` ensures vectors are objects (not coroutines) and normalizes results.
   - Selects & filters chunks (dedupe, min-score threshold) according to config.
   - Builds prompt: inserts template from `prompts/llm_prompt.txt`, adds filtered chunks, and includes user query + instructions.
   - Calls LLM client with timeout and handles response safely: checks if `choices` exists, fallback if empty, and logs raw output for debugging.
   - Creates `RAGResponse` with fields: `answer` (string), `used_chunks` (list of metadata), `sources` (citations), optional `debug` (raw LLM output, scores).
4) `rag_controller` returns response to client (HTTP 200) or detailed error (4xx/5xx) when needed.

Operational note: Service includes defensive checks to avoid errors like "list index out of range" when LLM returns `choices=[]`. If this error recurs, recommend enabling retry with exponential backoff in LLM call function.

## 4) Main Endpoints (Overview)

- GET `/health` — health checks (calls `health_service`).
- POST `/retrieve` — returns candidate chunks (vector search results).
- POST `/rag` — main endpoint: input `RAGRequest`, output `RAGResponse`.

Schema details: see `app/models/rag_model.py`.

## 5) Environment Variables & Important Configuration

Common variables (can be in `.env`):
- `WEAVIATE_URL` — Weaviate URL (host:port or cloud host).
- `WEAVIATE_API_KEY` — API key for Weaviate.
- `EMBEDDING_MODEL` — embedding model name (if using remote/local encoder).
- `LLM_API_KEY` / `GROQ_API_KEY` / `GEMINI_API_KEY` — keys for LLM provider.
- Timeout/settings can be adjusted in `app/config/settings.py`.

Important: Do not commit API keys to Git. Use secret store in CI/CD.

## 6) How to Run (Developer)

1) Install dependencies:
```bash
conda activate btth3
pip install -r app/requirements.txt
```

2) Start supporting services (Weaviate) — e.g., Docker Compose:
```bash
docker compose -f docker-compose-config.yaml up -d
```

3) Export required environment variables (example):
```bash
export WEAVIATE_URL="http://localhost:8080"
export WEAVIATE_API_KEY="..."
export EMBEDDING_MODEL="BGEm3"
export LLM_API_KEY="..."
```

4) Run FastAPI:
```bash
uvicorn app.main:app --reload
# OpenAPI: http://localhost:8000/docs
```

## 7) Quick Testing & Debugging

- Check syntax on `app/`:
```bash
python -m py_compile $(find app -name "*.py")
```

- Run related tests:
```bash
pytest tests/test_rag.py -q
```

- If LLM returns `choices=[]`:
  - Check timeout and review raw LLM output logs in `rag_service`.
  - Add retry/backoff for LLM calls.

## 8) Operational Notes & Suggested Improvements

- Add exponential backoff & retry for LLM calls in `rag_service`.
- Write integration tests with Weaviate + LLM mocks to run in CI (fast, validates flow).
- Add monitoring/metrics (latency, error rate, LLM empty-response count).