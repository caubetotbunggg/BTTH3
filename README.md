# 📚 Legal Assistant - RAG System for Legal Document Retrieval

## 🧠 Project Overview

This project aims to build an end-to-end **Retrieval-Augmented Generation (RAG)** system tailored for **Vietnamese legal documents**. It provides users (students, lawyers, citizens) with **accurate** and **explainable** answers by retrieving relevant legal text chunks and prompting a language model (LLM).

---

## 📁 Repository Structure

```bash
.
├── app/                            # FastAPI app (main API, routers, services)
├── data/                           # Legal documents: raw, parsed, chunked, embeddings
├── docs/                           # Documentation (API specs, prompts, evaluations)
├── scripts/                        # Scripts for crawling, parsing, cleaning, chunking
├── tests/                          # Unit & integration tests
├── .github/workflows/              # CI/CD with GitHub Actions
├── environment.yml                 # Conda environment definition
├── docker-compose-config.yaml      # Docker Compose config (Weaviate, etc.)
├── README.md                       # Project overview and usage guide
└── ...
```

---

## 🚀 Quick Start

### 1. Set up Environment

```bash
# Create and activate environment
conda env create -f environment.yml
conda activate environment
```

### 2. Run Docker Services (Weaviate, etc.)

```bash
docker compose -f docker-compose-config.yaml up -d
```

> Ensure Docker is installed and running before executing this.

### 3. Run FastAPI Service

```bash
uvicorn app.main:app --reload
```

Access API docs at: [http://localhost:8000/docs](http://localhost:8000/docs)

### 4. Run Tests

```bash
pytest tests/
```

---

## 📦 Data & Indexing

### 📌 Embedding Model

We use the multilingual embedding model:

```
intfloat/multilingual-e5-small
```

### 🧠 Indexing with Weaviate

```python
collection.data.insert_many(
    [
        DataObject(
            uuid=generate_uuid5(f"{file_id}_{i}"),
            properties={"text": text, "metadata": metadata},
            vector=vector,
        )
        for i, (text, vector, metadata) in enumerate(
            zip(documents, vectors, metadatas)
        )
    ]
)
```

---

## 🔎 Retrieval Flow

### 1. Connect to Weaviate

```python
from weaviate import connect_to_local
from weaviate.classes.init import AdditionalConfig, Timeout

client = connect_to_local(
    host="localhost",
    port=8080,
    additional_config=AdditionalConfig(timeout=Timeout(query=60))
)
collection = client.collections.get("Document")
```

### 2. Hybrid Search Query

```python
results = collection.query.hybrid(
    query=user_input,
    vector=embedding,
    alpha=0.6,  # BM25 (text) vs vector balance
    return_metadata=MetadataQuery(score=True, explain_score=True),
    limit=k,
)
```

---

## 🔧 Retrieve Service

### ✅ Testing & Coverage

```bash
pytest --cov=app --cov-report=term-missing
```

This will print test coverage line-by-line in your terminal.


### 🧹 Code Quality with Pre-commit

This project uses [`pre-commit`](https://pre-commit.com/) to enforce code quality and formatting using:

* [`black`](https://github.com/psf/black) – Code formatter
* [`isort`](https://github.com/PyCQA/isort) – Import sorter
* [`flake8`](https://github.com/PyCQA/flake8) – Linter

#### ⚙️ Install and enable hooks:

```bash
# Install pre-commit
pip install pre-commit

# Set up the hooks locally
pre-commit install

# (Optional) Run checks on all files
pre-commit run --all-files
```

> These checks will run automatically before every commit.


---

## 📌 Conventions & Workflow Notes

* Follow [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/) (e.g., `feat:`, `fix:`, `refactor:`)
* Run `pre-commit install` to enforce code formatting and checks before commit
* Always update `manifest.csv` after crawling or processing new files
* Ensure Docker containers are up when testing the full retrieval pipeline

---

## 📜 License

© 2025 Legal Assistant RAG Project Team
This project is for research and educational purposes only.

