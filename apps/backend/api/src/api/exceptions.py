"""
Centralized exception handling for external service errors.
"""

import grpc
from fastapi import Request, status
from fastapi.responses import JSONResponse
from pika.exceptions import (
    AMQPChannelError,
    AMQPConnectionError,
    AMQPError,
    ConnectionClosedByBroker,
    StreamLostError,
)

from src.exceptions import AppException


async def grpc_exception_handler(request: Request, exc: grpc.RpcError) -> JSONResponse:
    """Handle gRPC errors with appropriate HTTP status codes."""

    # Map gRPC status codes to HTTP status codes
    status_code_mapping = {
        grpc.StatusCode.UNAVAILABLE: status.HTTP_503_SERVICE_UNAVAILABLE,
        grpc.StatusCode.DEADLINE_EXCEEDED: status.HTTP_504_GATEWAY_TIMEOUT,
        grpc.StatusCode.CANCELLED: status.HTTP_503_SERVICE_UNAVAILABLE,
        grpc.StatusCode.INVALID_ARGUMENT: status.HTTP_400_BAD_REQUEST,
        grpc.StatusCode.NOT_FOUND: status.HTTP_404_NOT_FOUND,
        grpc.StatusCode.ALREADY_EXISTS: status.HTTP_409_CONFLICT,
        grpc.StatusCode.PERMISSION_DENIED: status.HTTP_403_FORBIDDEN,
        grpc.StatusCode.UNAUTHENTICATED: status.HTTP_401_UNAUTHORIZED,
    }

    grpc_code = exc.code()
    http_status = status_code_mapping.get(
        grpc_code, status.HTTP_500_INTERNAL_SERVER_ERROR
    )

    return JSONResponse(
        status_code=http_status,
        content={
            "error": "Database service error",
            "code": grpc_code.name,
            "message": exc.details(),
            "path": str(request.url.path),
        },
    )


async def rabbitmq_exception_handler(request: Request, exc: AMQPError) -> JSONResponse:
    """Handle RabbitMQ errors."""
    status_code_mapping = {
        AMQPConnectionError: status.HTTP_503_SERVICE_UNAVAILABLE,
        StreamLostError: status.HTTP_504_GATEWAY_TIMEOUT,
        AMQPChannelError: status.HTTP_500_INTERNAL_SERVER_ERROR,
        ConnectionClosedByBroker: status.HTTP_503_SERVICE_UNAVAILABLE,
    }

    http_status = status_code_mapping.get(
        type(exc), status.HTTP_500_INTERNAL_SERVER_ERROR
    )

    return JSONResponse(
        status_code=http_status,
        content={
            "error": "Message broker service unavailable",
            "message": str(exc),
            "path": str(request.url.path),
        },
    )


async def app_exception_handler(request: Request, exc: AppException):
    """Catch-all handler for AppException errors."""
    return JSONResponse(status_code=exc.status_code, content=exc._make_response_body())
