"""Basic tests for FastAPI backend."""

import pytest
from fastapi.testclient import TestClient
from app.main import app


def test_health_endpoint():
    """Test the health endpoint."""
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    assert "status" in response.json()


def test_root_endpoint():
    """Test the root endpoint."""
    client = TestClient(app)
    response = client.get("/")
    assert response.status_code == 200


def test_api_root():
    """Test the API root endpoint."""
    client = TestClient(app)
    response = client.get("/api/")
    assert response.status_code == 200
