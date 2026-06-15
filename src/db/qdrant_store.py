import logging
from typing import List, Dict, Any, Optional
from qdrant_client import QdrantClient
from qdrant_client.http import models as qdrant_models
from sentence_transformers import SentenceTransformer
from src.config import settings

logger = logging.getLogger(__name__)

class QdrantStore:
    def __init__(self):
        # Initialize Qdrant Client
        if settings.QDRANT_IN_MEMORY:
            logger.info("Initializing Qdrant in-memory database...")
            self.client = QdrantClient(":memory:")
        else:
            logger.info(f"Connecting to Qdrant at {settings.QDRANT_HOST}:{settings.QDRANT_PORT}...")
            self.client = QdrantClient(host=settings.QDRANT_HOST, port=settings.QDRANT_PORT)
            
        # Initialize Local Embedding Model
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        self.collection_name = "python_qa"
        self.vector_size = 384
        self._ensure_collection()

    def _ensure_collection(self):
        """Creates the Qdrant collection if it does not exist."""
        try:
            collections = self.client.get_collections().collections
            exists = any(c.name == self.collection_name for c in collections)
            
            if not exists:
                logger.info(f"Creating Qdrant collection: {self.collection_name} (dimensions: {self.vector_size})")
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=qdrant_models.VectorParams(
                        size=self.vector_size,
                        distance=qdrant_models.Distance.COSINE
                    )
                )
            else:
                logger.info(f"Collection {self.collection_name} already exists.")
        except Exception as e:
            logger.error(f"Error ensuring Qdrant collection: {e}")
            raise

    def get_embedding(self, text: str) -> List[float]:
        """Generates embedding using local SentenceTransformer."""
        try:
            embedding = self.embedding_model.encode(text)
            return embedding.tolist()
        except Exception as e:
            logger.error(f"Error generating local embedding: {e}")
            raise


    def get_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """Generates embeddings for a batch of texts by calling get_embedding sequentially."""
        logger.info(f"Generating embeddings sequentially for {len(texts)} texts...")
        return [self.get_embedding(t) for t in texts]




    def index_documents(self, documents: List[Dict[str, Any]]):
        """Indexes documents into the Qdrant collection.
        Each document should have keys: 'id' (int), 'text' (str), 'metadata' (dict).
        """
        logger.info(f"Indexing {len(documents)} documents into Qdrant...")
        
        # Batch generate embeddings
        texts = [doc["text"] for doc in documents]
        embeddings = self.get_embeddings_batch(texts)
        
        points = []
        for i, doc in enumerate(documents):
            points.append(
                qdrant_models.PointStruct(
                    id=doc["id"],
                    vector=embeddings[i],
                    payload={
                        "text": doc["text"],
                        **doc.get("metadata", {})
                    }
                )
            )
            
        # Upsert in batches of 100
        batch_size = 100
        for i in range(0, len(points), batch_size):
            self.client.upsert(
                collection_name=self.collection_name,
                points=points[i:i+batch_size]
            )
        logger.info("Indexing to Qdrant completed.")

    def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Performs dense vector search on Qdrant using the modern query_points API."""
        try:
            query_vector = self.get_embedding(query)
            response = self.client.query_points(
                collection_name=self.collection_name,
                query=query_vector,
                limit=top_k
            )
            
            hits = []
            for hit in response.points:
                hits.append({
                    "id": hit.id,
                    "score": hit.score,
                    "text": hit.payload.get("text", ""),
                    "metadata": {k: v for k, v in hit.payload.items() if k != "text"}
                })
            return hits
        except Exception as e:
            logger.error(f"Error searching Qdrant: {e}")
            return []

