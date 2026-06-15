import logging
import re
from typing import List, Dict, Any
from rank_bm25 import BM25Okapi

logger = logging.getLogger(__name__)

class BM25Index:
    def __init__(self):
        self.bm25: BM25Okapi = None
        self.documents: List[Dict[str, Any]] = []

    def _tokenize(self, text: str) -> List[str]:
        """Simple tokenizer that converts text to lowercase tokens."""
        return re.findall(r'\w+', text.lower())

    def build_index(self, documents: List[Dict[str, Any]]):
        """Builds a BM25 index from a list of documents.
        Each document should have keys: 'id' (int), 'text' (str), 'metadata' (dict).
        """
        logger.info(f"Building BM25 index with {len(documents)} documents...")
        self.documents = documents
        tokenized_corpus = [self._tokenize(doc["text"]) for doc in documents]
        self.bm25 = BM25Okapi(tokenized_corpus)
        logger.info("BM25 index built successfully.")

    def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Performs sparse keyword search using BM25."""
        if not self.bm25:
            logger.warning("BM25 index has not been built yet.")
            return []
            
        tokenized_query = self._tokenize(query)
        # Get BM25 scores for the query
        scores = self.bm25.get_scores(tokenized_query)
        
        # Zip documents with scores and sort
        scored_docs = list(zip(self.documents, scores))
        scored_docs.sort(key=lambda x: x[1], reverse=True)
        
        hits = []
        # Return top_k docs with scores > 0
        for doc, score in scored_docs[:top_k]:
            if score > 0:
                hits.append({
                    "id": doc["id"],
                    "score": float(score),
                    "text": doc["text"],
                    "metadata": doc.get("metadata", {})
                })
        return hits
