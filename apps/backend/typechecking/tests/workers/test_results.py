"""Unit tests for ResultWorker.

Covers the new results queue consumer behavior and idempotency paths.
"""

import json
from unittest.mock import MagicMock, patch

import pytest

from src.schemas.workers import ResultsMessage
from src.workers.results import ResultWorker


@pytest.fixture
def mock_db_client():
    client = MagicMock()
    client.get_task_id = MagicMock(return_value={"found": False, "value": None})
    client.set_task_id = MagicMock()
    client.update_task_id = MagicMock()
    return client


@pytest.fixture
def result_worker(mock_db_client):
    with patch("src.workers.results.get_database_client", return_value=mock_db_client):
        return ResultWorker(
            max_retries=5,
            retry_delay=2.0,
            backoff=2.0,
            threshold=60.0,
        )


@pytest.fixture
def sample_results_message() -> ResultsMessage:
    return ResultsMessage(
        task_id="task_result_1",
        project_id="project_1",
        import_name="test_import",
        results={"status": "success", "details": {"error_count": 0}},
        status="success",
        error="",
        traceparent=None,
        tracestate=None,
        baggage=None,
    )


class TestResultQueueWorker:
    def test_process_results_success_acks(self, result_worker, sample_results_message):
        result_worker._notify_task_completion = MagicMock(return_value=None)

        mock_channel = MagicMock()
        mock_method = MagicMock(delivery_tag="delivery_result_1")

        result_worker.process_results_request(
            mock_channel,
            mock_method,
            MagicMock(),
            json.dumps(sample_results_message).encode(),
        )

        result_worker._notify_task_completion.assert_called_once()
        mock_channel.basic_ack.assert_called_once_with(delivery_tag="delivery_result_1")

    @patch("src.workers.results.get_task_status", return_value="completed")
    def test_completed_results_task_is_skipped(
        self,
        _mock_get_status,
        result_worker,
        sample_results_message,
    ):
        mock_channel = MagicMock()
        mock_method = MagicMock(delivery_tag="delivery_result_2")

        result_worker.process_results_request(
            mock_channel,
            mock_method,
            MagicMock(),
            json.dumps(sample_results_message).encode(),
        )

        mock_channel.basic_ack.assert_called_once_with(delivery_tag="delivery_result_2")

    @patch("src.workers.results.get_task_status", return_value="notifying")
    def test_notifying_results_task_is_skipped(
        self,
        _mock_get_status,
        result_worker,
        sample_results_message,
    ):
        mock_channel = MagicMock()
        mock_method = MagicMock(delivery_tag="delivery_result_3")

        result_worker.process_results_request(
            mock_channel,
            mock_method,
            MagicMock(),
            json.dumps(sample_results_message).encode(),
        )

        mock_channel.basic_ack.assert_called_once_with(delivery_tag="delivery_result_3")

    def test_results_infrastructure_error_requeues(
        self, result_worker, sample_results_message
    ):
        result_worker._notify_task_completion = MagicMock(
            side_effect=ConnectionError("api down")
        )

        mock_channel = MagicMock()
        mock_method = MagicMock(delivery_tag="delivery_result_4")

        result_worker.process_results_request(
            mock_channel,
            mock_method,
            MagicMock(),
            json.dumps(sample_results_message).encode(),
        )

        mock_channel.basic_nack.assert_called_once_with(
            delivery_tag="delivery_result_4", requeue=True
        )


class TestNotifyTaskCompletion:
    @patch("src.workers.results.update_task_status")
    @patch("src.workers.results.post_json_http_with_ssl_fallback")
    def test_notify_task_completion_success_sets_completed(
        self,
        mock_post_json,
        mock_update_status,
        result_worker,
        sample_results_message,
    ):
        mock_post_json.return_value = 200

        result_worker._notify_task_completion(
            "task_result_1", sample_results_message, sample_results_message
        )

        mock_post_json.assert_called_once()
        kwargs = mock_post_json.call_args.kwargs
        assert kwargs["payload"]["task_id"] == "task_result_1"
        assert kwargs["payload"]["status"] == "success"

        assert mock_update_status.call_count == 1
        assert mock_update_status.call_args.kwargs["value"] == "completed"

    @patch("src.workers.results.update_task_status")
    @patch("src.workers.results.post_json_http_with_ssl_fallback")
    def test_notify_task_completion_failure_sets_failed(
        self,
        mock_post_json,
        mock_update_status,
        result_worker,
        sample_results_message,
    ):
        mock_post_json.side_effect = Exception("request failed")

        result_worker._notify_task_completion(
            "task_result_1", sample_results_message, sample_results_message
        )

        assert mock_update_status.call_count == 1
        assert mock_update_status.call_args.kwargs["value"] == "failed"
