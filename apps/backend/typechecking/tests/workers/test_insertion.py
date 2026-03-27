"""Unit tests for InsertionWorker (legacy filename).

Historically this file tested the old schema queue worker. Since that queue was
removed, it now validates the insertion worker behavior (insert queue).
"""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

import src.workers.insertion as insertion_module
from src.workers.insertion import InsertionWorker


@pytest.fixture
def mock_db_client():
    client = MagicMock()
    client.get_task_id = MagicMock(return_value={"found": False, "value": None})
    client.set_task_id = MagicMock()
    client.update_task_id = MagicMock()
    return client


@pytest.fixture
def insertion_worker(mock_db_client):
    with patch(
        "src.workers.insertion.get_database_client", return_value=mock_db_client
    ):
        return InsertionWorker(
            max_retries=5,
            retry_delay=2.0,
            backoff=2.0,
            threshold=60.0,
        )


@pytest.fixture
def sample_insertion_message():
    file_data = b"col1,col2\nvalue1,value2\n"
    return {
        "id": "task_insert_1",
        "task": "sample_insertion",
        "file_data": file_data.hex(),
        "project_id": "project_a",
        "table_name": "customers",
        "metadata": {
            "filename": "to_insert.csv",
            "content_type": "text/csv",
            "size": len(file_data),
        },
        "date": "2024-01-01T00:00:00",
        "extra": {},
        "overwrite": True,
        "db_uri": "postgresql://user:pass@localhost:5432/db",
        "idempotency_key": "idem-insert-1",
        "traceparent": None,
        "tracestate": None,
        "baggage": None,
    }


class TestInsertionQueueWorker:
    def test_process_insertion_success_acks_and_publishes(
        self, insertion_worker, sample_insertion_message
    ):
        result = {
            "task_id": "task_insert_1",
            "results": {"sheet1": "INSERT INTO customers VALUES (1)"},
            "status": "success",
        }
        insertion_worker._insert_data = MagicMock(return_value=result)
        insertion_worker._publish_result = MagicMock()

        mock_channel = MagicMock()
        mock_method = MagicMock(delivery_tag="delivery_insert_1")

        insertion_worker.process_insertion_tasks(
            mock_channel,
            mock_method,
            MagicMock(),
            json.dumps(sample_insertion_message).encode(),
        )

        insertion_worker._publish_result.assert_called_once_with(
            "task_insert_1", result, db_client=insertion_worker.db_client
        )
        mock_channel.basic_ack.assert_called_once_with(delivery_tag="delivery_insert_1")

    @patch("src.workers.insertion.get_task_status", return_value="success")
    def test_process_insertion_completed_task_is_skipped(
        self,
        _mock_get_status,
        insertion_worker,
        sample_insertion_message,
    ):
        mock_channel = MagicMock()
        mock_method = MagicMock(delivery_tag="delivery_insert_2")

        insertion_worker.process_insertion_tasks(
            mock_channel,
            mock_method,
            MagicMock(),
            json.dumps(sample_insertion_message).encode(),
        )

        mock_channel.basic_ack.assert_called_once_with(delivery_tag="delivery_insert_2")

    def test_process_insertion_infra_error_requeues(
        self, insertion_worker, sample_insertion_message
    ):
        insertion_worker._insert_data = MagicMock(
            side_effect=ConnectionError("db down")
        )

        mock_channel = MagicMock()
        mock_method = MagicMock(delivery_tag="delivery_insert_3")

        insertion_worker.process_insertion_tasks(
            mock_channel,
            mock_method,
            MagicMock(),
            json.dumps(sample_insertion_message).encode(),
        )

        mock_channel.basic_nack.assert_called_once_with(
            delivery_tag="delivery_insert_3", requeue=True
        )

    def test_unknown_insertion_task_is_ackd(
        self, insertion_worker, sample_insertion_message
    ):
        body = {**sample_insertion_message, "task": "unknown"}
        mock_channel = MagicMock()
        mock_method = MagicMock(delivery_tag="delivery_insert_4")

        insertion_worker.process_insertion_tasks(
            mock_channel,
            mock_method,
            MagicMock(),
            json.dumps(body).encode(),
        )

        mock_channel.basic_ack.assert_called_once_with(delivery_tag="delivery_insert_4")


class TestInsertionPublishResult:
    @patch("src.workers.insertion.update_task_status")
    def test_publish_result_uses_results_queue(
        self,
        mock_update_status,
        insertion_worker,
    ):
        insertion_worker.channel = MagicMock()
        result = {
            "task_id": "task_insert_pub",
            "results": {"sheet1": "INSERT INTO customers VALUES (1)"},
            "status": "success",
        }

        insertion_worker._publish_result(
            "task_insert_pub", result, db_client=insertion_worker.db_client
        )

        insertion_worker.channel.basic_publish.assert_called_once()
        kwargs = insertion_worker.channel.basic_publish.call_args.kwargs
        assert kwargs["exchange"] == insertion_module.mq_settings.RABBITMQ_EXCHANGE
        assert (
            kwargs["routing_key"]
            == insertion_module.mq_settings.RABBITMQ_PUBLISHERS_ROUTING_KEY_RESULTS
        )
        assert json.loads(kwargs["body"]) == result

        mock_update_status.assert_called_once()
        assert mock_update_status.call_args.kwargs["value"] == "published"


class TestInsertionDataFlow:
    @patch("src.workers.insertion.update_task_status")
    @patch("src.workers.insertion.psycopg.connect")
    @patch("src.workers.insertion.post_multipart_http")
    def test_insert_data_calls_excel_reader_and_executes_sql(
        self,
        mock_post_multipart,
        mock_psycopg_connect,
        mock_update_status,
        insertion_worker,
        sample_insertion_message,
    ):
        sql_per_sheet = {
            "sheet1": "INSERT INTO customers VALUES (1, 'alice')",
            "sheet2": "INSERT INTO customers VALUES (2, 'bob')",
        }

        mock_response = MagicMock()
        mock_response.json.return_value = sql_per_sheet
        mock_post_multipart.return_value = mock_response

        mock_cursor = MagicMock()
        mock_conn = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_conn_cm = MagicMock()
        mock_conn_cm.__enter__.return_value = mock_conn
        mock_conn_cm.__exit__.return_value = None
        mock_psycopg_connect.return_value = mock_conn_cm

        result = insertion_worker._insert_data(
            sample_insertion_message, db_client=insertion_worker.db_client
        )

        mock_post_multipart.assert_called_once()
        post_kwargs = mock_post_multipart.call_args.kwargs
        assert post_kwargs["data"] == {"table_name": "customers"}
        assert post_kwargs["params"] == {"overwrite": True}
        assert post_kwargs["files"]["spreadsheet"][0] == "to_insert.csv"

        assert mock_cursor.execute.call_count == 2
        mock_conn.commit.assert_called_once()

        called_statuses = [
            c.kwargs.get("value") for c in mock_update_status.call_args_list
        ]
        assert "processing-file" in called_statuses
        assert "requesting-insert-sql" in called_statuses
        assert "file-processed" in called_statuses

        assert result["status"] == "success"
        assert result["results"] == sql_per_sheet

    @patch("src.workers.insertion.update_task_status")
    @patch("src.workers.insertion.post_multipart_http")
    def test_insert_data_excel_reader_failure_returns_failed_processing(
        self,
        mock_post_multipart,
        mock_update_status,
        insertion_worker,
        sample_insertion_message,
    ):
        mock_post_multipart.side_effect = Exception("excel-reader error")

        result = insertion_worker._insert_data(
            sample_insertion_message, db_client=insertion_worker.db_client
        )

        assert result["status"] == "failed"
        assert result["results"] == {}

        called_statuses = [
            c.kwargs.get("value") for c in mock_update_status.call_args_list
        ]
        assert "failed-processing-file" in called_statuses

    @patch("src.workers.insertion.update_task_status")
    @patch("src.workers.insertion.psycopg.connect")
    @patch("src.workers.insertion.post_multipart_http")
    def test_insert_data_db_failure_returns_failed_inserting(
        self,
        mock_post_multipart,
        mock_psycopg_connect,
        mock_update_status,
        insertion_worker,
        sample_insertion_message,
    ):
        sql_per_sheet = {"sheet1": "INSERT INTO customers VALUES (1, 'alice')"}

        mock_response = MagicMock()
        mock_response.json.return_value = sql_per_sheet
        mock_post_multipart.return_value = mock_response

        mock_psycopg_connect.side_effect = Exception("db insert error")

        result = insertion_worker._insert_data(
            sample_insertion_message, db_client=insertion_worker.db_client
        )

        assert result["status"] == "failed"
        assert result["results"] == sql_per_sheet

        called_statuses = [
            c.kwargs.get("value") for c in mock_update_status.call_args_list
        ]
        assert "failed-inserting-data" in called_statuses
