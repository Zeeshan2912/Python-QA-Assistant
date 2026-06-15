import re
import json
import logging
import time
import requests
from typing import List, Dict, Any, Tuple, Optional
from src.config import settings
from src.db.qdrant_store import QdrantStore
from src.db.bm25_index import BM25Index

logger = logging.getLogger(__name__)

CEREBRAS_API_URL = "https://api.cerebras.ai/v1/chat/completions"
# Current Cerebras public API models (from official model catalog)
FREE_MODELS = [
    "gpt-oss-120b",   # Production model: OpenAI GPT OSS 120B ~3000 tok/s
    "zai-glm-4.7",   # Preview model: Z.ai GLM 4.7 355B ~1000 tok/s
]


def call_llm(messages: List[Dict], temperature: float = 0.2, max_tokens: int = 1500) -> str:
    """Call Cerebras API with model fallback for 429 rate limits."""
    headers = {
        "Authorization": f"Bearer {settings.CEREBRAS_API_KEY}",
        "Content-Type": "application/json",
    }

    for model in FREE_MODELS:
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        try:
            logger.info(f"Trying model: {model}")
            response = requests.post(CEREBRAS_API_URL, headers=headers, json=payload, timeout=90)
            if response.status_code == 429:
                logger.warning(f"Model {model} is rate-limited (429). Trying next model...")
                continue
            response.raise_for_status()
            data = response.json()
            content = data["choices"][0]["message"]["content"]
            logger.info(f"Got response from model: {model}")
            return content
        except requests.exceptions.HTTPError as e:
            logger.warning(f"Model {model} returned HTTP error: {e}. Trying next...")
            continue
        except Exception as e:
            logger.error(f"Unexpected error with model {model}: {e}. Trying next...")
            continue

    raise RuntimeError("All Cerebras models are unavailable. Please try again in a moment.")


import numpy as np

def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    v1 = np.array(vec1)
    v2 = np.array(vec2)
    return float(np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2)))

class SemanticCache:
    """An in-memory cache that retrieves answers for semantically similar queries."""
    def __init__(self, qdrant_store: QdrantStore, threshold: float = 0.95):
        self.qdrant_store = qdrant_store
        self.threshold = threshold
        self.cache = []  # list of dicts: {"query": str, "embedding": list, "response": dict}
        
    def get(self, query: str) -> Optional[Dict[str, Any]]:
        if not self.cache:
            return None
            
        embedding = self.qdrant_store.get_embedding(query)
        best_match = None
        highest_sim = 0.0
        
        for item in self.cache:
            sim = cosine_similarity(embedding, item["embedding"])
            if sim > highest_sim:
                highest_sim = sim
                best_match = item
                
        if highest_sim >= self.threshold and best_match:
            logger.info(f"Semantic Cache Hit! Similarity: {highest_sim:.3f} (matched: '{best_match['query']}')")
            response = best_match["response"].copy()
            response["cached"] = True
            return response
            
        return None
        
    def put(self, query: str, response: dict):
        embedding = self.qdrant_store.get_embedding(query)
        self.cache.append({
            "query": query,
            "embedding": embedding,
            "response": response
        })


class RAGPipeline:
    def __init__(self, qdrant_store: QdrantStore, bm25_index: BM25Index):
        self.qdrant_store = qdrant_store
        self.bm25_index = bm25_index
        self.semantic_cache = SemanticCache(qdrant_store, threshold=0.95)

    def reciprocal_rank_fusion(
        self, dense_results: List[Dict[str, Any]], sparse_results: List[Dict[str, Any]], k: int = 60
    ) -> List[Tuple[Dict[str, Any], float]]:
        """Applies Reciprocal Rank Fusion (RRF) to merge dense and sparse results."""
        rrf_scores = {}
        doc_map = {}

        for rank, hit in enumerate(dense_results):
            doc_id = hit["id"]
            doc_map[doc_id] = hit
            rrf_scores[doc_id] = rrf_scores.get(doc_id, 0.0) + (1.0 / (k + (rank + 1)))

        for rank, hit in enumerate(sparse_results):
            doc_id = hit["id"]
            doc_map[doc_id] = hit
            rrf_scores[doc_id] = rrf_scores.get(doc_id, 0.0) + (1.0 / (k + (rank + 1)))

        sorted_rrf = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)

        merged_results = []
        for doc_id, score in sorted_rrf:
            doc = doc_map[doc_id].copy()
            merged_results.append((doc, score))

        return merged_results

    def hybrid_search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Retrieves documents using hybrid search (Qdrant + BM25) and merges via RRF."""
        candidate_count = top_k * 2
        dense_hits = self.qdrant_store.search(query, top_k=candidate_count)
        sparse_hits = self.bm25_index.search(query, top_k=candidate_count)

        fused_results = self.reciprocal_rank_fusion(dense_hits, sparse_hits)

        top_results = []
        for doc, score in fused_results[:top_k]:
            doc["rrf_score"] = score
            top_results.append(doc)

        return top_results

    def generate_answer(self, query: str, contexts: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generates grounded answer using an LLM based on the retrieved contexts."""
        if not contexts:
            return {
                "answer": "I'm sorry, I couldn't find any relevant discussions or resources in the dataset to answer your question.",
                "sources": []
            }

        formatted_contexts = []
        sources = []
        for i, ctx in enumerate(contexts):
            title = ctx["metadata"].get("title", "Stack Overflow Discussion")
            score = ctx["metadata"].get("score", 0)
            url = ctx["metadata"].get("url", "")

            block = f"--- [Source {i+1}] ---\nTitle: {title}\nScore: {score}\nContent: {ctx['text']}\n"
            formatted_contexts.append(block)

            sources.append({
                "id": ctx["id"],
                "title": title,
                "score": score,
                "url": url,
                "rrf_score": ctx.get("rrf_score", 0)
            })

        context_str = "\n".join(formatted_contexts)

        system_instruction = (
            "You are an expert Python programming assistant helping data science learners.\n"
            "Your task is to answer the user's question using ONLY the provided Stack Overflow context sources.\n"
            "Follow these rules strictly:\n"
            "1. Ground your answer completely in the provided sources. Do not hallucinate.\n"
            "2. If the context does not contain enough information, state so clearly.\n"
            "3. Cite your sources using [Source X] notation.\n"
            "4. Provide clean, well-formatted Python code snippets where relevant.\n"
            "5. Keep the tone helpful, professional, and educational."
        )

        user_prompt = f"User Question: {query}\n\nContext Sources:\n{context_str}\n\nAnswer:"

        messages = [
            {"role": "system", "content": system_instruction},
            {"role": "user", "content": user_prompt}
        ]

        try:
            content = call_llm(messages, temperature=0.2, max_tokens=1500)
            return {
                "answer": content.strip(),
                "sources": sources
            }
        except Exception as e:
            logger.error(f"Error calling LLM for answer generation: {e}")
            return {
                "answer": f"Error generating answer: {str(e)}",
                "sources": sources
            }
