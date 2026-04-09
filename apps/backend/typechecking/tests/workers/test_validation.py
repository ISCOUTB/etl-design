"""Unit tests for ValidationWorker.

These tests are aligned with the current worker contract:
- input messages use project_id/table_name
- validation results are published to the results routing key
- insertion is optionally triggered through insertion routing key
"""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import UploadFile

import src.workers.validation as validation_module
from src.schemas.workers import ResultsMessage
from src.workers.validation import ValidationWorker


@pytest.fixture
def mock_db_client():
    """Create a mock DatabaseClient with sane defaults for idempotency checks."""
    client = MagicMock()
    client.get_task_id = MagicMock(return_value={"found": False, "value": None})
    client.set_task_id = MagicMock()
    client.update_task_id = MagicMock()
    return client


@pytest.fixture
def validation_worker(mock_db_client):
    """Create ValidationWorker with mocked DB client."""
    with patch(
        "src.workers.validation.get_database_client", return_value=mock_db_client
    ):
        return ValidationWorker(
            max_retries=5,
            retry_delay=2.0,
            backoff=2.0,
            threshold=60.0,
        )


@pytest.fixture
def sample_validation_message():
    """Create a message compatible with messaging_utils.schemas.ValidationMessage."""
    file_data = b"col1,col2\nvalue1,value2\n"
    return {
        "id": "task_123",
        "task": "sample_validation",
        "file_data": file_data.hex(),
        "project_id": "project_a",
        "table_name": "customers",
        "metadata": {
            "filename": "test_file.csv",
            "content_type": "text/csv",
            "size": len(file_data),
        },
        "date": "2024-01-01T00:00:00",
        "extra": {},
        "insert": False,
        "insert_table_name": None,
        "insert_overwrite": None,
        "insert_db_uri": None,
        "idempotency_key": "idem-123",
        "traceparent": None,
        "tracestate": None,
        "baggage": None,
    }


class TestValidationWorkerInitialization:
    def test_worker_initialization(self, validation_worker):
        assert validation_worker.TASK == "validation"
        assert validation_worker.max_retries == 5
        assert validation_worker.retry_delay == 2.0
        assert validation_worker.backoff == 2.0
        assert validation_worker.threshold == 60.0
        assert validation_worker.connection is None
        assert validation_worker.channel is None
        assert validation_worker.db_client is not None


class TestProcessValidationRequest:
    def test_process_validation_request_success(
        self, validation_worker, sample_validation_message
    ):
        mock_channel = MagicMock()
        mock_method = MagicMock(delivery_tag="delivery_1")

        result = {
            "task_id": "task_123",
            "status": "success",
            "results": {"status": "success", "details": {"error_count": 0}},
        }
        validation_worker._validate_data = AsyncMock(return_value=result)
        validation_worker._publish_result = MagicMock()

        validation_worker.process_validation_request(
            mock_channel,
            mock_method,
            MagicMock(),
            json.dumps(sample_validation_message).encode(),
        )

        validation_worker._publish_result.assert_called_once_with(
            "task_123", result, db_client=validation_worker.db_client
        )
        mock_channel.basic_ack.assert_called_once_with(delivery_tag="delivery_1")

    def test_process_validation_request_invalid_json_raises(self, validation_worker):
        mock_channel = MagicMock()
        mock_method = MagicMock(delivery_tag="delivery_2")

        with pytest.raises(json.JSONDecodeError):
            validation_worker.process_validation_request(
                mock_channel,
                mock_method,
                MagicMock(),
                b"not-json",
            )

    def test_infrastructure_error_requeues(
        self,
        validation_worker,
        sample_validation_message,
    ):
        validation_worker._validate_data = AsyncMock(
            side_effect=ConnectionError("db down")
        )

        mock_channel = MagicMock()
        mock_method = MagicMock(delivery_tag="delivery_3")

        validation_worker.process_validation_request(
            mock_channel,
            mock_method,
            MagicMock(),
            json.dumps(sample_validation_message).encode(),
        )

        mock_channel.basic_nack.assert_called_once_with(
            delivery_tag="delivery_3", requeue=True
        )

    def test_unknown_task_is_ackd(self, validation_worker, sample_validation_message):
        mock_channel = MagicMock()
        mock_method = MagicMock(delivery_tag="delivery_4")
        body = {
            **sample_validation_message,
            "task": "unknown",
        }

        validation_worker.process_validation_request(
            mock_channel,
            mock_method,
            MagicMock(),
            json.dumps(body).encode(),
        )

        mock_channel.basic_ack.assert_called_once_with(delivery_tag="delivery_4")

    @patch("src.workers.validation.get_task_status", return_value="success")
    def test_completed_task_is_ackd_without_reprocessing(
        self,
        _mock_get_status,
        validation_worker,
        sample_validation_message,
    ):
        mock_channel = MagicMock()
        mock_method = MagicMock(delivery_tag="delivery_5")

        validation_worker.process_validation_request(
            mock_channel,
            mock_method,
            MagicMock(),
            json.dumps(sample_validation_message).encode(),
        )

        mock_channel.basic_ack.assert_called_once_with(delivery_tag="delivery_5")
        assert validation_worker.db_client.set_task_id.call_count == 0

    def test_success_with_insert_publishes_insertion_message(
        self,
        validation_worker,
        sample_validation_message,
    ):
        msg = {
            **sample_validation_message,
            "insert": True,
            "insert_overwrite": True,
            "insert_db_uri": "mongodb://localhost:27017/db",
        }
        validation_worker._validate_data = AsyncMock(
            return_value={
                "task_id": "task_123",
                "status": "success",
                "results": {"status": "success"},
            }
        )
        validation_worker._publish_result = MagicMock()
        validation_worker.channel = MagicMock()

        mock_channel = MagicMock()
        mock_method = MagicMock(delivery_tag="delivery_6")
        validation_worker.process_validation_request(
            mock_channel,
            mock_method,
            MagicMock(),
            json.dumps(msg).encode(),
        )

        validation_worker.channel.basic_publish.assert_called_once()
        call_kwargs = validation_worker.channel.basic_publish.call_args.kwargs
        assert (
            call_kwargs["routing_key"]
            == validation_module.mq_settings.RABBITMQ_PUBLISHERS_ROUTING_KEY_INSERTION
        )
        body = json.loads(call_kwargs["body"])
        assert body["id"] == "task_123"
        assert body["task"] == "sample_insertion"
        assert body["db_uri"] == "mongodb://localhost:27017/db"


class TestValidateData:
    @pytest.mark.asyncio
    @patch("src.workers.validation.update_task_status")
    @patch("src.workers.validation.get_validation_summary")
    @patch("src.workers.validation.validate_file_against_schema")
    async def test_validate_data_success(
        self,
        mock_validate_file,
        mock_get_summary,
        mock_update_status,
        validation_worker,
        sample_validation_message,
    ):
        mock_validate_file.return_value = {
            "validation_results": {"is_valid": True},
            "error": None,
        }
        mock_get_summary.return_value = {
            "status": "success",
            "summary": "ok",
            "details": {"error_count": 0},
        }

        result = await validation_worker._validate_data(
            sample_validation_message, db_client=validation_worker.db_client
        )

        assert result["task_id"] == "task_123"
        assert result["status"] == "success"

        mock_validate_file.assert_called_once()
        validate_kwargs = mock_validate_file.call_args.kwargs
        uploaded_file = validate_kwargs["file"]
        assert isinstance(uploaded_file, UploadFile)
        assert uploaded_file.filename == "test_file.csv"
        assert validate_kwargs["import_name"] == "project_a__customers"

        assert mock_update_status.call_count == 3
        called_statuses = [
            c.kwargs["value"]
            for c in mock_update_status.call_args_list
            if c.kwargs.get("field") == "status"
        ]
        assert "processing-file" in called_statuses
        assert "validating-file" in called_statuses
        assert "success" in called_statuses

    @pytest.mark.asyncio
    @patch(
        "src.workers.validation.get_validation_summary",
        return_value={"status": "success"},
    )
    @patch("src.workers.validation.validate_file_against_schema")
    async def test_validate_data_converts_hex_file_content(
        self,
        mock_validate_file,
        _mock_get_summary,
        validation_worker,
        sample_validation_message,
    ):
        content = b"A,B\n1,2\n"
        message = {**sample_validation_message, "file_data": content.hex()}
        mock_validate_file.return_value = {
            "validation_results": {"is_valid": True},
            "error": None,
        }

        await validation_worker._validate_data(
            message, db_client=validation_worker.db_client
        )

        upload = mock_validate_file.call_args.kwargs["file"]
        assert upload.file.read() == content


class TestPublishResult:
    @patch("src.workers.validation.update_task_status")
    def test_publish_result_uses_results_routing_key(
        self,
        mock_update_status,
        validation_worker,
    ):
        validation_worker.channel = MagicMock()
        result = ResultsMessage(
            task_id="task_pub",
            project_id="project_a",
            import_name="project_a__customers",
            status="success",
            results={"status": "success"},
            error="",
            traceparent=None,
            tracestate=None,
            baggage=None,
        )

        validation_worker._publish_result(
            "task_pub", result, db_client=validation_worker.db_client
        )

        validation_worker.channel.basic_publish.assert_called_once()
        kwargs = validation_worker.channel.basic_publish.call_args.kwargs
        assert kwargs["exchange"] == validation_module.mq_settings.RABBITMQ_EXCHANGE
        assert (
            kwargs["routing_key"]
            == validation_module.mq_settings.RABBITMQ_PUBLISHERS_ROUTING_KEY_RESULTS
        )
        payload = json.loads(kwargs["body"])
        assert payload["task_id"] == "task_pub"
        assert payload["status"] == "success"
        assert payload["results"] == {"status": json.dumps("success")}
        assert payload["error"] == ""
        assert payload["traceparent"] is None
        assert payload["tracestate"] is None
        assert payload["baggage"] is None

        mock_update_status.assert_called_once()
        assert mock_update_status.call_args.kwargs["value"] == "published"


class TestStopConsuming:
    def test_stop_consuming_closes_channel_and_connections(self, validation_worker):
        validation_worker.channel = MagicMock(is_open=True)

        with patch(
            "src.workers.validation.RabbitMQConnectionFactory.close_thread_connections"
        ) as mock_close:
            validation_worker.stop_consuming()

        validation_worker.channel.stop_consuming.assert_called_once()
        mock_close.assert_called_once()

    def test_stop_consuming_with_closed_channel_does_not_raise(self, validation_worker):
        validation_worker.channel = MagicMock(is_open=False)
        validation_worker.stop_consuming()
