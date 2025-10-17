"""
Basic health check tests for CI/CD pipeline.
"""

import pytest


@pytest.mark.unit
def test_health_endpoint(client):
    """Test the health check endpoint."""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert data["status"] == "healthy"


@pytest.mark.unit
def test_root_endpoint(client):
    """Test the root endpoint."""
    response = client.get("/")
    assert response.status_code == 200


@pytest.mark.unit
def test_sample_semiprime_fixture(sample_semiprime):
    """Test that sample semiprime fixture works."""
    assert sample_semiprime["small"] == 143
    assert sample_semiprime["medium"] == 323
    assert 143 == 11 * 13
    assert 323 == 17 * 19
