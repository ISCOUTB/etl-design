"""Tests for cache routes."""

from unittest.mock import AsyncMock, Mock

import pytest
from fastapi.testclient import TestClient

from src.api.deps import get_db_client
from src.main import app


@pytest.fixture
def mock_db_client():
    client = Mock()
    client.redis_get_cache_async = AsyncMock(
        return_value={"cache": {"k1": '{"foo": 1}', "k2": '"bar"'}}
    )
    client.clear_cache_async = AsyncMock(
        return_value={
            "success": True,
            "status": "success",
            "message": "cache cleared",
        }
    )
    return client


@pytest.fixture
def cache_client(test_client: TestClient, mock_db_client):
    app.dependency_overrides[get_db_client] = lambda: mock_db_client
    try:
        yield test_client
    finally:
        app.dependency_overrides.pop(get_db_client, None)


class TestCacheRoutes:
    def test_get_cache_requires_auth(self, cache_client: TestClient):
        response = cache_client.get("/api/v1/cache/")
        assert response.status_code == 401

    def test_get_cache_forbidden_for_user(
        self, cache_client: TestClient, test_token: str
    ):
        response = cache_client.get(
            "/api/v1/cache/", headers={"Authorization": f"Bearer {test_token}"}
        )
        assert response.status_code == 403

    def test_get_cache_admin_success(
        self, cache_client: TestClient, test_admin_token: str
    ):
        response = cache_client.get(
            "/api/v1/cache/", headers={"Authorization": f"Bearer {test_admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["k1"]["foo"] == 1
        assert data["k2"] == "bar"

    def test_clear_cache_admin_success(
        self, cache_client: TestClient, test_admin_token: str
    ):
        response = cache_client.delete(
            "/api/v1/cache/clear",
            headers={"Authorization": f"Bearer {test_admin_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
