import asyncio
import signal

import grpc
from grpc._typing import Any  # type: ignore
from opentelemetry import trace
from prometheus_client import start_http_server
from proto_utils.generated.parsers import sql_builder_pb2, sql_builder_pb2_grpc
from proto_utils.telemetry import configure_otel_tracing
from py_async_grpc_prometheus.prometheus_async_server_interceptor import (
    PromAsyncServerInterceptor,
)

from src.core.config import settings
from src.handlers.sql_builder import sql_builder_handler
from src.utils.logger import logger
from src.utils.trace_context import (
    attach_trace_context,
    detach_trace_context,
    extract_trace_headers_from_context,
)
from src.utils.watch_files import main_debug

configure_otel_tracing(
    service_name=settings.OTEL_SERVICE_NAME,
    service_version=settings.OTEL_SERVICE_VERSION,
    environment="debug" if settings.SQL_BUILDER_DEBUG else "production",
)
tracer = trace.get_tracer("sql_builder.grpc")


class SQLBuilderServicer(sql_builder_pb2_grpc.SQLBuilderServicer):
    """gRPC Servicer for SQL builder operations."""

    def __init__(self):
        """Initialize the SQL builder servicer."""
        logger.info(
            "[INIT] Initializing SQLBuilderServicer - "
            f"SQL Channel: {settings.SQL_BUILDER_CHANNEL}, "
            f"Debug Mode: {settings.SQL_BUILDER_DEBUG}"
        )

    async def BuildSQL(
        self,
        request: sql_builder_pb2.BuildSQLRequest,
        context: grpc.aio.ServicerContext[Any, Any],
    ) -> sql_builder_pb2.BuildSQLResponse:
        trace_context_token = None
        inbound_trace_headers: dict[str, str] = {}

        if settings.SQL_TRACE_CONTEXT_ENABLED:
            inbound_trace_headers = extract_trace_headers_from_context(context)
            trace_context_token = attach_trace_context(inbound_trace_headers)

        if (
            settings.SQL_TRACE_CONTEXT_LOG_HEADERS
            and settings.SQL_BUILDER_DEBUG
            and inbound_trace_headers
        ):
            logger.info(
                "[TRACE_CONTEXT] Inbound gRPC trace headers received - "
                f"traceparent: {inbound_trace_headers.get('traceparent')}, "
                f"tracestate: {inbound_trace_headers.get('tracestate')}"
            )

        table_name = request.table_name
        column_count = len(request.cols)

        logger.info(
            f"[SQL_BUILD] Request from client {context.peer()} - "
            f"Table: {table_name}, Columns: {column_count}"
        )

        try:
            with tracer.start_as_current_span("grpc.BuildSQL") as span:
                span.set_attribute("rpc.system", "grpc")
                span.set_attribute("rpc.method", "BuildSQL")
                span.set_attribute("sql.column_count", column_count)
                response = sql_builder_handler(request)
            content_levels = len(response.content)

            logger.info(
                f"[SQL_BUILD] SQL building completed - "
                f"Content Levels: {content_levels}, Error: {bool(response.error)}"
            )

            return response
        except Exception as e:
            logger.error(f"[SQL_BUILD] Operation failed: {e}")
            raise
        finally:
            if trace_context_token is not None:
                detach_trace_context(trace_context_token)


async def serve() -> None:
    """Start the gRPC SQL builder server."""
    # Create servicer instance
    servicer = SQLBuilderServicer()

    # Create and configure server

    # Interceptor for Prometheus metrics if enabled
    if settings.ENABLE_PROMETHEUS_METRICS:
        logger.info("[SERVER] Prometheus metrics enabled")

        # Create prometheus metrics server
        start_http_server(int(settings.PROMETHEUS_METRICS_PORT))
        logger.info(
            "[SERVER] Prometheus metrics rest server started on port "
            f"{settings.PROMETHEUS_METRICS_PORT}"
        )

        logger.info("[SERVER] Starting gRPC server with Prometheus interceptor")
        server = grpc.aio.server(interceptors=(PromAsyncServerInterceptor(),))
    else:
        server = grpc.aio.server()

    sql_builder_pb2_grpc.add_SQLBuilderServicer_to_server(servicer, server)
    server.add_insecure_port(settings.SQL_BUILDER_CHANNEL)

    # Start server
    logger.info("[SERVER] Starting gRPC SQL Builder server...")
    await server.start()

    logger.info(
        f"[SERVER] SQL Builder server ready on {settings.SQL_BUILDER_CHANNEL}"
    )
    logger.info(f"[SERVER] Debug mode: {settings.SQL_BUILDER_DEBUG}")

    # Set up graceful shutdown
    stop_event = asyncio.Event()

    def _signal_handler() -> None:
        logger.info("[SERVER] Shutdown signal received")
        stop_event.set()

    loop = asyncio.get_running_loop()
    loop.add_signal_handler(signal.SIGINT, _signal_handler)
    loop.add_signal_handler(signal.SIGTERM, _signal_handler)

    try:
        await stop_event.wait()
    finally:
        logger.info("[SERVER] Stopping server...")
        await server.stop(grace=5)
        logger.info("[SERVER] Server stopped")


def main() -> None:
    """Main entry point for the SQL builder server."""
    try:
        logger.info("[MAIN] Initializing SQL Builder Server...")
        asyncio.run(serve())
    except KeyboardInterrupt:
        logger.info("[MAIN] Application terminated by user")
    except Exception as e:
        logger.error(f"[MAIN] Fatal error: {e}")
        raise


if __name__ == "__main__":
    if settings.SQL_BUILDER_DEBUG:
        try:
            asyncio.run(main_debug(main))
        except KeyboardInterrupt:
            logger.info("[MAIN] Application terminated by user")
    else:
        main()
