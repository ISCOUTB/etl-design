from time import perf_counter

from fastapi import Request
from opentelemetry import context as otel_context
from opentelemetry import trace
from opentelemetry.propagate import extract
from starlette.middleware.base import BaseHTTPMiddleware

from src.utils import logger

tracer = trace.get_tracer("api.middleware.logs")


class LogsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Extract trace context from incoming HTTP headers (W3C format)
        extracted_context = extract(dict(request.headers))
        token = otel_context.attach(extracted_context)

        # Store trace headers in request state for downstream use (excel-reader, RabbitMQ)
        request.state.trace_headers = {
            "traceparent": request.headers.get("traceparent", ""),
            "tracestate": request.headers.get("tracestate", ""),
            "baggage": request.headers.get("baggage", ""),
        }

        try:
            with tracer.start_as_current_span("http.request") as span:
                span.set_attribute("http.method", request.method)
                span.set_attribute("http.route", request.url.path)

                start_time = perf_counter()
                logger.info(
                    "request.started",
                    extra={
                        "method": request.method,
                        "path": request.url.path,
                        "query": str(request.url.query),
                        "client": request.client.host if request.client else None,
                    },
                )

                response = await call_next(request)
                duration_ms = round((perf_counter() - start_time) * 1000, 2)
                span.set_attribute("http.status_code", response.status_code)
                span.set_attribute("http.response.duration_ms", duration_ms)

                logger.info(
                    "request.completed",
                    extra={
                        "method": request.method,
                        "path": request.url.path,
                        "status_code": response.status_code,
                        "duration_ms": duration_ms,
                    },
                )

                return response
        finally:
            otel_context.detach(token)
