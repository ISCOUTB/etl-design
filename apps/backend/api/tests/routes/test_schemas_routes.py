"""Tests for schema management routes."""

from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from src import schemas as app_schemas


class TestSchemasRoutes:
    PROJECT_ID = "00000000-0000-0000-0000-000000000001"

    def test_create_schema_requires_auth(self, test_client: TestClient):
        response = test_client.post(
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
        self, test_client: TestClient, test_token: str
    ):
        response = test_client.post(
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
        self, test_client: TestClient, test_admin_token: str
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
            response = test_client.post(
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
        self, test_client: TestClient, test_admin_token: str
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
            response = test_client.get(
                f"/api/v1/schemas/{self.PROJECT_ID}/raw?table_name=users",
                headers={"Authorization": f"Bearer {test_admin_token}"},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "schema-1"
        assert data["import_name"] == f"{self.PROJECT_ID}__users"

    def test_search_schemas_admin_success_with_mock(
        self, test_client: TestClient, test_admin_token: str
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
            response = test_client.get(
                f"/api/v1/schemas/search/{self.PROJECT_ID}",
                headers={"Authorization": f"Bearer {test_admin_token}"},
            )

        assert response.status_code == 200
        assert response.json()["schemas"] == []
