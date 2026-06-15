from typing import List, Optional
from pydantic import BaseModel, Field

class QuestionRequest(BaseModel):
    question: str = Field(
        ..., 
        description="The Python-related question asked by the data science learner.",
        examples=["How do I merge two dictionaries in Python 3.9+?"]
    )

class SourceMetadata(BaseModel):
    id: int = Field(..., description="Unique ID of the Stack Overflow thread.")
    title: str = Field(..., description="Title of the question.")
    score: int = Field(..., description="Score/Upvotes of the post.")
    url: str = Field("", description="URL of the Stack Overflow post.")
    rrf_score: float = Field(..., description="Reciprocal Rank Fusion score of this document.")

class GuardrailEvaluation(BaseModel):
    is_grounded: bool = Field(..., description="Groundedness status of the answer.")
    grounding_score: float = Field(..., description="Confidence/grounding score from 0 to 1.")
    critique: str = Field(..., description="Critique/Explanation of the grounding check.")

class QuestionResponse(BaseModel):
    answer: str = Field(..., description="The grounded answer to the question.")
    sources: List[SourceMetadata] = Field(default=[], description="List of Stack Overflow posts used as context.")
    evaluation: GuardrailEvaluation = Field(..., description="Real-time groundedness evaluation metrics.")
    latency_ms: float = Field(..., description="Time taken to process the request in milliseconds.")
    cached: bool = Field(default=False, description="Whether the response was served instantly from the Semantic Cache.")

class HealthResponse(BaseModel):
    status: str = Field(..., description="API operational status ('healthy' or 'unhealthy').")
    qdrant_connected: bool = Field(..., description="Qdrant connection status.")
    bm25_indexed: bool = Field(..., description="BM25 index status.")
    environment: str = Field(..., description="Current deployment environment (e.g. production, development).")
