import os
import sys
import re
import time
import json
import logging
from typing import Dict, Any, List
from pydantic import BaseModel, Field
from openai import OpenAI

# Add the project root to sys.path so we can import from 'src'
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.config import settings
from src.db.qdrant_store import QdrantStore
from src.db.bm25_index import BM25Index
from src.db.default_data import DEFAULT_QA_DATA
from src.core.rag import RAGPipeline

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Quota constants
# Groq Free Tier has generous limits compared to Gemini Free Tier
# We can sleep briefly to be polite, but 30s is no longer needed.
# ---------------------------------------------------------------------------
INTER_QUERY_SLEEP_S = 1

# Define Golden Dataset
GOLDEN_DATASET = [
    {
        "query": "How do I merge two dictionaries in Python?",
        "ground_truth": "Use the | operator in Python 3.9+ (e.g. dict1 | dict2) or dictionary unpacking ** in Python 3.5+ (e.g. {**dict1, **dict2})."
    },
    {
        "query": "What is the difference between append and extend on a list?",
        "ground_truth": "append() adds the argument as a single element to the end of the list. extend() iterates over the argument and adds each element to the list."
    },
    {
        "query": "How do I read a file line by line in Python into a list?",
        "ground_truth": "Open the file with a context manager (with open) and use a list comprehension with line.strip() to read it line-by-line."
    },
    {
        "query": "How do I convert a string to datetime in Python?",
        "ground_truth": "Use the datetime.strptime(date_string, format_string) function from the datetime module."
    },
    {
        "query": "What does the yield keyword do in Python?",
        "ground_truth": "yield is used in generator functions. It pauses function execution and returns a value to the caller, retaining the function state for subsequent iterations."
    },
    {
        "query": "How do I check if a list is empty in Python?",
        "ground_truth": "The PEP 8 recommended way is to check the list's truthiness directly: if not my_list, because empty collections evaluate to False."
    },
    {
        "query": "How do I create a list compression / list comprehension in Python?",
        "ground_truth": "Use the bracket syntax with an expression and loop: [expression for item in iterable if condition]."
    },
    {
        "query": "How to write a decorator in Python?",
        "ground_truth": "A decorator is a function that takes another function, wraps it to extend its behavior, and returns the wrapper function."
    }
]


class JudgeEvaluation(BaseModel):
    faithfulness_score: float = Field(description="Score from 0.0 (contains hallucinations) to 1.0 (fully grounded in context).")
    relevance_score: float = Field(description="Score from 0.0 (irrelevant to query) to 1.0 (directly answers the query).")
    explanation: str = Field(description="Brief explanation of the scores given.")


class RAGEvaluator:
    def __init__(self):
        self.openai_client = OpenAI(
            base_url="https://api.cerebras.ai/v1",
            api_key=settings.CEREBRAS_API_KEY,
            timeout=60.0,
            max_retries=3,
        )
        self.model_name = "gpt-oss-120b"

    def evaluate_response(self, query: str, context: str, answer: str, ground_truth: str) -> JudgeEvaluation:
        """Uses Cerebras as a Judge to evaluate Faithfulness and Answer Relevance."""
        prompt = (
            f"You are an expert AI Evaluator grading a RAG Q&A Assistant response.\n\n"
            f"USER QUERY:\n{query}\n\n"
            f"RETRIEVED CONTEXT:\n{context}\n\n"
            f"GENERATED ANSWER:\n{answer}\n\n"
            f"GROUND TRUTH REFERENCE:\n{ground_truth}\n\n"
            f"Please grade the GENERATED ANSWER on two metrics:\n"
            f"1. Faithfulness (Groundedness): Is the answer derived ONLY from the context without fabricating information?\n"
            f"2. Answer Relevance: Does the answer directly address the user query and align with the ground truth?\n\n"
            f"Output strictly a JSON string matching this schema: {{\"faithfulness_score\": float, \"relevance_score\": float, \"explanation\": str}}"
        )

        max_retries = 3
        delay = 2
        for attempt in range(max_retries):
            try:
                response = self.openai_client.chat.completions.create(
                    model=self.model_name,
                    messages=[
                        {"role": "system", "content": "You are a precise evaluator. Always output only valid JSON, without any markdown formatting blocks."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.0,
                )
                raw_json = response.choices[0].message.content
                # Parse cleanly even if it contains backticks
                if "```json" in raw_json:
                    raw_json = raw_json.split("```json")[1].split("```")[0]
                elif "```" in raw_json:
                    raw_json = raw_json.split("```")[1].split("```")[0]
                data = json.loads(raw_json.strip())
                return JudgeEvaluation(**data)
            except Exception as e:
                err_str = str(e)
                if "429" in err_str or "rate limit" in err_str.lower():
                    logger.warning(f"Rate limit hit on judge call. Waiting {delay}s (attempt {attempt+1}/{max_retries})...")
                    time.sleep(delay)
                    delay *= 2
                else:
                    logger.error(f"Non-rate-limit error calling evaluator judge: {e}")
                    break

        logger.error("Judge evaluation failed after all retries. Returning N/A scores.")
        return JudgeEvaluation(
            faithfulness_score=0.0,
            relevance_score=0.0,
            explanation="EVALUATION FAILED: All retry attempts exhausted due to API errors."
        )


def main():
    logger.info("Starting Golden Dataset Evaluation Harness...")
    logger.info(
        f"API budget: 2 LLM calls/query × {len(GOLDEN_DATASET)} queries = "
        f"{2 * len(GOLDEN_DATASET)} total calls (Free Tier daily limit: 20)."
    )

    # Initialize index and pipeline
    qdrant_store = QdrantStore()
    bm25_index = BM25Index()

    # Ensure indexes are populated (use default data)
    collections_info = qdrant_store.client.get_collection(qdrant_store.collection_name)
    if collections_info.points_count == 0:
        qdrant_store.index_documents(DEFAULT_QA_DATA)
    bm25_index.build_index(DEFAULT_QA_DATA)

    rag_pipeline = RAGPipeline(qdrant_store, bm25_index)
    evaluator = RAGEvaluator()

    evaluation_results = []

    for idx, item in enumerate(GOLDEN_DATASET):
        query = item["query"]
        ground_truth = item["ground_truth"]

        logger.info(f"[{idx+1}/{len(GOLDEN_DATASET)}] Evaluating: '{query}'")

        start_time = time.time()

        # 1. Retrieve context (embedding call — not counted against generateContent quota)
        contexts = rag_pipeline.hybrid_search(query, top_k=3)
        context_str = "\n\n".join([c["text"] for c in contexts])

        # 2. Generate Answer (LLM call #1 per query)
        rag_output = rag_pipeline.generate_answer(query, contexts)
        answer = rag_output["answer"]

        latency = (time.time() - start_time) * 1000.0

        # 3. LLM-as-a-Judge evaluation (LLM call #2 per query)
        #    NOTE: Guardrails (3rd LLM call) are intentionally skipped here to
        #    stay within the Free Tier daily limit of 20 generateContent requests.
        judge_scores = evaluator.evaluate_response(query, context_str, answer, ground_truth)

        evaluation_results.append({
            "index": idx + 1,
            "query": query,
            "answer": answer,
            "ground_truth": ground_truth,
            "faithfulness": judge_scores.faithfulness_score,
            "relevance": judge_scores.relevance_score,
            "explanation": judge_scores.explanation,
            "latency_ms": latency
        })

        # Rate-limit guard: sleep between queries (skip after the last one)
        if idx < len(GOLDEN_DATASET) - 1:
            logger.info(f"Sleeping {INTER_QUERY_SLEEP_S}s to respect Gemini Free Tier rate limits...")
            time.sleep(INTER_QUERY_SLEEP_S)

    # ------------------------------------------------------------------
    # Write evaluation results to markdown report
    # ------------------------------------------------------------------
    report_path = "test_results.md"

    avg_latency = sum(r["latency_ms"] for r in evaluation_results) / len(evaluation_results)
    avg_faithfulness = sum(r["faithfulness"] for r in evaluation_results) / len(evaluation_results)
    avg_relevance = sum(r["relevance"] for r in evaluation_results) / len(evaluation_results)

    md_content = f"""# Python Q&A Assistant - Evaluation Results

This document presents the evaluation of the Python Q&A Assistant RAG Pipeline on the **Golden Dataset** (8 diverse queries representing typical user questions).

## Executive Summary

- **Total Queries Tested**: {len(evaluation_results)}
- **Average Response Latency**: {avg_latency:.2f} ms
- **Average Faithfulness Score (LLM-as-a-Judge)**: {avg_faithfulness:.2f} / 1.00
- **Average Answer Relevance Score (LLM-as-a-Judge)**: {avg_relevance:.2f} / 1.00

---

## Evaluation Metric Definitions

1. **Faithfulness (Groundedness)**: Checks if the generated answer is strictly supported by the retrieved context. A score of `1.0` indicates zero hallucination.
2. **Answer Relevance**: Measures how well the generated answer addresses the question and aligns with the ground-truth standard.
3. **Self-RAG Guardrails**: Active in the production API pipeline; intentionally skipped during offline evaluation to conserve API quota.

---

## Detailed Test Logs

"""
    for r in evaluation_results:
        md_content += f"""### Query {r['index']}: {r['query']}

**Ground Truth Standard:**  
*{r['ground_truth']}*

**Generated Answer:**  
```
{r['answer']}
```

**Metrics:**
- **Response Latency**: {r['latency_ms']:.2f} ms
- **Faithfulness**: {r['faithfulness']:.2f}/1.0
- **Answer Relevance**: {r['relevance']:.2f}/1.0
- **Judge Review**: {r['explanation']}

---
"""

    with open(report_path, "w", encoding="utf-8") as f:
        f.write(md_content)

    logger.info(f"Evaluation report written to {report_path}")
    logger.info(f"Summary — Faithfulness: {avg_faithfulness:.2f} | Relevance: {avg_relevance:.2f} | Latency: {avg_latency:.0f}ms")


if __name__ == "__main__":
    main()
