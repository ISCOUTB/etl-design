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
    context: grpc.aio.ServicerContext[Any, Any],
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


def attach_trace_context(headers: dict[str, str]) -> object:
    extracted_context = extract(headers)
    return otel_context.attach(extracted_context)


def detach_trace_context(token: object) -> None:
    otel_context.detach(token)
