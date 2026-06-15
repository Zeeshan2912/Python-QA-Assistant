import pytest
from src.db.bm25_index import BM25Index
from src.core.rag import RAGPipeline

def test_bm25_tokenization():
    """Verifies tokenizer lowercases and strips punctuation."""
    index = BM25Index()
    tokens = index._tokenize("Python: How to merge dicts?")
    assert tokens == ["python", "how", "to", "merge", "dicts"]

def test_bm25_indexing_and_search():
    """Verifies BM25 index correctly returns documents matching search keywords."""
    index = BM25Index()
    docs = [
        {"id": 1, "text": "Python dict merge dictionary", "metadata": {}},
        {"id": 2, "text": "FastAPI query parameters request", "metadata": {}}
    ]
    index.build_index(docs)
    
    results = index.search("dict merge", top_k=1)
    assert len(results) == 1
    assert results[0]["id"] == 1

def test_rrf_merging():
    """Verifies Reciprocal Rank Fusion logic correctly merges and sorts results."""
    # Create empty store mock dependencies
    pipeline = RAGPipeline(None, None)
    
    dense_results = [
        {"id": 1, "text": "Doc A"},
        {"id": 2, "text": "Doc B"}
    ]
    sparse_results = [
        {"id": 2, "text": "Doc B"},
        {"id": 3, "text": "Doc C"}
    ]
    
    merged = pipeline.reciprocal_rank_fusion(dense_results, sparse_results, k=60)
    
    # Doc 2 should have the highest score since it appears in both lists
    assert len(merged) == 3
    assert merged[0][0]["id"] == 2
