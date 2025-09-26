"""Basic tests for Flask document uploader."""

import pytest
from app import app


def test_home_page():
    """Test the home page loads."""
    with app.test_client() as client:
        response = client.get('/')
        assert response.status_code == 200
        assert b'Upload Document' in response.data


def test_health_check():
    """Test the health endpoint."""
    with app.test_client() as client:
        response = client.get('/health')
        assert response.status_code == 200
        assert b'healthy' in response.data.lower()


def test_upload_without_file():
    """Test upload endpoint without file."""
    with app.test_client() as client:
        response = client.post('/upload')
        assert response.status_code == 400  # Should fail without file
