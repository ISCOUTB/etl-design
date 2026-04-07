"""
Tests for API healthcheck endpoint.

These tests verify that the API healthcheck endpoint works correctly
and returns proper status information.
"""

from fastapi.testclient import TestClient


class TestHealthcheckEndpoint:
    """Test healthcheck endpoint."""

    def test_healthcheck_status_ok(self, test_client: TestClient):
        """Healthcheck returns either healthy (200) or degraded (503)."""
        response = test_client.get("/api/v1/healthcheck")

        assert response.status_code in [200, 503]

    def test_healthcheck_response_structure(self, test_client: TestClient):
        """Test that healthcheck response has expected structure."""
        response = test_client.get("/api/v1/healthcheck")

        assert response.status_code in [200, 503]
        data = response.json()

        # Check that response has basic health status fields
        assert isinstance(data, dict)
        assert "status" in data or "error" in data
