from collections.abc import Callable
from functools import wraps
from typing import Any

import grpc
from opentelemetry import context as otel_context
from opentelemetry.propagate import extract

_TRACE_HEADER_KEYS = {"traceparent", "tracestate", "baggage"}


def _metadata_key_value(item: Any) -> tuple[str, str] | None:
    if hasattr(item, "key") and hasattr(item, "value"):
        return str(item.key), str(item.value)

    if isinstance(item, tuple) and len(item) == 2:
        return str(item[0]), str(item[1])

    return None


def extract_trace_headers_from_context(
    context: grpc.aio.ServicerContext,
) -> dict[str, str]:
    headers: dict[str, str] = {}

    for item in context.invocation_metadata() or ():
        pair = _metadata_key_value(item)
        if pair is None:
            continue

        key, value = pair
        key = key.lower()
        if key in _TRACE_HEADER_KEYS:
            headers[key] = value

    return headers


def attach_trace_context(headers: dict[str, str]) -> Any:
    extracted_context = extract(headers)
    return otel_context.attach(extracted_context)


def detach_trace_context(token: Any) -> None:
    otel_context.detach(token)


def with_grpc_trace_context(
    *,
    logger,
    enabled: bool,
    log_headers: bool,
    debug_enabled: bool,
) -> Callable:
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(self, request, context, *args, **kwargs):
            trace_context_token = None
            inbound_trace_headers: dict[str, str] = {}

            if enabled:
                inbound_trace_headers = extract_trace_headers_from_context(context)
                trace_context_token = attach_trace_context(inbound_trace_headers)

            if log_headers and debug_enabled and inbound_trace_headers:
                logger.info(
                    "[TRACE_CONTEXT] Inbound gRPC trace headers received - "
                    f"traceparent: {inbound_trace_headers.get('traceparent')}, "
                    f"tracestate: {inbound_trace_headers.get('tracestate')}"
                )

            try:
                return await func(self, request, context, *args, **kwargs)
            finally:
                if trace_context_token is not None:
                    detach_trace_context(trace_context_token)

        return wrapper

    return decorator


def decorate_grpc_methods(
    cls: type, method_names: list[str], decorator: Callable
) -> type:
    for method_name in method_names:
        method = getattr(cls, method_name)
        setattr(cls, method_name, decorator(method))
    return cls
