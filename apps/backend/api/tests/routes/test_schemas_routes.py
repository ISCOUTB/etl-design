"""Tests for schema management routes."""

from unittest.mock import AsyncMock, Mock, patch

import pytest
from fastapi.testclient import TestClient

from src import schemas as app_schemas
from src.api.deps import get_project_service
from src.main import app


@pytest.fixture
def mock_project_service():
    service = Mock()
    service.get_project_by_id = Mock(return_value=object())
    return service


@pytest.fixture
def schemas_client(test_client: TestClient, mock_project_service):
    app.dependency_overrides[get_project_service] = lambda: mock_project_service
    try:
        yield test_client
    finally:
        app.dependency_overrides.pop(get_project_service, None)


class TestSchemasRoutes:
    PROJECT_ID = "00000000-0000-0000-0000-000000000001"

    def test_create_schema_requires_auth(self, schemas_client: TestClient):
        response = schemas_client.post(
            f"/api/v1/schemas/{self.PROJECT_ID}?table_name=users",
            json={
                "$schema": "https://json-schema.org/draft-07/schema",
                "type": "object",
                "properties": {"id": {"type": "string"}},
                "required": ["id"],
            },
        )
        assert response.status_code == 401

    def test_create_schema_forbidden_for_user(
        self, schemas_client: TestClient, test_token: str
    ):
        response = schemas_client.post(
            f"/api/v1/schemas/{self.PROJECT_ID}?table_name=users",
            headers={"Authorization": f"Bearer {test_token}"},
            json={
                "$schema": "https://json-schema.org/draft-07/schema",
                "type": "object",
                "properties": {"id": {"type": "string"}},
                "required": ["id"],
            },
        )
        assert response.status_code == 403

    def test_create_schema_admin_success_with_mocks(
        self, schemas_client: TestClient, test_admin_token: str
    ):
        with (
            patch(
                "src.api.routes.schemas.PermissionService.has_permission",
                return_value=True,
            ),
            patch(
                "src.api.routes.schemas.SchemaService.save_schema",
                new=AsyncMock(return_value={"status": "inserted", "result": {}}),
            ),
            patch(
                "src.api.routes.schemas.SchemaService.map_db_response_to_api",
                return_value={
                    "status": "success",
                    "code": 200,
                    "message": "Schema created successfully",
                    "data": {},
                },
            ),
        ):
            response = schemas_client.post(
                f"/api/v1/schemas/{self.PROJECT_ID}?table_name=users",
                headers={"Authorization": f"Bearer {test_admin_token}"},
                json={
                    "$schema": "https://json-schema.org/draft-07/schema",
                    "type": "object",
                    "properties": {"id": {"type": "string"}},
                    "required": ["id"],
                },
            )

        assert response.status_code == 200
        assert response.json()["status"] == "success"

    def test_get_raw_schema_admin_success_with_mock(
        self, schemas_client: TestClient, test_admin_token: str
    ):
        mock_schema = app_schemas.MongoSchemasResponse(
            id="schema-1",
            import_name=f"{self.PROJECT_ID}__users",
            created_at="2026-03-24T00:00:00+00:00",
            active_schema={
                "$schema": "https://json-schema.org/draft-07/schema",
                "type": "object",
                "properties": {"id": {"type": "string"}},
                "required": ["id"],
            },
            schemas_releases=[],
        )

        with (
            patch(
                "src.api.routes.schemas.PermissionService.has_permission",
                return_value=True,
            ),
            patch(
                "src.api.routes.schemas.SchemaService.get_raw_schema",
                new=AsyncMock(return_value=mock_schema),
            ),
        ):
            response = schemas_client.get(
                f"/api/v1/schemas/{self.PROJECT_ID}/raw?table_name=users",
                headers={"Authorization": f"Bearer {test_admin_token}"},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "schema-1"
        assert data["import_name"] == f"{self.PROJECT_ID}__users"

    def test_search_schemas_admin_success_with_mock(
        self, schemas_client: TestClient, test_admin_token: str
    ):
        with (
            patch(
                "src.api.routes.schemas.PermissionService.has_permission",
                return_value=True,
            ),
            patch(
                "src.api.routes.schemas.SchemaService.get_schemas_by_project_id",
                new=AsyncMock(
                    return_value=app_schemas.MongoGetSchemasByImportResponse(schemas=[])
                ),
            ),
        ):
            response = schemas_client.get(
                f"/api/v1/schemas/search/{self.PROJECT_ID}",
                headers={"Authorization": f"Bearer {test_admin_token}"},
            )

        assert response.status_code == 200
        assert response.json()["schemas"] == []
