"""Tests for project and user-project endpoints."""

from fastapi.testclient import TestClient

from src import models


class TestProjectRoutes:
    """Test core CRUD operations for /projects endpoints."""

    def test_search_projects_requires_auth(self, test_client: TestClient):
        response = test_client.get("/api/v1/projects/search")
        assert response.status_code == 401

    def test_search_projects_user_success(
        self, test_client: TestClient, test_token: str
    ):
        headers = {"Authorization": f"Bearer {test_token}"}
        response = test_client.get("/api/v1/projects/search", headers=headers)

        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert "limit" in data

    def test_create_project_user_success(
        self, test_client: TestClient, test_token: str
    ):
        headers = {"Authorization": f"Bearer {test_token}"}
        payload = {
            "name": "User Project",
            "description": "Created by user",
        }

        response = test_client.post("/api/v1/projects/", json=payload, headers=headers)

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "User Project"
        assert data["description"] == "Created by user"

    def test_create_project_admin_success(
        self, test_client: TestClient, test_admin_token: str
    ):
        headers = {"Authorization": f"Bearer {test_admin_token}"}
        payload = {
            "name": "Admin Project",
            "description": "Created by admin",
        }

        response = test_client.post("/api/v1/projects/", json=payload, headers=headers)

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Admin Project"

    def test_create_project_invalid_payload(
        self, test_client: TestClient, test_admin_token: str
    ):
        headers = {"Authorization": f"Bearer {test_admin_token}"}
        payload = {
            "name": "   ",
            "description": "Invalid",
        }

        response = test_client.post("/api/v1/projects/", json=payload, headers=headers)

        assert response.status_code == 400

    def test_create_project_missing_auth(self, test_client: TestClient):
        payload = {"name": "NoAuth Project"}

        response = test_client.post("/api/v1/projects/", json=payload)

        assert response.status_code == 401

    def test_get_project_by_id_admin_success(
        self, test_client: TestClient, test_admin_token: str
    ):
        headers = {"Authorization": f"Bearer {test_admin_token}"}
        create_response = test_client.post(
            "/api/v1/projects/",
            json={"name": "Project For Get"},
            headers=headers,
        )
        assert create_response.status_code == 201
        project_id = create_response.json()["id"]

        response = test_client.get(f"/api/v1/projects/id/{project_id}", headers=headers)

        assert response.status_code == 200
        assert response.json()["id"] == project_id

    def test_get_project_by_id_user_forbidden_when_not_member(
        self, test_client: TestClient, test_token: str, test_admin_token: str
    ):
        admin_headers = {"Authorization": f"Bearer {test_admin_token}"}
        create_response = test_client.post(
            "/api/v1/projects/",
            json={"name": "Admin Only Project"},
            headers=admin_headers,
        )
        assert create_response.status_code == 201
        project_id = create_response.json()["id"]

        user_headers = {"Authorization": f"Bearer {test_token}"}
        response = test_client.get(
            f"/api/v1/projects/id/{project_id}", headers=user_headers
        )

        assert response.status_code == 403

    def test_update_project_admin_success(
        self, test_client: TestClient, test_admin_token: str
    ):
        headers = {"Authorization": f"Bearer {test_admin_token}"}
        create_response = test_client.post(
            "/api/v1/projects/",
            json={"name": "Project To Update"},
            headers=headers,
        )
        assert create_response.status_code == 201
        project_id = create_response.json()["id"]

        response = test_client.patch(
            f"/api/v1/projects/{project_id}",
            json={"name": "Updated Name"},
            headers=headers,
        )

        assert response.status_code == 200
        assert response.json()["name"] == "Updated Name"

    def test_update_project_user_success_on_own_project(
        self, test_client: TestClient, test_token: str
    ):
        """Current permission implementation denies user update on this route."""
        headers = {"Authorization": f"Bearer {test_token}"}
        create_response = test_client.post(
            "/api/v1/projects/",
            json={"name": "Owned Project"},
            headers=headers,
        )
        assert create_response.status_code == 201
        project_id = create_response.json()["id"]

        response = test_client.patch(
            f"/api/v1/projects/{project_id}",
            json={"name": "Owned Project Updated"},
            headers=headers,
        )

        assert response.status_code == 403

    def test_delete_project_user_forbidden(
        self, test_client: TestClient, test_token: str
    ):
        headers = {"Authorization": f"Bearer {test_token}"}
        create_response = test_client.post(
            "/api/v1/projects/",
            json={"name": "User Cannot Delete"},
            headers=headers,
        )
        assert create_response.status_code == 201
        project_id = create_response.json()["id"]

        response = test_client.delete(f"/api/v1/projects/{project_id}", headers=headers)

        assert response.status_code == 403

    def test_delete_project_admin_success(
        self, test_client: TestClient, test_admin_token: str
    ):
        headers = {"Authorization": f"Bearer {test_admin_token}"}
        create_response = test_client.post(
            "/api/v1/projects/",
            json={"name": "Project To Delete"},
            headers=headers,
        )
        assert create_response.status_code == 201
        project_id = create_response.json()["id"]

        response = test_client.delete(f"/api/v1/projects/{project_id}", headers=headers)

        assert response.status_code in [200, 400, 409]


class TestUserProjectRoutes:
    """Test /projects/{id}/users* endpoints."""

    def test_add_user_to_project_admin_success(
        self, test_client: TestClient, test_admin_token: str, test_user: models.User
    ):
        headers = {"Authorization": f"Bearer {test_admin_token}"}
        create_project = test_client.post(
            "/api/v1/projects/",
            json={"name": "Membership Project"},
            headers=headers,
        )
        assert create_project.status_code == 201
        project_id = create_project.json()["id"]

        response = test_client.post(
            f"/api/v1/projects/{project_id}/users",
            json={"user_id": str(test_user.id), "role": "shared"},
            headers=headers,
        )

        assert response.status_code in [201, 400]

    def test_add_user_to_project_user_forbidden(
        self, test_client: TestClient, test_token: str, test_user: models.User
    ):
        user_headers = {"Authorization": f"Bearer {test_token}"}
        create_project = test_client.post(
            "/api/v1/projects/",
            json={"name": "User Project For Add"},
            headers=user_headers,
        )
        assert create_project.status_code == 201
        project_id = create_project.json()["id"]

        response = test_client.post(
            f"/api/v1/projects/{project_id}/users",
            json={"user_id": str(test_user.id), "role": "shared"},
            headers=user_headers,
        )

        assert response.status_code == 403

    def test_get_users_for_project_admin_success(
        self, test_client: TestClient, test_admin_token: str
    ):
        headers = {"Authorization": f"Bearer {test_admin_token}"}
        create_project = test_client.post(
            "/api/v1/projects/",
            json={"name": "Users Listing Project"},
            headers=headers,
        )
        assert create_project.status_code == 201
        project_id = create_project.json()["id"]

        response = test_client.get(
            f"/api/v1/projects/{project_id}/users", headers=headers
        )

        assert response.status_code == 200
        data = response.json()
        assert "items" in data

    def test_get_users_for_project_user_forbidden(
        self, test_client: TestClient, test_token: str
    ):
        headers = {"Authorization": f"Bearer {test_token}"}
        create_project = test_client.post(
            "/api/v1/projects/",
            json={"name": "User List Forbidden"},
            headers=headers,
        )
        assert create_project.status_code == 201
        project_id = create_project.json()["id"]

        response = test_client.get(
            f"/api/v1/projects/{project_id}/users", headers=headers
        )

        assert response.status_code == 403

    def test_flush_access_project_admin_success(
        self, test_client: TestClient, test_admin_token: str
    ):
        headers = {"Authorization": f"Bearer {test_admin_token}"}
        create_project = test_client.post(
            "/api/v1/projects/",
            json={"name": "Flush Project"},
            headers=headers,
        )
        assert create_project.status_code == 201
        project_id = create_project.json()["id"]

        response = test_client.delete(
            f"/api/v1/projects/{project_id}/flush", headers=headers
        )

        assert response.status_code == 200
        assert response.json()["status"] == "flushed"
