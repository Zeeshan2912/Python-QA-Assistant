import os
import sys
import json
import logging
from dotenv import load_dotenv

# Ensure project root is in PYTHONPATH
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load env variables before importing modules
load_dotenv()

from src.db.qdrant_store import QdrantStore
from src.db.default_data import DEFAULT_QA_DATA


logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def run_indexing():
    """Generates embeddings and indexes the preprocessed Stack Overflow dataset into Qdrant."""
    cleaned_data_path = os.path.join("data", "cleaned_qa.json")
    
    if os.path.exists(cleaned_data_path):
        logger.info(f"Loading cleaned dataset from {cleaned_data_path}...")
        with open(cleaned_data_path, "r", encoding="utf-8") as f:
            documents = json.load(f)
    else:
        logger.warning(
            f"Preprocessed dataset not found at {cleaned_data_path}.\n"
            "Falling back to indexing the default high-quality Q&A dataset..."
        )
        documents = DEFAULT_QA_DATA
        
    logger.info(f"Indexing {len(documents)} documents into Qdrant...")
    
    try:
        qdrant_store = QdrantStore()
        # Clean any old collection by recreating it
        try:
            qdrant_store.client.delete_collection(qdrant_store.collection_name)
        except Exception:
            pass
        qdrant_store._ensure_collection()
        
        # Populate
        qdrant_store.index_documents(documents)
        logger.info("Indexing completed successfully!")
    except Exception as e:
        logger.error(f"Indexing failed: {e}")
        raise

if __name__ == "__main__":
    run_indexing()
