---
title: Python QA Assistant
emoji: 🐍
colorFrom: blue
colorTo: indigo
sdk: docker
pinned: false
---

# Python Programming Q&A Assistant

**🚀 Live Deployed App URL:** [https://huggingface.co/spaces/Zee2912/Python_QA_Assistant](https://huggingface.co/spaces/Zee2912/Python_QA_Assistant)

An AI-powered, production-grade retrieval-augmented generation (RAG) assistant designed to help data science learners get accurate, grounded answers to their Python questions.

This repository was built for the **Analytics Vidhya AI Engineer Take-Home Assessment**. It features hybrid retrieval (Dense Vector + Sparse Keyword search), Reciprocal Rank Fusion (RRF), real-time Self-RAG groundedness guardrails, and an automated evaluation harness.

---

## 🌟 Key Features

* **Hybrid Search (Dense + Sparse)**: Combines semantic search (powered by Qdrant and Gemini Embeddings) with keyword search (BM25) to accurately match conceptual queries and exact syntax symbols.
* **Reciprocal Rank Fusion (RRF)**: Merges rankings from dense and sparse retrievers using a mathematically robust ranking fusion algorithm.
* **Automated Evaluation Harness**: Includes an offline pipeline to test and evaluate the system against a Golden Dataset of 8+ complex Python queries, measuring Faithfulness, Relevance, and Latency.
* **Production-Grade API**: Built on FastAPI with asynchronous endpoints, structured JSON logging (`structlog`), CORS security, and comprehensive OpenAPI docs.
* **Zero-Configuration Run**: Automatically indexes a default high-quality Python QA dataset if the databases are empty on startup, making the project instantly testable out of the box.

---

## 🗺️ System Architecture

```
                    +-----------------------------+
                    |         User Client         |
                    +--------------+--------------+
                                   | POST /api/v1/ask
                                   v
                    +--------------+--------------+
                    |     FastAPI Web Service     |
                    +--------------+--------------+
                                   |
                                   v
                    +--------------+--------------+
                    |       Hybrid Searcher       |
                    +-------+-------------+-------+
                            |             |
            +---------------+             +---------------+
            | (Dense Search)              | (Sparse Search)
            v                             v
     +------+------+               +------+------+
     |  Qdrant DB  |               |  BM25 Index  |
     +------+------+               +------+------+
            |                             |
            +---------------+-------------+
                            | Reciprocal Rank Fusion (RRF)
                            v
                    +--------------+--------------+
                    |   Cerebras RAG Generator    |
                    +--------------+--------------+
                                   |
                                   v
                    +--------------+--------------+
                    |     Self-RAG Guardrail      |
                    +--------------+--------------+
                                   | Response & Sources
                                   v
                            [User Client]
```

---

## 🚀 Getting Started

### 1. Prerequisites
- Python 3.10 or higher installed.
- A **Cerebras API Key**. Get one from [Cerebras Inference](https://inference.cerebras.ai/).

### 2. Installation & Environment Setup
Clone the repository and navigate to the project directory:
```bash
git clone <your-repo-url>
cd python-qa-assistant
```

Create a virtual environment and activate it:
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

Install the dependencies:
```bash
pip install -r requirements.txt
```

Create your configuration environment file:
```bash
cp .env.example .env
```
Open `.env` and fill in your `CEREBRAS_API_KEY`:
```env
CEREBRAS_API_KEY=csk-...
```

### 3. Running the FastAPI Server
Start the local development server:
```bash
uvicorn src.main:app --reload
```
Once started, open your browser and navigate to:
- **Interactive API Documentation**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **Alt Docs (ReDoc)**: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

---

## 🛠️ Ingestion & Preprocessing

The system runs in **Demo Mode** out of the box by using a precompiled set of high-quality Stack Overflow Python posts.

To index the full Kaggle **Stack Overflow - Python Questions & Answers** dataset:
1. Download the dataset from [Kaggle](https://www.kaggle.com/datasets/stackoverflow/pythonquestions).
2. Extract and place `Questions.csv` and `Answers.csv` inside a directory named `data/` in the root folder.
3. Preprocess the dataset to extract high-score, cleaned Q&A pairs:
   ```bash
   python scripts/preprocess.py
   ```
4. Index the cleaned Q&A data into Qdrant:
   ```bash
   python scripts/index_data.py
   ```

---

## 🧪 Testing & Evaluation

### 1. Run Unit & Integration Tests
We use `pytest` for codebase testing:
```bash
pytest
```

### 2. Run the Evaluation Harness
Evaluate the RAG pipeline against the **Golden Dataset** (8+ diverse Python queries). The script measures Faithfulness and Relevance using LLM-as-a-judge, outputs logs to the terminal, and compiles a comprehensive report:
```bash
python scripts/evaluate.py
```
This generates the [test_results.md](test_results.md) file in the root directory detailing the quality audit.

---

## 🐳 Deployment (Docker & Hugging Face Spaces)

The application is fully containerized.

### Run Locally with Docker Compose
To build and spin up the FastAPI service along with a dedicated Qdrant database:
```bash
docker-compose up --build
```
The API will be accessible at [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs).

### Deploy to Hugging Face Spaces (Docker Space)
1. Create a new Space on [Hugging Face](https://huggingface.co/spaces) and select **Docker** as the SDK.
2. Choose the **Blank** template.
3. In your Space Settings, add your `CEREBRAS_API_KEY` under **Variables and Secrets**.
4. Push this repository's codebase to your Hugging Face Space repository.
5. Hugging Face will automatically build the `Dockerfile` and run the service.

* **Live Deployed App URL**: `https://huggingface.co/spaces/<your-username>/<your-space-name>` (or your Render URL)

---

## 📂 Project Structure

```
python-qa-assistant/
├── .github/workflows/ci.yml       # GitHub Actions for automated linting & testing
├── src/
│   ├── __init__.py
│   ├── config.py                 # Pydantic Settings env loader
│   ├── main.py                   # FastAPI application config & lifespan
│   ├── core/
│   │   ├── __init__.py
│   │   ├── rag.py                # Hybrid Search + RRF + Cerebras Pipeline
│   │   └── guardrails.py         # Self-RAG groundedness auditor
│   ├── db/
│   │   ├── __init__.py
│   │   ├── qdrant_store.py       # Qdrant Vector DB Client (in-memory/remote)
│   │   ├── bm25_index.py         # BM25 Index wrapper
│   │   └── default_data.py       # Embedded Python QA dataset (Demo Mode)
│   └── api/
│       ├── __init__.py
│       ├── router.py             # FastAPI API endpoints
│       └── schemas.py            # Pydantic Request/Response validation models
├── tests/
│   ├── __init__.py
│   ├── test_api.py               # Integration routes tests
│   └── test_rag.py               # Unit algorithms tests
├── scripts/
│   ├── preprocess.py             # Stack Overflow CSV parser
│   ├── index_data.py             # Vector store populate script
│   └── evaluate.py               # Golden Dataset evaluation harness
├── .env.example
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── test_results.md               # Compiled evaluation metrics and logs
├── slide_deck.md                 # 10-slide architectural scaling deck
└── README.md
```
