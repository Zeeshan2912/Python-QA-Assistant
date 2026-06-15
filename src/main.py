import logging
import sys
from contextlib import asynccontextmanager
import structlog
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.config import settings
from src.db.qdrant_store import QdrantStore
from src.db.bm25_index import BM25Index
from src.db.default_data import DEFAULT_QA_DATA
from src.core.rag import RAGPipeline
from src.core.guardrails import Guardrails
from src.api.router import router as api_router

# Configure Structured Logging
logging.basicConfig(
    format="%(message)s",
    stream=sys.stdout,
    level=logging.INFO,
)

structlog.configure(
    processors=[
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.JSONRenderer(),
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup Phase
    logger.info("Starting Python Programming Q&A Assistant Service...")
    
    try:
        # Initialize databases
        qdrant_store = QdrantStore()
        bm25_index = BM25Index()
        
        # Check if Qdrant collection is empty; if so, populate with default QA data
        collections_info = qdrant_store.client.get_collection(qdrant_store.collection_name)
        if collections_info.points_count == 0:
            logger.info("Qdrant collection empty. Populating with default high-quality Python Q&A dataset...")
            qdrant_store.index_documents(DEFAULT_QA_DATA)
            
        # Build BM25 index using the same default data
        bm25_index.build_index(DEFAULT_QA_DATA)
        
        # Initialize pipelines
        rag_pipeline = RAGPipeline(qdrant_store, bm25_index)
        guardrails = Guardrails()
        
        # Store in app state for request handlers
        app.state.qdrant_store = qdrant_store
        app.state.bm25_index = bm25_index
        app.state.rag_pipeline = rag_pipeline
        app.state.guardrails = guardrails
        
        logger.info("All components initialized successfully!")
    except Exception as e:
        logger.error("Failed to initialize system components during startup", error=str(e))
        # Keep running so healthchecks can report error state
        
    yield
    
    # Shutdown Phase
    logger.info("Shutting down Python Programming Q&A Assistant Service...")

# Initialize FastAPI App
app = FastAPI(
    title="Python Programming Q&A Assistant API",
    description="A production-grade, grounded RAG Q&A service for Python learners, powered by Qdrant, BM25, and Google Gemini.",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global Exception Handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error("Unhandled Exception occurred", path=request.url.path, error=str(exc))
    return JSONResponse(
        status_code=500,
        content={"detail": "An unexpected error occurred. Please contact the administrator."}
    )

# Include Router
app.include_router(api_router, prefix="/api/v1")

# Root endpoint: Serve Web UI
import os
from fastapi.responses import RedirectResponse, FileResponse
@app.get("/", include_in_schema=False)
async def root():
    static_file_path = os.path.join(os.path.dirname(__file__), "static", "index.html")
    if os.path.exists(static_file_path):
        return FileResponse(static_file_path)
    return RedirectResponse(url="/docs")
