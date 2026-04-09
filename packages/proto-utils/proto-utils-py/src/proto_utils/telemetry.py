import os
from threading import Lock

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

_config_lock = Lock()
_configured = False


def _resolve_traces_endpoint(endpoint: str | None) -> str:
    if endpoint:
        base = endpoint.rstrip("/")
    else:
        base = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://alloy:4318").rstrip(
            "/"
        )

    explicit_traces_endpoint = os.getenv("OTEL_EXPORTER_OTLP_TRACES_ENDPOINT", "")
    if explicit_traces_endpoint:
        return explicit_traces_endpoint

    if base.endswith("/v1/traces"):
        return base
    return f"{base}/v1/traces"


def configure_otel_tracing(
    *,
    service_name: str,
    service_version: str = "1.0.0",
    environment: str = "production",
    endpoint: str | None = None,
) -> None:
    """Configure OpenTelemetry tracing once per process.

    This sets up a TracerProvider with OTLP/HTTP exporter so spans can be sent
    to Alloy/Tempo. If tracing is disabled via OTEL_TRACING_ENABLED=false, this
    function exits without changing global tracer provider.
    """
    global _configured

    if os.getenv("OTEL_TRACING_ENABLED", "true").lower() in {"0", "false", "no"}:
        return

    with _config_lock:
        if _configured:
            return

        traces_endpoint = _resolve_traces_endpoint(endpoint)

        resource = Resource.create(
            {
                "service.name": service_name,
                "service.version": service_version,
                "deployment.environment": environment,
            }
        )

        provider = TracerProvider(resource=resource)
        exporter = OTLPSpanExporter(endpoint=traces_endpoint)
        processor = BatchSpanProcessor(exporter)
        provider.add_span_processor(processor)

        trace.set_tracer_provider(provider)
        _configured = True
