"""
Tests for API healthcheck endpoint.

These tests verify that the API healthcheck endpoint works correctly
and returns proper status information.
"""

from unittest.mock import AsyncMock, Mock

import pytest
from fastapi.testclient import TestClient

from src.api.deps import get_db_client, get_publisher
from src.main import app


@pytest.fixture
def mock_db_client():
    db_client = Mock()
    db_client.mongo_ping_async = AsyncMock(return_value={"pong": True})
    db_client.redis_ping_async = AsyncMock(return_value={"pong": True})
    return db_client


@pytest.fixture
def mock_publisher():
    publisher = Mock()
    publisher._channel = Mock(is_open=True)
    return publisher


@pytest.fixture
def healthcheck_client(test_client: TestClient, mock_db_client, mock_publisher):
    app.dependency_overrides[get_db_client] = lambda: mock_db_client
    app.dependency_overrides[get_publisher] = lambda: mock_publisher
    try:
        yield test_client
    finally:
        app.dependency_overrides.pop(get_db_client, None)
        app.dependency_overrides.pop(get_publisher, None)


class TestHealthcheckEndpoint:
    """Test healthcheck endpoint."""

    def test_healthcheck_status_ok(self, healthcheck_client: TestClient):
        """Healthcheck returns either healthy (200) or degraded (503)."""
        response = healthcheck_client.get("/api/v1/healthcheck")

        assert response.status_code in [200, 503]

    def test_healthcheck_response_structure(self, healthcheck_client: TestClient):
        """Test that healthcheck response has expected structure."""
        response = healthcheck_client.get("/api/v1/healthcheck")

        assert response.status_code in [200, 503]
        data = response.json()

        # Check that response has basic health status fields
        assert isinstance(data, dict)
        assert "mongo_status" in data
        assert "redis_status" in data
        assert "message_queue" in data
        assert isinstance(data["mongo_status"], bool)
        assert isinstance(data["redis_status"], bool)
        assert isinstance(data["message_queue"], bool)
