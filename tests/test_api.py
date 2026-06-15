import pytest
from fastapi.testclient import TestClient
import os
from dotenv import load_dotenv

load_dotenv()

# We need to set a dummy/mock API key if it's not present in the environment for unit tests
if "GEMINI_API_KEY" not in os.environ:
    os.environ["GEMINI_API_KEY"] = "mock-key-for-testing"

from src.main import app

client = TestClient(app)

def test_health_endpoint():
    """Verifies that the /health endpoint is operational and returns correct schema."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "qdrant_connected" in data
    assert "bm25_indexed" in data
    assert data["status"] in ["healthy", "unhealthy"]

def test_ask_endpoint_missing_payload():
    """Verifies that /ask endpoint returns a 422 validation error when request body is empty."""
    response = client.post("/api/v1/ask", json={})
    assert response.status_code == 422

def test_ask_endpoint_invalid_schema():
    """Verifies validation error when request payload lacks required fields."""
    response = client.post("/api/v1/ask", json={"query": "test"})
    assert response.status_code == 422
