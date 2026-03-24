"""Unit tests for validation handlers."""

from unittest.mock import MagicMock, patch

import pytest

from src.handlers.validation import (
    _convert_data_types,
    get_validation_summary,
    validate_chunks,
    validate_data_parallel,
    validate_file_against_schema,
)


class TestConvertDataTypes:
    def test_convert_boolean_and_integer(self):
        schema = {
            "type": "object",
            "properties": {
                "active": {"type": "boolean"},
                "age": {"type": "integer"},
            },
        }
        data = [{"active": "true", "age": "25.0"}, {"active": "false", "age": "30"}]

        result = _convert_data_types(data, schema)

        assert result[0]["active"] is True
        assert result[1]["active"] is False
        assert result[0]["age"] == 25
        assert isinstance(result[0]["age"], int)

    def test_convert_number_and_none(self):
        schema = {"type": "object", "properties": {"score": {"type": "number"}}}
        data = [{"score": "95.5"}, {"score": ""}, {"score": None}]

        result = _convert_data_types(data, schema)

        assert result[0]["score"] == 95.5
        assert result[1]["score"] is None
        assert result[2]["score"] is None


class TestValidateChunks:
    def test_validate_chunks_all_valid(self):
        schema = {
            "type": "object",
            "properties": {"name": {"type": "string"}},
            "required": ["name"],
        }
        data = [{"name": "a"}, {"name": "b"}]

        index, is_valid, errors = validate_chunks((data, schema, 0))

        assert index == 0
        assert is_valid is True
        assert errors == []

    def test_validate_chunks_with_errors(self):
        schema = {
            "type": "object",
            "properties": {"age": {"type": "integer"}},
            "required": ["age"],
        }
        data = [{"age": "bad"}]

        _, is_valid, errors = validate_chunks((data, schema, 0))

        assert is_valid is False
        assert len(errors) == 1


class TestValidateDataParallel:
    @patch("src.handlers.validation.mp.Pool")
    def test_validate_data_parallel_valid(self, mock_pool_cls):
        mock_pool = MagicMock()
        mock_pool.map.return_value = [(0, True, []), (1, True, [])]
        mock_pool_cls.return_value.__enter__.return_value = mock_pool

        data = [{"a": 1}, {"a": 2}]
        schema = {"type": "object", "properties": {"a": {"type": "integer"}}}

        result = validate_data_parallel(data, schema, n_workers=2)

        assert result["is_valid"] is True
        assert result["errors"] == []
        assert "total_items" in result

    def test_validate_data_parallel_empty(self):
        result = validate_data_parallel([], {"type": "object"}, n_workers=1)

        assert result["is_valid"] is True
        assert result["total_items"] == 0


class TestGetValidationSummary:
    def test_summary_success(self):
        validation_result = {
            "success": True,
            "error": None,
            "validation_results": {
                "is_valid": True,
                "total_items": 5,
                "valid_items": 5,
                "invalid_items": 0,
                "errors": [],
                "file_name": "data.csv",
                "validated_at": "2026-01-01T00:00:00",
            },
        }

        summary = get_validation_summary(validation_result)

        assert summary["status"] == "success"
        assert "All 5 items" in summary["summary"]

    def test_summary_warning(self):
        validation_result = {
            "success": True,
            "error": None,
            "validation_results": {
                "is_valid": False,
                "total_items": 5,
                "valid_items": 3,
                "invalid_items": 2,
                "errors": ["e1", "e2"],
            },
        }

        summary = get_validation_summary(validation_result)

        assert summary["status"] == "warning"
        assert summary["details"]["error_count"] == 2


class TestValidateFileAgainstSchema:
    @pytest.mark.asyncio
    @patch("src.handlers.validation.get_active_schema")
    async def test_validate_file_no_schema_found(
        self,
        mock_get_schema,
        sample_upload_file_csv,
    ):
        mock_get_schema.return_value = None
        db_client = MagicMock()

        result = await validate_file_against_schema(
            sample_upload_file_csv,
            "project_a__missing",
            db_client,
        )

        assert result["success"] is False
        assert "No active schema found" in result["error"]

    @pytest.mark.asyncio
    @patch("src.handlers.validation.get_active_schema")
    @patch("src.handlers.validation.FileProcessor.process_file")
    async def test_validate_file_processing_error(
        self,
        mock_process_file,
        mock_get_schema,
        sample_upload_file_csv,
        sample_json_schema,
    ):
        mock_get_schema.return_value = sample_json_schema
        mock_process_file.return_value = (False, [], "Failed to process file")
        db_client = MagicMock()

        result = await validate_file_against_schema(
            sample_upload_file_csv,
            "project_a__customers",
            db_client,
        )

        assert result["success"] is False
        assert result["error"] == "Failed to process file"

    @pytest.mark.asyncio
    @patch("src.handlers.validation.get_active_schema")
    @patch("src.handlers.validation.FileProcessor.process_file")
    async def test_validate_file_columns_mismatch(
        self,
        mock_process_file,
        mock_get_schema,
        sample_upload_file_csv,
        sample_json_schema,
    ):
        mock_get_schema.return_value = sample_json_schema
        mock_process_file.return_value = (True, [{"wrong": "value"}], None)
        db_client = MagicMock()

        result = await validate_file_against_schema(
            sample_upload_file_csv,
            "project_a__customers",
            db_client,
        )

        assert result["success"] is False
        assert "Columns do not match schema properties" in result["error"]

    @pytest.mark.asyncio
    @patch("src.handlers.validation.validate_data_parallel")
    @patch("src.handlers.validation.FileProcessor.get_file_info")
    @patch("src.handlers.validation.FileProcessor.process_file")
    @patch("src.handlers.validation.get_active_schema")
    async def test_validate_file_success(
        self,
        mock_get_schema,
        mock_process_file,
        mock_get_file_info,
        mock_validate_parallel,
        sample_upload_file_csv,
        sample_json_schema,
        sample_valid_data,
    ):
        mock_get_schema.return_value = sample_json_schema
        mock_process_file.return_value = (True, sample_valid_data, None)
        mock_get_file_info.return_value = {
            "filename": "test.csv",
            "size": 1024,
            "content_type": "text/csv",
        }
        mock_validate_parallel.return_value = {
            "is_valid": True,
            "total_items": 10,
            "valid_items": 10,
            "invalid_items": 0,
            "errors": [],
        }
        db_client = MagicMock()

        result = await validate_file_against_schema(
            sample_upload_file_csv,
            "project_a__customers",
            db_client,
            n_workers=2,
        )

        assert result["success"] is True
        assert result["error"] is None
        assert result["validation_results"]["is_valid"] is True
        assert result["validation_results"]["import_name"] == "project_a__customers"
