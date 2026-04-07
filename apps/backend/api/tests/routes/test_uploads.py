"""Tests for upload routes."""

from unittest.mock import AsyncMock, Mock, patch

import pytest
from fastapi.testclient import TestClient

from src.api.deps import (
    get_db_client,
    get_idempotency_service,
    get_project_service,
    get_publisher,
)
from src.main import app


@pytest.fixture
def mock_db_client():
    return Mock()


@pytest.fixture
def mock_publisher():
    return Mock()


@pytest.fixture
def mock_idempotency_service():
    service = Mock()
    service.validate_task = AsyncMock(
        return_value={
            "status": "accepted",
            "code": 202,
            "message": "Validation request published successfully",
            "data": {"task_id": "task-1", "project_id": "project-1"},
        }
    )
    service.insert_task = AsyncMock(
        return_value={
            "status": "accepted",
            "code": 202,
            "message": "Insert request published successfully",
            "data": {"task_id": "task-2", "project_id": "project-1"},
        }
    )
    service.process_task = AsyncMock(
        return_value={
            "status": "accepted",
            "code": 202,
            "message": "Process request published successfully",
            "data": {"task_id": "task-3", "project_id": "project-1"},
        }
    )
    return service


@pytest.fixture
def mock_project_service():
    service = Mock()
    service.get_project_db_uri = Mock(
        return_value="postgresql://test:test@localhost:5432/db"
    )
    return service


@pytest.fixture
def uploads_client(
    test_client: TestClient,
    mock_db_client,
    mock_publisher,
    mock_idempotency_service,
    mock_project_service,
):
    app.dependency_overrides[get_db_client] = lambda: mock_db_client
    app.dependency_overrides[get_publisher] = lambda: mock_publisher
    app.dependency_overrides[get_idempotency_service] = lambda: mock_idempotency_service
    app.dependency_overrides[get_project_service] = lambda: mock_project_service
    try:
        yield test_client
    finally:
        app.dependency_overrides.pop(get_db_client, None)
        app.dependency_overrides.pop(get_publisher, None)
        app.dependency_overrides.pop(get_idempotency_service, None)
        app.dependency_overrides.pop(get_project_service, None)


class TestUploadsRoutes:
    PROJECT_ID = "00000000-0000-0000-0000-000000000001"

    def test_validate_requires_auth(self, uploads_client: TestClient):
        response = uploads_client.post(
            "/api/v1/uploads/validate",
            data={"project_id": self.PROJECT_ID, "table_name": "users"},
            files={
                "spreadsheet_file": (
                    "users.xlsx",
                    b"test-content",
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                )
            },
        )
        assert response.status_code == 401

    def test_validate_forbidden_for_user(
        self, uploads_client: TestClient, test_token: str
    ):
        response = uploads_client.post(
            "/api/v1/uploads/validate",
            headers={"Authorization": f"Bearer {test_token}"},
            data={"project_id": self.PROJECT_ID, "table_name": "users"},
            files={
                "spreadsheet_file": (
                    "users.xlsx",
                    b"test-content",
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                )
            },
        )
        assert response.status_code == 403

    def test_validate_admin_success_with_mock(
        self, uploads_client: TestClient, test_admin_token: str
    ):
        with patch(
            "src.api.routes.uploads.PermissionService.has_permission", return_value=True
        ):
            response = uploads_client.post(
                "/api/v1/uploads/validate",
                headers={"Authorization": f"Bearer {test_admin_token}"},
                data={"project_id": self.PROJECT_ID, "table_name": "users"},
                files={
                    "spreadsheet_file": (
                        "users.xlsx",
                        b"test-content",
                        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    )
                },
            )

        assert response.status_code == 200
        assert response.json()["status"] == "accepted"

    def test_process_admin_success_with_mock(
        self, uploads_client: TestClient, test_admin_token: str
    ):
        with patch(
            "src.api.routes.uploads.PermissionService.has_permission", return_value=True
        ):
            response = uploads_client.post(
                "/api/v1/uploads/process",
                headers={"Authorization": f"Bearer {test_admin_token}"},
                data={"project_id": self.PROJECT_ID, "table_name": "users"},
                files={
                    "spreadsheet_file": (
                        "users.xlsx",
                        b"test-content",
                        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    )
                },
            )

        assert response.status_code == 200
        assert response.json()["status"] == "accepted"

    def test_table_json_requires_auth(self, uploads_client: TestClient):
        response = uploads_client.post(
            "/api/v1/uploads/table-json?execute_sql=false",
            json={
                "project_id": self.PROJECT_ID,
                "table_name": "users",
                "jsonschema": {
                    "$schema": "https://json-schema.org/draft-07/schema",
                    "type": "object",
                    "properties": {"id": {"type": "string"}},
                    "required": ["id"],
                },
                "primary_keys": ["id"],
            },
        )
        assert response.status_code == 401
