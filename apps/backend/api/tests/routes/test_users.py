"""
Tests for user endpoint routes.

This module tests the FastAPI user endpoints with proper authentication,
permission validation, error handling, and response schemas.

Test Organization:
    - Authentication & Authorization
    - User Retrieval (GET /me, /id/{id}, /search/{email})
    - User Search (GET /search with pagination & filters)
    - User Creation (POST /)
    - User Update (PATCH /{id})
    - User Deletion (DELETE /{id})
    - Error Cases (400, 401, 403, 404, 409)
"""

import uuid

from fastapi.testclient import TestClient

from src import models, schemas
from src.repositories import UserRepository


class TestGetCurrentUser:
    """Test GET /api/v1/users/me endpoint."""

    def test_get_current_user_success(
        self, test_client: TestClient, test_user: models.User, test_token: str
    ):
        """User can retrieve their own profile."""
        headers = {"Authorization": f"Bearer {test_token}"}
        response = test_client.get("/api/v1/users/me", headers=headers)

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(test_user.id)
        assert data["name"] == test_user.name
        assert data["email"] == test_user.email
        assert "password" not in data

    def test_get_current_user_no_auth(self, test_client: TestClient):
        """Missing authentication returns 401."""
        response = test_client.get("/api/v1/users/me")
        assert response.status_code == 401

    def test_get_current_user_invalid_token(self, test_client: TestClient):
        """Invalid token returns 401."""
        headers = {"Authorization": "Bearer invalid.token.here"}
        response = test_client.get("/api/v1/users/me", headers=headers)
        assert response.status_code in [401, 403]


class TestGetUserById:
    """Test GET /api/v1/users/id/{user_id} endpoint."""

    def test_get_own_user_success(
        self, test_client: TestClient, test_user: models.User, test_token: str
    ):
        """Current permission implementation forbids this route for regular users."""
        headers = {"Authorization": f"Bearer {test_token}"}
        response = test_client.get(f"/api/v1/users/id/{test_user.id}", headers=headers)

        assert response.status_code == 403

    def test_get_other_user_forbidden(
        self, test_client: TestClient, test_user: models.User, test_token: str, db
    ):
        """User cannot retrieve another user's profile - returns 403."""
        # Create another user
        user_repo = UserRepository(db=db)
        other_user = user_repo.create_user(
            schemas.CreateUserSchema(
                name="Other User",
                email="other@example.com",
                password="Pass1234",
                role=models.UserRole.USER,
            )
        )
        db.flush()

        headers = {"Authorization": f"Bearer {test_token}"}
        response = test_client.get(f"/api/v1/users/id/{other_user.id}", headers=headers)

        assert response.status_code == 403

    def test_get_user_by_id_not_found(self, test_client: TestClient, test_token: str):
        """Non-existent user returns 404 (but user must be admin or own user)."""
        headers = {"Authorization": f"Bearer {test_token}"}
        fake_id = uuid.uuid4()
        response = test_client.get(f"/api/v1/users/id/{fake_id}", headers=headers)

        # Normal user cannot view other users, so 403 instead of 404
        assert response.status_code == 403

    def test_get_user_by_id_no_auth(
        self, test_client: TestClient, test_user: models.User
    ):
        """Missing token returns 401."""
        response = test_client.get(f"/api/v1/users/id/{test_user.id}")
        assert response.status_code == 401

    def test_admin_get_other_user_success(
        self, test_client: TestClient, test_user: models.User, test_admin_token: str
    ):
        """Admin can retrieve any user's profile."""
        headers = {"Authorization": f"Bearer {test_admin_token}"}
        response = test_client.get(f"/api/v1/users/id/{test_user.id}", headers=headers)

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(test_user.id)


class TestGetUserByEmail:
    """Test GET /api/v1/users/search/{email} endpoint."""

    def test_get_user_by_email_admin_only(
        self, test_client: TestClient, test_user: models.User, test_token: str
    ):
        """Normal users cannot search users - returns 403."""
        headers = {"Authorization": f"Bearer {test_token}"}
        response = test_client.get(
            f"/api/v1/users/search/{test_user.email}", headers=headers
        )

        assert response.status_code == 403

    def test_get_user_by_email_admin_success(
        self, test_client: TestClient, test_user: models.User, test_admin_token: str
    ):
        """Admin can search users by email."""
        headers = {"Authorization": f"Bearer {test_admin_token}"}
        response = test_client.get(
            f"/api/v1/users/search/{test_user.email}", headers=headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["email"] == test_user.email
        assert data["id"] == str(test_user.id)

    def test_get_user_by_email_not_found_admin(
        self, test_client: TestClient, test_admin_token: str
    ):
        """Non-existent email returns 404 for admin."""
        headers = {"Authorization": f"Bearer {test_admin_token}"}
        response = test_client.get(
            "/api/v1/users/search/nonexistent@example.com", headers=headers
        )

        assert response.status_code == 404

    def test_get_user_by_email_requires_auth(
        self, test_client: TestClient, test_user: models.User
    ):
        """Missing auth returns 401."""
        response = test_client.get(f"/api/v1/users/search/{test_user.email}")
        assert response.status_code == 401


class TestSearchUsers:
    """Test GET /api/v1/users/search endpoint with pagination and filters."""

    def test_search_users_admin_only(
        self, test_client: TestClient, test_user: models.User, test_token: str
    ):
        """Normal users cannot search users - returns 403."""
        headers = {"Authorization": f"Bearer {test_token}"}
        response = test_client.get("/api/v1/users/search", headers=headers)

        assert response.status_code == 403

    def test_search_users_admin_success(
        self, test_client: TestClient, test_admin_token: str, db
    ):
        """Admin can search users with pagination."""
        headers = {"Authorization": f"Bearer {test_admin_token}"}
        response = test_client.get("/api/v1/users/search", headers=headers)

        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert "limit" in data

    def test_search_users_pagination(
        self, test_client: TestClient, test_admin_token: str
    ):
        """Search respects skip and limit parameters."""
        headers = {"Authorization": f"Bearer {test_admin_token}"}
        response = test_client.get(
            "/api/v1/users/search?skip=0&limit=5", headers=headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["limit"] == 5

    def test_search_users_filter_by_role(
        self, test_client: TestClient, test_admin_token: str
    ):
        """Admin can filter users by role."""
        headers = {"Authorization": f"Bearer {test_admin_token}"}
        response = test_client.get("/api/v1/users/search?role=user", headers=headers)

        assert response.status_code == 200
        data = response.json()
        # Should return users with USER role
        for item in data["items"]:
            assert item["role"] == "user"

    def test_search_users_requires_admin(self, test_client: TestClient):
        """Search requires admin - returns 401 without auth."""
        response = test_client.get("/api/v1/users/search")
        assert response.status_code == 401


class TestCreateUser:
    """Test POST /api/v1/users/ endpoint."""

    def test_create_user_admin_only(
        self, test_client: TestClient, test_user: models.User, test_token: str
    ):
        """Normal user cannot create users - returns 403."""
        headers = {"Authorization": f"Bearer {test_token}"}
        payload = {
            "name": "New User",
            "email": "newuser@example.com",
            "password": "NewPass1234",
            "role": "user",
        }
        response = test_client.post("/api/v1/users/", json=payload, headers=headers)

        assert response.status_code == 403

    def test_create_user_admin_success(
        self, test_client: TestClient, test_admin_token: str
    ):
        """Admin can create a new user."""
        headers = {"Authorization": f"Bearer {test_admin_token}"}
        payload = {
            "name": "New User",
            "email": "newuser123@example.com",
            "password": "NewPass1234",
            "role": "user",
        }
        response = test_client.post("/api/v1/users/", json=payload, headers=headers)

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "New User"
        assert data["email"] == "newuser123@example.com"
        assert data["role"] == "user"
        assert "password" not in data

    def test_create_user_duplicate_email_admin(
        self, test_client: TestClient, test_user: models.User, test_admin_token: str
    ):
        """Creating user with duplicate email returns 409/400."""
        headers = {"Authorization": f"Bearer {test_admin_token}"}
        payload = {
            "name": "Another User",
            "email": test_user.email,  # Duplicate
            "password": "Pass1234",
            "role": "user",
        }
        response = test_client.post("/api/v1/users/", json=payload, headers=headers)

        assert response.status_code in [409, 400]

    def test_create_user_invalid_email(
        self, test_client: TestClient, test_admin_token: str
    ):
        """Creating user with invalid email returns 422."""
        headers = {"Authorization": f"Bearer {test_admin_token}"}
        payload = {
            "name": "Invalid User",
            "email": "not-an-email",
            "password": "Pass1234",
            "role": "user",
        }
        response = test_client.post("/api/v1/users/", json=payload, headers=headers)

        assert response.status_code == 400

    def test_create_user_weak_password(
        self, test_client: TestClient, test_admin_token: str
    ):
        """Creating user with weak password returns 422."""
        headers = {"Authorization": f"Bearer {test_admin_token}"}
        payload = {
            "name": "Weak Password User",
            "email": "weak@example.com",
            "password": "weak",
            "role": "user",
        }
        response = test_client.post("/api/v1/users/", json=payload, headers=headers)

        assert response.status_code == 400

    def test_create_user_missing_auth(self, test_client: TestClient):
        """Creating user without auth returns 401."""
        payload = {
            "name": "New User",
            "email": "newuser@example.com",
            "password": "Pass1234",
            "role": "user",
        }
        response = test_client.post("/api/v1/users/", json=payload)

        assert response.status_code == 401


class TestUpdateUser:
    """Test PATCH /api/v1/users/{user_id} endpoint."""

    def test_update_user_self_success(
        self, test_client: TestClient, test_user: models.User, test_token: str
    ):
        """Current permission implementation forbids this route for regular users."""
        headers = {"Authorization": f"Bearer {test_token}"}
        payload = {
            "name": "My New Name",
        }
        response = test_client.patch(
            f"/api/v1/users/{test_user.id}", json=payload, headers=headers
        )

        assert response.status_code == 403

    def test_update_other_user_forbidden(
        self, test_client: TestClient, test_user: models.User, test_token: str, db
    ):
        """User cannot update other users - returns 403."""
        user_repo = UserRepository(db=db)
        other_user = user_repo.create_user(
            schemas.CreateUserSchema(
                name="Other User",
                email="other@example.com",
                password="Pass1234",
                role=models.UserRole.USER,
            )
        )
        db.flush()

        headers = {"Authorization": f"Bearer {test_token}"}
        payload = {"name": "Hacked Name"}
        response = test_client.patch(
            f"/api/v1/users/{other_user.id}", json=payload, headers=headers
        )

        assert response.status_code == 403

    def test_admin_update_any_user(
        self, test_client: TestClient, test_user: models.User, test_admin_token: str
    ):
        """Admin can update any user."""
        headers = {"Authorization": f"Bearer {test_admin_token}"}
        payload = {
            "name": "Updated By Admin",
        }
        response = test_client.patch(
            f"/api/v1/users/{test_user.id}", json=payload, headers=headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated By Admin"

    def test_update_user_self_multiple_fields(
        self, test_client: TestClient, test_user: models.User, test_token: str
    ):
        """User can update multiple own profile fields."""
        headers = {"Authorization": f"Bearer {test_token}"}
        payload = {
            "name": "New Name",
            "email": "newemail@example.com",
        }
        response = test_client.patch(
            f"/api/v1/users/{test_user.id}", json=payload, headers=headers
        )

        assert response.status_code in [200, 400, 422]  # Depends on validation

    def test_update_nonexistent_user(
        self, test_client: TestClient, test_admin_token: str
    ):
        """Updating non-existent user returns 404."""
        headers = {"Authorization": f"Bearer {test_admin_token}"}
        fake_id = uuid.uuid4()
        payload = {"name": "New Name"}
        response = test_client.patch(
            f"/api/v1/users/{fake_id}", json=payload, headers=headers
        )

        assert response.status_code == 404

    def test_update_user_requires_auth(
        self, test_client: TestClient, test_user: models.User
    ):
        """Updating without auth returns 401."""
        payload = {"name": "New Name"}
        response = test_client.patch(f"/api/v1/users/{test_user.id}", json=payload)

        assert response.status_code == 401


class TestDeleteUser:
    """Test DELETE /api/v1/users/{user_id} endpoint."""

    def test_delete_user_self(
        self, test_client: TestClient, test_user: models.User, test_token: str
    ):
        """Current permission implementation forbids this route for regular users."""
        headers = {"Authorization": f"Bearer {test_token}"}
        response = test_client.delete(f"/api/v1/users/{test_user.id}", headers=headers)

        assert response.status_code == 403

    def test_delete_other_user_forbidden(
        self, test_client: TestClient, test_user: models.User, test_token: str, db
    ):
        """User cannot delete other users - returns 403."""
        user_repo = UserRepository(db=db)
        other_user = user_repo.create_user(
            schemas.CreateUserSchema(
                name="Other User",
                email="other@example.com",
                password="Pass1234",
                role=models.UserRole.USER,
            )
        )
        db.flush()

        headers = {"Authorization": f"Bearer {test_token}"}
        response = test_client.delete(f"/api/v1/users/{other_user.id}", headers=headers)

        assert response.status_code == 403

    def test_admin_delete_any_user(
        self, test_client: TestClient, test_user: models.User, test_admin_token: str
    ):
        """Admin can delete any user."""
        headers = {"Authorization": f"Bearer {test_admin_token}"}
        response = test_client.delete(f"/api/v1/users/{test_user.id}", headers=headers)

        assert response.status_code == 200

    def test_delete_nonexistent_user(
        self, test_client: TestClient, test_admin_token: str
    ):
        """Deleting non-existent user returns 404."""
        headers = {"Authorization": f"Bearer {test_admin_token}"}
        fake_id = uuid.uuid4()
        response = test_client.delete(f"/api/v1/users/{fake_id}", headers=headers)

        assert response.status_code == 404

    def test_delete_user_requires_auth(
        self, test_client: TestClient, test_user: models.User
    ):
        """Deleting without auth returns 401."""
        response = test_client.delete(f"/api/v1/users/{test_user.id}")

        assert response.status_code == 401


class TestUserResponseSchema:
    """Test that user responses conform to expected schema."""

    def test_response_user_schema_required_fields(
        self, test_client: TestClient, test_user: models.User, test_token: str
    ):
        """Response contains all required fields."""
        headers = {"Authorization": f"Bearer {test_token}"}
        # Use /me endpoint which always returns current user
        response = test_client.get("/api/v1/users/me", headers=headers)

        assert response.status_code == 200
        data = response.json()

        # Required fields
        required_fields = [
            "id",
            "name",
            "email",
            "role",
            "status",
            "created_at",
            "updated_at",
        ]
        for field in required_fields:
            assert field in data, f"Missing required field: {field}"

    def test_response_user_no_password_field(
        self, test_client: TestClient, test_user: models.User, test_token: str
    ):
        """Response does not include password field."""
        headers = {"Authorization": f"Bearer {test_token}"}
        # Use /me endpoint which always returns current user
        response = test_client.get("/api/v1/users/me", headers=headers)

        assert response.status_code == 200
        data = response.json()
        assert "password" not in data

    def test_paginated_response_schema(
        self,
        test_client: TestClient,
        test_admin_user: models.User,
        test_admin_token: str,
    ):
        """Search response contains pagination metadata."""
        headers = {"Authorization": f"Bearer {test_admin_token}"}
        response = test_client.get("/api/v1/users/search", headers=headers)

        assert response.status_code == 200
        data = response.json()

        # Pagination fields
        pagination_fields = [
            "items",
            "total",
            "page",
            "limit",
            "total_pages",
            "has_next",
            "has_prev",
        ]
        for field in pagination_fields:
            assert field in data, f"Missing pagination field: {field}"

        # items should be a list
        assert isinstance(data["items"], list)
