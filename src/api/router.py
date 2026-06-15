import time
import structlog
from fastapi import APIRouter, Request, HTTPException, status
from src.api.schemas import QuestionRequest, QuestionResponse, HealthResponse, GuardrailEvaluation

logger = structlog.get_logger(__name__)
router = APIRouter()

@router.post(
    "/ask",
    response_model=QuestionResponse,
    status_code=status.HTTP_200_OK,
    summary="Ask a Python Programming Question",
    description="Processes a query, retrieves context from Stack Overflow, generates a grounded response, and audits it."
)
async def ask_question(request: Request, payload: QuestionRequest):
    start_time = time.time()
    
    # Retrieve pipelines from app state
    rag_pipeline = getattr(request.app.state, "rag_pipeline", None)
    guardrails = getattr(request.app.state, "guardrails", None)
    
    if not rag_pipeline or not guardrails:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="RAG pipeline is not fully initialized. Please try again later."
        )

    logger.info("Received query", query=payload.question)  # structlog supports kwargs
    
    try:
        # Check Semantic Cache first
        cached_response = rag_pipeline.semantic_cache.get(payload.question)
        if cached_response:
            latency = (time.time() - start_time) * 1000.0
            return QuestionResponse(
                answer=cached_response["answer"],
                sources=cached_response["sources"],
                evaluation=GuardrailEvaluation(
                    is_grounded=cached_response["evaluation"]["is_grounded"],
                    grounding_score=cached_response["evaluation"]["grounding_score"],
                    critique=cached_response["evaluation"]["critique"]
                ),
                latency_ms=round(latency, 2),
                cached=True
            )

        # Step 1: Hybrid Retrieve & Rank Contexts
        contexts = rag_pipeline.hybrid_search(payload.question, top_k=5)
        
        # Step 2: Generate Answer
        rag_output = rag_pipeline.generate_answer(payload.question, contexts)
        answer = rag_output["answer"]
        sources = rag_output["sources"]
        
        # Step 3: Run Guardrails (with a brief pause to respect free-tier rate limits)
        import asyncio
        await asyncio.sleep(2)
        critique_report = guardrails.verify_groundedness(payload.question, contexts, answer)
        
        latency = (time.time() - start_time) * 1000.0
        
        # Cache the generated response for future identical or semantically similar queries
        response_to_cache = {
            "answer": answer,
            "sources": sources,
            "evaluation": {
                "is_grounded": critique_report.is_grounded,
                "grounding_score": critique_report.grounding_score,
                "critique": critique_report.critique_explanation
            }
        }
        rag_pipeline.semantic_cache.put(payload.question, response_to_cache)
        
        return QuestionResponse(
            answer=answer,
            sources=sources,
            evaluation=GuardrailEvaluation(
                is_grounded=critique_report.is_grounded,
                grounding_score=critique_report.grounding_score,
                critique=critique_report.critique_explanation
            ),
            latency_ms=round(latency, 2),
            cached=False
        )
    except Exception as e:
        logger.error("Error processing request", error=str(e))  # structlog supports kwargs
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while processing the request: {str(e)}"
        )

@router.get(
    "/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Service Health Check"
)
async def health_check(request: Request):
    qdrant_store = getattr(request.app.state, "qdrant_store", None)
    bm25_index = getattr(request.app.state, "bm25_index", None)
    
    qdrant_ok = False
    bm25_ok = False
    
    if qdrant_store:
        try:
            # Check connection
            qdrant_store.client.get_collections()
            qdrant_ok = True
        except Exception as e:
            logger.error("Healthcheck Qdrant connection failed", error=str(e))  # structlog supports kwargs
            
    if bm25_index and bm25_index.bm25 is not None:
        bm25_ok = True
        
    status_str = "healthy" if (qdrant_ok and bm25_ok) else "unhealthy"
    
    from src.config import settings
    return HealthResponse(
        status=status_str,
        qdrant_connected=qdrant_ok,
        bm25_indexed=bm25_ok,
        environment=settings.ENVIRONMENT
    )
