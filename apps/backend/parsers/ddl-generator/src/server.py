"""gRPC DDL Generator Server.

This module implements a gRPC server that provides DDL (Data Definition Language)
generation services for the ETL design system. It processes AST (Abstract Syntax Tree)
structures and column information to generate SQL DDL statements.

The server provides the following services:
    - DDL generation: converts AST and column data to SQL DDL statements

Architecture:
    Client -> gRPC DDL Generator Server (this) -> DDL Generator Handler -> Core Logic

Logging Enhancements:
    - Structured logging with operation tags for filtering and debugging
    - Client information tracking for connection monitoring
    - Detailed request/response logging with sanitized data
    - Error handling with contextual information
    - Performance tracking and operation success/failure metrics
"""

import asyncio
import signal

import grpc
from grpc._typing import Any  # type: ignore
from prometheus_client import start_http_server
from proto_utils.generated.parsers import (
    ddl_generator_pb2,
    ddl_generator_pb2_grpc,
)
from py_async_grpc_prometheus.prometheus_async_server_interceptor import (
    PromAsyncServerInterceptor,
)

from src.core.config import settings
from src.handlers.ddl_generator import generate_ddl_handler
from src.utils.logger import logger
from src.utils.trace_context import (
    attach_trace_context,
    detach_trace_context,
    extract_trace_headers_from_context,
)
from src.utils.watch_files import main_debug


class DDLGeneratorServicer(ddl_generator_pb2_grpc.DDLGeneratorServicer):
    """gRPC Servicer for DDL generation operations.

    This class implements the DDLGeneratorService gRPC interface, providing
    methods for converting AST structures and column information into SQL DDL.
    It acts as the entry point for all DDL generation requests in the ETL system.

    The servicer delegates actual DDL generation to specialized handlers
    while providing comprehensive logging, error handling, and client tracking.

    Attributes:
        None. The servicer is stateless and delegates to handler functions.

    Note:
        All operations are logged with structured tags for easy filtering
        and debugging. Client information is tracked for monitoring purposes.
    """

    def __init__(self):
        """Initialize the DDL generator servicer.

        Sets up the servicer with configuration logging. The servicer itself
        is stateless and relies on handler functions for actual DDL generation.
        """
        logger.info(
            "[INIT] Initializing DDLGeneratorServicer - "
            f"DDL Channel: {settings.DDL_GENERATOR_CHANNEL}, "
            f"Debug Mode: {settings.DDL_GENERATOR_DEBUG}"
        )

    async def GenerateDDL(
        self,
        request: ddl_generator_pb2.DDLRequest,
        context: grpc.aio.ServicerContext[Any, Any],
    ) -> ddl_generator_pb2.DDLResponse:
        trace_context_token = None
        inbound_trace_headers: dict[str, str] = {}

        if settings.DDL_TRACE_CONTEXT_ENABLED:
            inbound_trace_headers = extract_trace_headers_from_context(context)
            trace_context_token = attach_trace_context(inbound_trace_headers)

        if (
            settings.DDL_TRACE_CONTEXT_LOG_HEADERS
            and settings.DDL_GENERATOR_DEBUG
            and inbound_trace_headers
        ):
            logger.info(
                "[TRACE_CONTEXT] Inbound gRPC trace headers received - "
                f"traceparent: {inbound_trace_headers.get('traceparent')}, "
                f"tracestate: {inbound_trace_headers.get('tracestate')}"
            )

        column_count = len(request.columns)
        ast_type = request.ast.type if request.HasField("ast") else "NO_AST"

        logger.info(
            f"[DDL_GENERATE] Request from client {context.peer()} - "
            f"AST Type: {ast_type}, Column Count: {column_count}"
        )

        try:
            response = generate_ddl_handler(request)
            sql_length = len(response.sql) if response.sql else 0

            logger.info(
                f"[DDL_GENERATE] DDL generation completed - "
                f"Response Type: {response.type}, SQL Length: {sql_length} chars"
            )

            return response
        except Exception as e:
            logger.error(f"[DDL_GENERATE] Operation failed: {e}")
            raise
        finally:
            if trace_context_token is not None:
                detach_trace_context(trace_context_token)


async def serve() -> None:
    """Start the gRPC DDL generator server."""
    # Create servicer instance
    servicer = DDLGeneratorServicer()

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

    ddl_generator_pb2_grpc.add_DDLGeneratorServicer_to_server(servicer, server)
    server.add_insecure_port(settings.DDL_GENERATOR_CHANNEL)

    # Start server
    logger.info("[SERVER] Starting gRPC DDL Generator server...")
    await server.start()

    logger.info(
        f"[SERVER] DDL Generator server ready on {settings.DDL_GENERATOR_CHANNEL}"
    )
    logger.info(f"[SERVER] Debug mode: {settings.DDL_GENERATOR_DEBUG}")

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
    """Main entry point for the DDL generator server."""
    try:
        logger.info("[MAIN] Initializing DDL Generator Server...")
        asyncio.run(serve())
    except KeyboardInterrupt:
        logger.info("[MAIN] Application terminated by user")
    except Exception as e:
        logger.error(f"[MAIN] Fatal error: {e}")
        raise


if __name__ == "__main__":
    if settings.DDL_GENERATOR_DEBUG:
        try:
            asyncio.run(main_debug(main))
        except KeyboardInterrupt:
            logger.info("[MAIN] Application terminated by user")
    else:
        main()
