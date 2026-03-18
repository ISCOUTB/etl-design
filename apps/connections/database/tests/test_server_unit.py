import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest
from proto_utils.generated.database import (
    database_pb2,
    mongo_pb2,
    redis_pb2,
)

import src.server as server_module


def _mock_context():
    return SimpleNamespace(peer=lambda: "unit-test-client")


def _servicer_with_mock_handlers():
    servicer = server_module.DatabaseServicer.__new__(server_module.DatabaseServicer)
    servicer.redis_handler = MagicMock()
    servicer.mongo_handler = MagicMock()
    servicer.database_tasks_handler = MagicMock()
    return servicer


def test_database_servicer_init_uses_handler_classes(monkeypatch):
    fake_redis = object()
    fake_mongo = object()
    fake_tasks = object()

    monkeypatch.setattr(server_module, "RedisHandler", lambda: fake_redis)
    monkeypatch.setattr(server_module, "MongoHandler", lambda: fake_mongo)
    monkeypatch.setattr(server_module, "DatabaseTasksHandler", lambda: fake_tasks)

    servicer = server_module.DatabaseServicer()

    assert servicer.redis_handler is fake_redis
    assert servicer.mongo_handler is fake_mongo
    assert servicer.database_tasks_handler is fake_tasks


def test_redis_ping_delegates_to_handler():
    servicer = _servicer_with_mock_handlers()
    expected = redis_pb2.RedisPingResponse(pong=True)
    servicer.redis_handler.ping.return_value = expected

    response = asyncio.run(
        servicer.RedisPing(redis_pb2.RedisPingRequest(), _mock_context())
    )

    servicer.redis_handler.ping.assert_called_once()
    assert response == expected


def test_mongo_count_delegates_to_handler():
    servicer = _servicer_with_mock_handlers()
    expected = mongo_pb2.MongoCountAllDocumentsResponse(amount=7)
    servicer.mongo_handler.count_all_documents.return_value = expected

    response = asyncio.run(
        servicer.MongoCountAllDocuments(
            mongo_pb2.MongoCountAllDocumentsRequest(), _mock_context()
        )
    )

    servicer.mongo_handler.count_all_documents.assert_called_once()
    assert response == expected


def test_task_set_and_remove_delegate_to_handler():
    servicer = _servicer_with_mock_handlers()

    set_response = database_pb2.SetTaskIdResponse(success=True)
    rm_response = database_pb2.RemoveTaskIdResponse(success=True)

    servicer.database_tasks_handler.set_task_id.return_value = set_response
    servicer.database_tasks_handler.remove_task_id.return_value = rm_response

    r1 = asyncio.run(
        servicer.SetTaskId(
            database_pb2.SetTaskIdRequest(task_id="1", task="excel"),
            _mock_context(),
        )
    )
    r2 = asyncio.run(
        servicer.RemoveTaskId(
            database_pb2.RemoveTaskIdRequest(task_id="1", task="excel"),
            _mock_context(),
        )
    )

    servicer.database_tasks_handler.set_task_id.assert_called_once()
    servicer.database_tasks_handler.remove_task_id.assert_called_once()
    assert r1.success is True
    assert r2.success is True


def test_servicer_method_propagates_exceptions():
    servicer = _servicer_with_mock_handlers()
    servicer.redis_handler.get.side_effect = RuntimeError("boom")

    with pytest.raises(RuntimeError, match="boom"):
        asyncio.run(
            servicer.RedisGet(
                redis_pb2.RedisGetRequest(key="k"),
                _mock_context(),
            )
        )


def test_serve_without_prometheus(monkeypatch):
    fake_server = AsyncMock()
    fake_server.add_insecure_port = MagicMock(return_value=None)
    fake_server.wait_for_termination.side_effect = KeyboardInterrupt

    monkeypatch.setattr(server_module.grpc.aio, "server", lambda **kwargs: fake_server)
    monkeypatch.setattr(
        server_module.database_pb2_grpc,
        "add_DatabaseServiceServicer_to_server",
        MagicMock(),
    )
    monkeypatch.setattr(server_module, "DatabaseServicer", lambda: MagicMock())
    monkeypatch.setattr(server_module, "start_http_server", MagicMock())

    monkeypatch.setattr(server_module.settings, "ENABLE_PROMETHEUS_METRICS", False)
    monkeypatch.setattr(server_module.settings, "DATABASE_CONNECTION_HOST", "localhost")
    monkeypatch.setattr(server_module.settings, "DATABASE_CONNECTION_PORT", 50050)
    monkeypatch.setattr(server_module.settings, "DATABASE_CONNECTION_DEBUG", False)

    asyncio.run(server_module.serve())

    server_module.database_pb2_grpc.add_DatabaseServiceServicer_to_server.assert_called_once()
    fake_server.add_insecure_port.assert_called_once_with("localhost:50050")
    fake_server.start.assert_awaited_once()
    fake_server.stop.assert_awaited_once_with(grace=5)
    server_module.start_http_server.assert_not_called()


def test_serve_with_prometheus(monkeypatch):
    fake_server = AsyncMock()
    fake_server.add_insecure_port = MagicMock(return_value=None)
    fake_server.wait_for_termination.side_effect = KeyboardInterrupt

    created_kwargs = {}

    def _fake_server(**kwargs):
        created_kwargs.update(kwargs)
        return fake_server

    monkeypatch.setattr(server_module.grpc.aio, "server", _fake_server)
    monkeypatch.setattr(
        server_module.database_pb2_grpc,
        "add_DatabaseServiceServicer_to_server",
        MagicMock(),
    )
    monkeypatch.setattr(server_module, "DatabaseServicer", lambda: MagicMock())
    monkeypatch.setattr(server_module, "start_http_server", MagicMock())

    monkeypatch.setattr(server_module.settings, "ENABLE_PROMETHEUS_METRICS", True)
    monkeypatch.setattr(server_module.settings, "PROMETHEUS_METRICS_PORT", "9090")
    monkeypatch.setattr(server_module.settings, "DATABASE_CONNECTION_HOST", "localhost")
    monkeypatch.setattr(server_module.settings, "DATABASE_CONNECTION_PORT", 50050)
    monkeypatch.setattr(server_module.settings, "DATABASE_CONNECTION_DEBUG", False)

    asyncio.run(server_module.serve())

    server_module.start_http_server.assert_called_once_with(9090)
    assert "interceptors" in created_kwargs
    fake_server.start.assert_awaited_once()


def test_main_closes_connections_on_keyboard_interrupt(monkeypatch):
    fake_manager = MagicMock()

    def _raise_keyboard_interrupt(coro):
        coro.close()
        raise KeyboardInterrupt

    monkeypatch.setattr(server_module.asyncio, "run", _raise_keyboard_interrupt)
    monkeypatch.setattr(server_module, "get_connection_manager", lambda: fake_manager)

    server_module.main()

    fake_manager.close_all.assert_called_once()


def test_main_reraises_unexpected_exceptions(monkeypatch):
    def _raise_runtime_error(coro):
        coro.close()
        raise RuntimeError("fatal")

    monkeypatch.setattr(server_module.asyncio, "run", _raise_runtime_error)

    with pytest.raises(RuntimeError, match="fatal"):
        server_module.main()
