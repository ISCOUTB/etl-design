from types import SimpleNamespace

import pytest

from src import server as ddl_server


class FakeContext:
    def peer(self) -> str:
        return "test-peer"


class FakeRequest:
    def __init__(self, ast_type: str = "cell", columns=None):
        if columns is None:
            columns = {"A": "col_a"}
        self.columns = columns
        self.ast = SimpleNamespace(type=ast_type)

    def HasField(self, field: str) -> bool:
        return field == "ast"


class FakeEvent:
    def __init__(self):
        self.is_set = False

    def set(self):
        self.is_set = True

    async def wait(self):
        return None


class FakeLoop:
    def __init__(self, trigger_on_register: bool = False):
        self.handlers = []
        self.trigger_on_register = trigger_on_register

    def add_signal_handler(self, sig, callback):
        self.handlers.append((sig, callback))
        if self.trigger_on_register:
            callback()


class FakeGrpcServer:
    def __init__(self):
        self.started = False
        self.stopped_with_grace = None
        self.bound_channel = None

    def add_insecure_port(self, channel):
        self.bound_channel = channel

    async def start(self):
        self.started = True

    async def stop(self, grace):
        self.stopped_with_grace = grace


@pytest.mark.anyio
async def test_generate_ddl_servicer_returns_handler_response(monkeypatch):
    expected = SimpleNamespace(type="cell", sql="col_a")

    def fake_generate_ddl_handler(request):
        return expected

    monkeypatch.setattr(ddl_server, "generate_ddl_handler", fake_generate_ddl_handler)

    servicer = ddl_server.DDLGeneratorServicer()
    response = await servicer.GenerateDDL(FakeRequest(), FakeContext())

    assert response is expected


@pytest.mark.anyio
async def test_generate_ddl_servicer_reraises_handler_errors(monkeypatch):
    def fake_generate_ddl_handler(request):
        raise RuntimeError("handler failed")

    monkeypatch.setattr(ddl_server, "generate_ddl_handler", fake_generate_ddl_handler)

    servicer = ddl_server.DDLGeneratorServicer()

    with pytest.raises(RuntimeError, match="handler failed"):
        await servicer.GenerateDDL(FakeRequest(), FakeContext())


def test_main_calls_asyncio_run(monkeypatch):
    called = {"run": False}

    def fake_run(coro):
        called["run"] = True
        coro.close()

    monkeypatch.setattr(ddl_server.asyncio, "run", fake_run)

    ddl_server.main()

    assert called["run"] is True


def test_main_logs_on_keyboard_interrupt(monkeypatch):
    logs = []

    def fake_run(coro):
        coro.close()
        raise KeyboardInterrupt()

    monkeypatch.setattr(ddl_server.asyncio, "run", fake_run)
    monkeypatch.setattr(ddl_server.logger, "info", lambda msg: logs.append(msg))

    ddl_server.main()

    assert any("terminated by user" in msg for msg in logs)


def test_main_reraises_unexpected_exceptions(monkeypatch):
    logs = []

    def fake_run(coro):
        coro.close()
        raise ValueError("fatal")

    monkeypatch.setattr(ddl_server.asyncio, "run", fake_run)
    monkeypatch.setattr(ddl_server.logger, "error", lambda msg: logs.append(msg))

    with pytest.raises(ValueError, match="fatal"):
        ddl_server.main()

    assert any("Fatal error" in msg for msg in logs)


@pytest.mark.anyio
async def test_serve_without_metrics_starts_and_stops_server(monkeypatch):
    fake_server = FakeGrpcServer()
    fake_loop = FakeLoop(trigger_on_register=False)
    fake_event = FakeEvent()
    added = {"servicer_registered": False}

    monkeypatch.setattr(
        ddl_server.settings,
        "ENABLE_PROMETHEUS_METRICS",
        False,
        raising=False,
    )
    monkeypatch.setattr(
        ddl_server.settings,
        "DDL_GENERATOR_HOST",
        "127.0.0.1",
        raising=False,
    )
    monkeypatch.setattr(
        ddl_server.settings,
        "DDL_GENERATOR_PORT",
        "50053",
        raising=False,
    )
    monkeypatch.setattr(
        ddl_server.grpc.aio,
        "server",
        lambda *args, **kwargs: fake_server,
    )
    monkeypatch.setattr(ddl_server.asyncio, "Event", lambda: fake_event)
    monkeypatch.setattr(ddl_server.asyncio, "get_running_loop", lambda: fake_loop)
    monkeypatch.setattr(
        ddl_server.ddl_generator_pb2_grpc,
        "add_DDLGeneratorServicer_to_server",
        lambda servicer, server: added.__setitem__("servicer_registered", True),
    )

    await ddl_server.serve()

    assert added["servicer_registered"] is True
    assert fake_server.bound_channel == "127.0.0.1:50053"
    assert fake_server.started is True
    assert fake_server.stopped_with_grace == 5
    assert len(fake_loop.handlers) == 2


@pytest.mark.anyio
async def test_serve_with_metrics_uses_interceptor_and_prometheus_server(monkeypatch):
    fake_server = FakeGrpcServer()
    fake_loop = FakeLoop(trigger_on_register=True)
    fake_event = FakeEvent()
    state = {"http_server_started": False, "interceptor_used": False}

    monkeypatch.setattr(
        ddl_server.settings,
        "ENABLE_PROMETHEUS_METRICS",
        True,
        raising=False,
    )
    monkeypatch.setattr(
        ddl_server.settings,
        "PROMETHEUS_METRICS_PORT",
        "50123",
        raising=False,
    )
    monkeypatch.setattr(
        ddl_server.settings,
        "DDL_GENERATOR_HOST",
        "127.0.0.1",
        raising=False,
    )
    monkeypatch.setattr(
        ddl_server.settings,
        "DDL_GENERATOR_PORT",
        "50054",
        raising=False,
    )

    def fake_http_server(port):
        state["http_server_started"] = port == 50123

    def fake_interceptor():
        state["interceptor_used"] = True
        return "fake-interceptor"

    def fake_grpc_server(*args, **kwargs):
        assert kwargs.get("interceptors") == ("fake-interceptor",)
        return fake_server

    monkeypatch.setattr(ddl_server, "start_http_server", fake_http_server)
    monkeypatch.setattr(ddl_server, "PromAsyncServerInterceptor", fake_interceptor)
    monkeypatch.setattr(ddl_server.grpc.aio, "server", fake_grpc_server)
    monkeypatch.setattr(ddl_server.asyncio, "Event", lambda: fake_event)
    monkeypatch.setattr(ddl_server.asyncio, "get_running_loop", lambda: fake_loop)
    monkeypatch.setattr(
        ddl_server.ddl_generator_pb2_grpc,
        "add_DDLGeneratorServicer_to_server",
        lambda servicer, server: None,
    )

    await ddl_server.serve()

    assert state["http_server_started"] is True
    assert state["interceptor_used"] is True
    assert fake_event.is_set is True
    assert fake_server.bound_channel == "127.0.0.1:50054"
    assert fake_server.started is True
    assert fake_server.stopped_with_grace == 5
