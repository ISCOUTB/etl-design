"""Resilience tests aligned with current handler behavior.

These tests intentionally avoid brittle end-to-end gRPC checks and focus on:
1. Retry configuration sanity.
2. Default behavior (no retry unless explicitly enabled).
3. Retry behavior when retry_on_failure=True.
"""

from unittest.mock import MagicMock, patch

import pymongo.errors
import pytest
import redis.exceptions
from proto_utils.database import dtypes

from src.handlers.mongo_handler import MongoHandler
from src.handlers.redis_handler import RedisHandler
from src.handlers.tasks_handler import DatabaseTasksHandler


class TestRetryConfiguration:
    def test_redis_retry_config_is_defined(self):
        handler = RedisHandler()

        assert handler.max_retries_redis > 0
        assert handler.retry_delay_redis > 0
        assert handler.backoff_redis >= 1.0

    def test_mongo_retry_config_is_defined(self):
        handler = MongoHandler()

        assert handler.max_retries_mongo > 0
        assert handler.retry_delay_mongo > 0
        assert handler.backoff_mongo >= 1.0

    def test_tasks_retry_config_is_defined_for_both_databases(self):
        handler = DatabaseTasksHandler()

        assert handler.max_retries_redis > 0
        assert handler.retry_delay_redis > 0
        assert handler.backoff_redis >= 1.0

        assert handler.max_retries_mongo > 0
        assert handler.retry_delay_mongo > 0
        assert handler.backoff_mongo >= 1.0


class TestRetryBehavior:
    def test_redis_no_retry_by_default(self):
        """Current behavior: retry is opt-in via retry_on_failure=True."""
        handler = RedisHandler()

        with patch.object(handler.manager, "get_redis_connection") as mock_get_conn:
            failing_conn = MagicMock()
            failing_conn.ping.side_effect = redis.exceptions.ConnectionError(
                "Connection refused"
            )
            mock_get_conn.return_value = failing_conn

            request = dtypes.RedisPingRequest()

            with pytest.raises(redis.exceptions.ConnectionError):
                handler._execute_with_retry(
                    lambda req, redis_db: dtypes.RedisPingResponse(
                        pong=redis_db.ping()
                    ),
                    request,
                )

            assert mock_get_conn.call_count == 1

    def test_redis_retries_when_retry_on_failure_is_enabled(self):
        handler = RedisHandler()

        with patch.object(handler.manager, "get_redis_connection") as mock_get_conn:
            failing_conn = MagicMock()
            failing_conn.ping.side_effect = redis.exceptions.ConnectionError(
                "Connection refused"
            )

            working_conn = MagicMock()
            working_conn.ping.return_value = True

            mock_get_conn.side_effect = [failing_conn, working_conn]

            with patch("src.handlers.redis_handler.time.sleep"):
                request = dtypes.RedisPingRequest()
                response = handler._execute_with_retry(
                    lambda req, redis_db: dtypes.RedisPingResponse(
                        pong=redis_db.ping()
                    ),
                    request,
                    retry_on_failure=True,
                )

            assert response["pong"] is True
            assert mock_get_conn.call_count == 2

    def test_mongo_retries_when_retry_on_failure_is_enabled(self):
        handler = MongoHandler()

        with patch.object(
            handler.manager, "get_mongo_schemas_connection"
        ) as mock_get_conn:
            failing_conn = MagicMock()
            failing_conn.count_documents.side_effect = pymongo.errors.ConnectionFailure(
                "Connection refused"
            )

            working_conn = MagicMock()
            working_conn.count_documents.return_value = 5

            mock_get_conn.side_effect = [failing_conn, working_conn]

            with patch("src.handlers.mongo_handler.time.sleep"):
                request = dtypes.MongoCountAllDocumentsRequest()
                response = handler._execute_with_retry(
                    lambda req, mongo_schemas_connection, **_: (
                        dtypes.MongoCountAllDocumentsResponse(
                            amount=mongo_schemas_connection.count_documents()
                        )
                    ),
                    request,
                    retry_on_failure=True,
                )

            assert response["amount"] == 5
            assert mock_get_conn.call_count == 2

    def test_redis_retries_are_exhausted_when_enabled(self):
        handler = RedisHandler()

        with patch.object(handler.manager, "get_redis_connection") as mock_get_conn:
            failing_conn = MagicMock()
            failing_conn.ping.side_effect = redis.exceptions.ConnectionError(
                "Connection refused"
            )
            mock_get_conn.return_value = failing_conn

            with patch("src.handlers.redis_handler.time.sleep"):
                request = dtypes.RedisPingRequest()

                with pytest.raises(redis.exceptions.ConnectionError):
                    handler._execute_with_retry(
                        lambda req, redis_db: dtypes.RedisPingResponse(
                            pong=redis_db.ping()
                        ),
                        request,
                        retry_on_failure=True,
                    )

            assert mock_get_conn.call_count == handler.max_retries_redis
