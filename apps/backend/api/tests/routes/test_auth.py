"""Tests for auth endpoints."""

from fastapi.testclient import TestClient


class TestAuthRoutes:
    """Test /auth endpoints."""

    def test_sign_up_success(self, test_client: TestClient):
        response = test_client.post(
            "/api/v1/auth/sign-up",
            data={
                "username": "signup_user",
                "email": "signup_user@example.com",
                "password": "Pass1234",
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "signup_user@example.com"
        assert data["name"] == "signup_user"
        assert "password" not in data

    def test_sign_up_duplicate_email(self, test_client: TestClient):
        payload = {
            "username": "dup_user",
            "email": "dup_user@example.com",
            "password": "Pass1234",
        }
        first_response = test_client.post("/api/v1/auth/sign-up", data=payload)
        assert first_response.status_code == 201

        second_response = test_client.post("/api/v1/auth/sign-up", data=payload)
        assert second_response.status_code in [400, 409]

    def test_sign_up_invalid_email(self, test_client: TestClient):
        response = test_client.post(
            "/api/v1/auth/sign-up",
            data={
                "username": "invalid_email_user",
                "email": "not-an-email",
                "password": "Pass1234",
            },
        )

        assert response.status_code == 422

    def test_sign_in_success_after_sign_up(self, test_client: TestClient):
        sign_up_payload = {
            "username": "signin_user",
            "email": "signin_user@example.com",
            "password": "Pass1234",
        }
        sign_up_response = test_client.post(
            "/api/v1/auth/sign-up", data=sign_up_payload
        )
        assert sign_up_response.status_code == 201

        sign_in_response = test_client.post(
            "/api/v1/auth/sign-in",
            data={
                "email": "signin_user@example.com",
                "password": "Pass1234",
            },
        )

        assert sign_in_response.status_code == 200
        data = sign_in_response.json()
        assert data["email"] == "signin_user@example.com"

    def test_sign_in_invalid_credentials(self, test_client: TestClient):
        response = test_client.post(
            "/api/v1/auth/sign-in",
            data={
                "email": "missing_user@example.com",
                "password": "WrongPass123",
            },
        )

        assert response.status_code in [400, 401]

    def test_test_token_requires_auth(self, test_client: TestClient):
        response = test_client.get("/api/v1/auth/test-token")

        assert response.status_code == 401

    def test_test_token_success(self, test_client: TestClient, test_token: str):
        headers = {"Authorization": f"Bearer {test_token}"}
        response = test_client.get("/api/v1/auth/test-token", headers=headers)

        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert "email" in data
        assert "role" in data
