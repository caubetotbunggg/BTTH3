# Legal Assistant - RAG System for Legal Document Retrieval

## 🧠 Project Overview

This project aims to build an end-to-end Retrieval-Augmented Generation (RAG) system tailored to legal documents in Vietnam. It provides users (students, lawyers, citizens) with accurate and explainable answers by retrieving relevant legal text chunks and prompting an LLM.

## 📁 Repository Structure

```
.
├── app/                      # FastAPI app code
├── data/                     # Raw, parsed, processed legal data
├── docs/                     # Documentation (API, prompts, metrics...)
├── scripts/                  # Crawler, parser, cleaner, chunker, etc.
├── tests/                    # Unit & integration tests
├── .github/workflows/       # GitHub Actions CI/CD
├── environment.yml          # Conda environment definition
├── README.md                # Project overview and usage
└── ...
```


## 🚀 Quick Start

```bash
# Setup environment
conda env create -f environment.yml
conda activate environment

# Run service
uvicorn app.main:app --reload

# Run tests
pytest --cov=app tests/
```

## 🔍 Example API Call

```bash
curl -X POST http://localhost:8000/retrieve \
  -H "Content-Type: application/json" \
  -d '{"question": "Quy định về hợp đồng lao động", "top_k": 3}'
```

## RAG Module

### Endpoints

#### `POST /rag/retrieve`

* **Description:** Retrieve relevant documents from vector store.
* **Payload:**

```json
{
  "query": "giáo dục hòa nhập là gì?",
  "top_k": 5
}
```

* **Response:**

```json
{
    "chunk_id": "str",
    "text": "str",
    "score": "score",
    "meta": {
        "law_id": "str",
        "section_title": "str",
        "date": "date",
    },
}
```

#### `POST /rag/query`

* **Description:** Retrieve relevant documents and generate answer using LLM.
* **Payload:**

```json
{
  "query": "giáo dục hòa nhập là gì?",
  "top_k": 5
}
```

* **Response:**

```json
{
  "text": "Dựa vào ...",
}
```

---

### Examples

```bash
curl -X POST http://localhost:8000/rag \
  -H "Content-Type: application/json" \
  -d '{"query": "giáo dục hòa nhập là gì", "top_k": 3}'

---

### Limits

* **Timeout:**
  * LLM Completion: 15 seconds

Requests that exceed timeout or rate limits will receive:

```json
{
  "detail": "Hệ thống bận vui lòng thử lại sau."
}
```


## 📌 Notes

* Follow Conventional Commits (`feat:`, `fix:`, `test:`...)
* Use pre-commit to ensure formatting
* Update `manifest.csv` after crawling or parsing


---

© 2025 Legal Assistant RAG Project Team
