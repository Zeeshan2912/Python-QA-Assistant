# Presentation Slide Deck: Python Programming Q&A Assistant
**Analytics Vidhya AI Engineer Take-Home Assessment**  
*Candidate Presentation | Round 1*

---

## Slide 1: Executive Summary
### **Project Overview**
- **Goal**: Build an AI-powered, grounded Q&A Assistant to help data science learners get accurate answers to Python queries using Stack Overflow posts.
- **Key Achievements**:
  - Engineered a hybrid retrieval mechanism (Qdrant Dense + BM25 Sparse) combined with Reciprocal Rank Fusion (RRF).
  - Implemented real-time groundedness checks (Self-RAG Guardrails) to eliminate LLM hallucinations.
  - Built an automated evaluation harness with a Golden Dataset (8+ complex Python queries).
  - Designed a robust scale-out architecture for 100+ concurrent users.

---

## Slide 2: The Core Challenge
### **Retrieval & Hallucination Challenges in LLMs**
- **Semantic Overlap vs. Exact Syntax**: Standard dense vector search often misses exact code keywords or syntax symbols.
- **Hallucinations**: When answering coding questions, standard LLMs may confidently generate non-existent library parameters or syntax.
- **Resource Constraints**: High-performance RAG indexing of full Stack Overflow (10GB+ dataset) must run efficiently within serverless/free-tier constraints without lagging.
- **Groundedness**: Output must cite specific Stack Overflow discussions, ensuring the answer is audit-proven.

---

## Slide 3: System Architecture
```
                     +----------------------------+
                     |        User Client         |
                     +--------------+-------------+
                                    | POST /ask
                                    v
                     +--------------+-------------+
                     |    FastAPI Web Service     |
                     +--------------+-------------+
                                    |
                                    v
                     +--------------+-------------+
                     |      Hybrid Searcher       |
                     +-------+------------+-------+
                             |            |
             +---------------+            +---------------+
             | (Dense Search)             | (Sparse Search)
             v                            v
      +------+------+              +------+------+
      |   Qdrant    |              |  BM25 Index  |
      +------+------+              +------+------+
             |                            |
             +---------------+------------+
                             | Reciprocal Rank Fusion (RRF)
                             v
                     +--------------+-------------+
                     |   Cerebras RAG Generator   |
                     +--------------+-------------+
                                    |
                                    v
                     +--------------+-------------+
                     |    Self-RAG Guardrail      |
                     +--------------+-------------+
                                    | Response & Sources
                                    v
                             [User Client]
```

---

## Slide 4: Hybrid Search & Reciprocal Rank Fusion (RRF)
### **Why Hybrid Search?**
- **Dense Vector Search (Qdrant)**: Captures semantic meaning and intent (e.g., "dictionary merging").
- **Sparse Keyword Search (BM25)**: Captures exact syntax and keywords (e.g., `|`, `**`, `list.extend`).

### **Reciprocal Rank Fusion (RRF)**
- Integrates Dense and Sparse rankings without arbitrary score normalization:
  $$RRF\_Score(d) = \sum_{m \in M} \frac{1}{k + r_m(d)}$$
  *(where $k = 60$)*
- Ensures that documents ranked highly in *either* or *both* indices rise to the top of the LLM context pool.

---

## Slide 5: Generative Groundedness & Self-RAG Guardrails
### **1. Grounded Prompts**
- LLM is provided with contexts structured with source IDs: `[Source 1]`, `[Source 2]`.
- System instructions force strict adherence: *"Answer ONLY using the provided context. Cite sources using [Source X] format."*

### **2. Self-RAG Guardrail**
- Real-time audit executed via Cerebras JSON mode schema constraints.
- Evaluates:
  - **`is_grounded`**: (Boolean flag).
  - **`grounding_score`**: (0.0 to 1.0).
  - **`hallucinated_claims`**: Captures and details exact fabrications.
- Warnings or refined responses are triggered dynamically based on audit results.

---

## Slide 6: FastAPI Backend Production Hardening
### **Design Decisions & Best Practices**
- **Asynchronous Execution (`async/await`)**: Unblocks the event loop during network-bound LLM and database calls, maximizing CPU core efficiency.
- **Pydantic v2 Models**: Rigid validation of incoming question requests and outbound JSON responses.
- **Structured Logging (Structlog)**: Formats app logs as JSON strings, allowing easy indexing in monitoring systems (Grafana Loki, ELK stack).
- **Graceful Startup Ingestion**: The database dynamically indexes a high-quality QA dataset on startup if the database is empty, achieving a zero-setup out-of-the-box demo.

---

## Slide 7: Quality & Evaluation Harness
### **The Golden Dataset Evaluation**
- Developed `scripts/evaluate.py` to automate quality verification.
- **Golden Dataset**: 8 diverse Python questions mapped to ground-truth answers.
- **LLM-as-a-Judge**: A separate Cerebras evaluation call scores two key metrics:
  1. **Faithfulness**: Checks if the response is fully grounded in the retrieved context.
  2. **Answer Relevance**: Checks if the response addresses the user query.
- **Execution Report**: Outputs `test_results.md` showing latency, scores, and judge critiques.

---

## Slide 8: Scaling to 100+ Concurrent Users
### **Production Architecture Blueprint**

```
+------------+     +-------------------+     +-----------------+
|   Client   | --> |  Nginx / ALB LB   | --> |  FastAPI Pods   | (K8s Horizontal Pod Autoscaler)
+------------+     +-------------------+     +--------+--------+
                                                      |
                                     +----------------+---------------+
                                     |                                |
                                     v                                v
                           +---------+---------+            +---------+---------+
                           |    Redis Cache    |            |  Qdrant DB Cluster |
                           | (Exact & Semantic)|            | (Distributed Raft)|
                           +-------------------+            +-------------------+
```

### **Stateless FastAPI Workers**
- Deploy stateless FastAPI pods inside Kubernetes, managed by a Horizontal Pod Autoscaler (HPA) scaling on CPU/Memory usage.
- Run async workers under Gunicorn/Uvicorn to process multiple requests concurrently without blocking threads.

---

## Slide 9: Scaling Storage & Caching
### **1. Vector Database Scaling (Qdrant)**
- Deploy Qdrant in **Distributed Mode** (cluster with multiple nodes using Raft consensus).
- Use **Payload Indexing** and **HNSW segment partitioning** to guarantee sub-10ms dense search lookups across millions of vectors.
- Implement read replicas to handle high read volumes.

### **2. Caching Tier (Redis)**
- **Exact Query Cache**: Store previous answers matching exact queries (TTL 1 hour) for instant O(1) response times.
- **Semantic Cache**: Store query embeddings in Redis. If a new query is highly similar (Cosine Distance > 0.95) to a cached query, return the cached answer, bypassing the LLM pipeline completely.
  - **Impact**: Reduces LLM API latency from ~1.5s to <50ms and saves API costs.

---

## Slide 10: Cost & Observability
### **1. Cost Management**
- Bypassing LLM generation with **Redis Semantic Cache** reduces token usage by 40-60% in high-traffic settings.
- Using compact embedding models and batching embeddings reduces token overhead.
- Utilize inference providers (e.g. Cerebras Llama) with fast, cheap tiering to keep costs linear to traffic.

### **2. Production Observability**
- **Tracing**: Implement OpenTelemetry (Jaeger/AWS X-Ray) to track trace spans across API, retrieval, and LLM calls to detect latency bottlenecks.
- **Logging**: Collect structured logs into ELK or Datadog.
- **Alerting**: Set up Prometheus metrics monitoring HTTP error rates (5xx) and latency percentiles (p95, p99).
