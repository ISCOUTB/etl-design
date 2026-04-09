"""Unit tests for healthcheck service."""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.schemas.healthcheck import (
    DatabaseHealthCheckResult,
    RabbitMQHealthCheckResult,
)
from src.services.healthcheck import (
    check_database_client_connection,
    check_database_client_connection_async,
    check_databases_connection,
    check_rabbitmq_connection,
)


class TestCheckRabbitMQConnection:
    @pytest.mark.asyncio
    @patch("src.services.healthcheck.aio_pika.connect_robust")
    async def test_rabbitmq_connection_healthy(self, mock_connect):
        mock_channel = AsyncMock()
        mock_connection = AsyncMock()
        mock_connection.channel.return_value = mock_channel
        mock_connect.return_value = mock_connection

        result = await check_rabbitmq_connection()

        assert result.status == "healthy"
        assert result.response_time_ms == "< 5000"
        assert result.error is None

    @pytest.mark.asyncio
    @patch("src.services.healthcheck.aio_pika.connect_robust")
    async def test_rabbitmq_connection_timeout(self, mock_connect):
        mock_connect.side_effect = asyncio.TimeoutError()

        result = await check_rabbitmq_connection()

        assert result.status == "unhealthy"
        assert result.response_time_ms == "> 5000"
        assert result.error == "Connection timeout"

    @pytest.mark.asyncio
    @patch("src.services.healthcheck.aio_pika.connect_robust")
    async def test_rabbitmq_connection_error(self, mock_connect):
        mock_connect.side_effect = Exception("Connection refused")

        result = await check_rabbitmq_connection()

        assert result.status == "unhealthy"
        assert result.response_time_ms == "N/A"
        assert "Connection refused" in result.error


class TestCheckDatabaseClientConnection:
    def test_database_connection_all_healthy(self):
        db_client = MagicMock()
        db_client.redis_ping.return_value = {"pong": True}
        db_client.mongo_ping.return_value = {"pong": True}

        result = check_database_client_connection(db_client)

        assert result.status == "healthy"
        assert result.mongodb is True
        assert result.redis is True

    def test_database_connection_partial_unhealthy(self):
        db_client = MagicMock()
        db_client.redis_ping.side_effect = Exception("redis down")
        db_client.mongo_ping.return_value = {"pong": True}

        result = check_database_client_connection(db_client)

        assert result.status == "unhealthy"
        assert result.mongodb is True
        assert result.redis is False


class TestCheckDatabaseClientConnectionAsync:
    @pytest.mark.asyncio
    async def test_database_connection_async_all_healthy(self):
        db_client = MagicMock()
        db_client.redis_ping_async = AsyncMock(return_value={"pong": True})
        db_client.mongo_ping_async = AsyncMock(return_value={"pong": True})

        result = await check_database_client_connection_async(db_client)

        assert result.status == "healthy"
        assert result.mongodb is True
        assert result.redis is True

    @pytest.mark.asyncio
    async def test_database_connection_async_unhealthy(self):
        db_client = MagicMock()
        db_client.redis_ping_async = AsyncMock(side_effect=Exception("redis down"))
        db_client.mongo_ping_async = AsyncMock(return_value={"pong": True})

        result = await check_database_client_connection_async(db_client)

        assert result.status == "unhealthy"
        assert result.mongodb is True
        assert result.redis is False


class TestCheckDatabasesConnection:
    @pytest.mark.asyncio
    @patch("src.services.healthcheck.check_rabbitmq_connection")
    @patch("src.services.healthcheck.check_database_client_connection")
    async def test_all_services_healthy_sync_db(
        self,
        mock_db_check,
        mock_rabbitmq_check,
    ):
        mock_db_check.return_value = DatabaseHealthCheckResult(
            status="healthy", mongodb=True, redis=True
        )
        mock_rabbitmq_check.return_value = RabbitMQHealthCheckResult(
            status="healthy", response_time_ms="< 5000", error=None
        )

        result = await check_databases_connection(MagicMock(), awaitable=False)

        assert result.status == "healthy"
        assert result.database.status == "healthy"
        assert result.rabbitmq.status == "healthy"

    @pytest.mark.asyncio
    @patch("src.services.healthcheck.check_rabbitmq_connection")
    @patch("src.services.healthcheck.check_database_client_connection_async")
    async def test_unhealthy_when_rabbitmq_fails_async_db(
        self,
        mock_db_check_async,
        mock_rabbitmq_check,
    ):
        mock_db_check_async.return_value = DatabaseHealthCheckResult(
            status="healthy", mongodb=True, redis=True
        )
        mock_rabbitmq_check.return_value = RabbitMQHealthCheckResult(
            status="unhealthy", response_time_ms="N/A", error="refused"
        )

        result = await check_databases_connection(MagicMock(), awaitable=True)

        assert result.status == "unhealthy"
        assert result.database.status == "healthy"
        assert result.rabbitmq.status == "unhealthy"
