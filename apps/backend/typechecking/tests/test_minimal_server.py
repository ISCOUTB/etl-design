"""Unit tests for minimal FastAPI server."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.minimal_server import app
from src.schemas.healthcheck import (
    DatabaseHealthCheckResult,
    OverallHealthCheckResult,
    RabbitMQHealthCheckResult,
)


@pytest.fixture
def client():
    return TestClient(app)


def _healthy_result() -> OverallHealthCheckResult:
    return OverallHealthCheckResult(
        status="healthy",
        database=DatabaseHealthCheckResult(
            status="healthy",
            mongodb=True,
            redis=True,
        ),
        rabbitmq=RabbitMQHealthCheckResult(
            status="healthy",
            response_time_ms="< 5000",
            error=None,
        ),
    )


def _unhealthy_result() -> OverallHealthCheckResult:
    return OverallHealthCheckResult(
        status="unhealthy",
        database=DatabaseHealthCheckResult(
            status="unhealthy",
            mongodb=False,
            redis=True,
        ),
        rabbitmq=RabbitMQHealthCheckResult(
            status="unhealthy",
            response_time_ms="> 5000",
            error="timeout",
        ),
    )


class TestRootEndpoint:
    def test_root_returns_message(self, client):
        response = client.get("/")

        assert response.status_code == 200
        assert response.json() == {"message": "Minimal Typechecking Server is running."}

    def test_root_content_type(self, client):
        response = client.get("/")

        assert response.status_code == 200
        assert "application/json" in response.headers["content-type"]


class TestHealthEndpoint:
    @patch("src.minimal_server.get_database_client")
    @patch("src.minimal_server.check_databases_connection", new_callable=AsyncMock)
    def test_health_check_healthy_returns_200(
        self,
        mock_check_databases,
        mock_get_db_client,
        client,
    ):
        mock_db = MagicMock()
        mock_db.aclose = AsyncMock()
        mock_get_db_client.return_value = mock_db
        mock_check_databases.return_value = _healthy_result()

        response = client.get("/health")

        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "healthy"
        assert body["database"]["status"] == "healthy"
        assert body["rabbitmq"]["status"] == "healthy"
        mock_check_databases.assert_awaited_once()
        mock_db.aclose.assert_awaited_once()

    @patch("src.minimal_server.get_database_client")
    @patch("src.minimal_server.check_databases_connection", new_callable=AsyncMock)
    def test_health_check_unhealthy_returns_503(
        self,
        mock_check_databases,
        mock_get_db_client,
        client,
    ):
        mock_db = MagicMock()
        mock_db.aclose = AsyncMock()
        mock_get_db_client.return_value = mock_db
        mock_check_databases.return_value = _unhealthy_result()

        response = client.get("/health")

        assert response.status_code == 503
        assert response.json()["detail"] == "Service is unhealthy"
        mock_db.aclose.assert_awaited_once()

    @patch("src.minimal_server.get_database_client")
    @patch("src.minimal_server.check_databases_connection", new_callable=AsyncMock)
    def test_health_check_propagates_unexpected_exception(
        self,
        mock_check_databases,
        mock_get_db_client,
        client,
    ):
        mock_db = MagicMock()
        mock_db.aclose = AsyncMock()
        mock_get_db_client.return_value = mock_db
        mock_check_databases.side_effect = RuntimeError("Unexpected error")

        with pytest.raises(RuntimeError) as exc_info:
            client.get("/health")

        assert "Unexpected error" in str(exc_info.value)
        mock_db.aclose.assert_awaited_once()

    @patch("src.minimal_server.get_database_client")
    @patch("src.minimal_server.check_databases_connection", new_callable=AsyncMock)
    def test_multiple_health_checks(
        self,
        mock_check_databases,
        mock_get_db_client,
        client,
    ):
        mock_db = MagicMock()
        mock_db.aclose = AsyncMock()
        mock_get_db_client.return_value = mock_db
        mock_check_databases.return_value = _healthy_result()

        response1 = client.get("/health")
        response2 = client.get("/health")
        response3 = client.get("/health")

        assert response1.status_code == 200
        assert response2.status_code == 200
        assert response3.status_code == 200
        assert mock_check_databases.await_count == 3
        assert mock_db.aclose.await_count == 3


class TestServerConfiguration:
    def test_app_is_fastapi_instance(self):
        assert isinstance(app, FastAPI)

    def test_routes_are_registered(self):
        routes = [route.path for route in app.routes]
        assert "/" in routes
        assert "/health" in routes
