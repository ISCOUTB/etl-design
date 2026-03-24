"""Unit tests for schema handlers.

The current handlers.schemas module only exposes get_active_schema.
"""

from unittest.mock import MagicMock

from src.handlers.schemas import get_active_schema


class TestGetActiveSchema:
    def test_get_active_schema_found(self):
        mock_db_client = MagicMock()
        mock_schema = {
            "type": "object",
            "properties": {"name": {"type": "string"}},
        }
        mock_db_client.mongo_find_jsonschema.return_value = {
            "status": "found",
            "schema": mock_schema,
        }

        result = get_active_schema("project_a__customers", mock_db_client)

        assert result == mock_schema
        mock_db_client.mongo_find_jsonschema.assert_called_once()
        req = mock_db_client.mongo_find_jsonschema.call_args.args[0]
        assert req["import_name"] == "project_a__customers"

    def test_get_active_schema_not_found_returns_none(self):
        mock_db_client = MagicMock()
        mock_db_client.mongo_find_jsonschema.return_value = {
            "status": "not_found",
            "schema": None,
        }

        result = get_active_schema("project_a__missing", mock_db_client)

        assert result is None
        mock_db_client.mongo_find_jsonschema.assert_called_once()

    def test_get_active_schema_propagates_database_error(self):
        mock_db_client = MagicMock()
        mock_db_client.mongo_find_jsonschema.side_effect = RuntimeError(
            "db unavailable"
        )

        try:
            get_active_schema("project_a__customers", mock_db_client)
            assert False, "Expected RuntimeError"
        except RuntimeError as exc:
            assert "db unavailable" in str(exc)
