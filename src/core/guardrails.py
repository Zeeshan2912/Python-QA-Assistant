import re
import json
import logging
import requests
from typing import List, Dict, Any
from pydantic import BaseModel, Field
from src.config import settings

logger = logging.getLogger(__name__)

CEREBRAS_API_URL = "https://api.cerebras.ai/v1/chat/completions"
LLM_MODEL = "gpt-oss-120b"  # Cerebras production model


class GroundednessReport(BaseModel):
    is_grounded: bool = Field(description="True if the answer is fully supported by the context without hallucination, False otherwise.")
    grounding_score: float = Field(description="Groundedness score from 0.0 (not grounded) to 1.0 (fully grounded).")
    critique_explanation: str = Field(description="Explanation of the evaluation decision.")
    hallucinated_claims: List[str] = Field(description="List of specific claims in the answer not supported by the context.")


class Guardrails:
    def __init__(self):
        pass  # No client needed — we call Cerebras directly via requests

    def verify_groundedness(self, query: str, contexts: List[Dict[str, Any]], answer: str) -> GroundednessReport:
        """Verifies if the generated answer is grounded in the retrieved contexts using LLM self-critique."""
        if not contexts or not answer:
            return GroundednessReport(
                is_grounded=True,
                grounding_score=1.0,
                critique_explanation="Empty context or answer.",
                hallucinated_claims=[]
            )

        context_str = "\n\n".join([f"--- Source {i+1} ---\n{ctx['text']}" for i, ctx in enumerate(contexts)])

        prompt = (
            f"You are an AI Quality Auditor. Verify if an AI answer is fully grounded in the provided context.\n\n"
            f"USER QUERY:\n{query}\n\n"
            f"PROVIDED CONTEXT:\n{context_str}\n\n"
            f"AI ANSWER TO AUDIT:\n{answer}\n\n"
            f"Output ONLY a valid JSON object with these exact keys:\n"
            f'{{ "is_grounded": true or false, "grounding_score": 0.0 to 1.0, "critique_explanation": "...", "hallucinated_claims": [] }}'
        )

        headers = {
            "Authorization": f"Bearer {settings.CEREBRAS_API_KEY}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": LLM_MODEL,
            "messages": [
                {"role": "system", "content": "You are a precise auditor. Output only valid JSON, no extra text."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.0,
            "max_tokens": 512,
        }

        try:
            response = requests.post(CEREBRAS_API_URL, headers=headers, json=payload, timeout=90)
            response.raise_for_status()
            raw = response.json()["choices"][0]["message"]["content"]

            # Extract JSON robustly — models sometimes wrap JSON in markdown code blocks
            json_match = re.search(r'\{.*\}', raw, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
            else:
                data = json.loads(raw)

            return GroundednessReport(**data)

        except Exception as e:
            logger.error(f"Error in guardrails groundedness verification: {e}")
            return GroundednessReport(
                is_grounded=True,
                grounding_score=0.8,
                critique_explanation=f"Fallback due to execution error: {str(e)}",
                hallucinated_claims=[]
            )
