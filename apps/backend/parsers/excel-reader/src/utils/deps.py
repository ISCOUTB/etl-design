from collections import namedtuple
from collections.abc import Generator

import grpc
from opentelemetry.propagate import inject
from proto_utils.generated.parsers import (
    ddl_generator_pb2_grpc,
    formula_parser_pb2_grpc,
    sql_builder_pb2_grpc,
)

from src.core.config import settings

_ClientCallDetails = namedtuple(
    "_ClientCallDetails",
    [
        "method",
        "timeout",
        "metadata",
        "credentials",
        "wait_for_ready",
        "compression",
    ],
)


class TraceContextClientInterceptor(
    grpc.UnaryUnaryClientInterceptor,
    grpc.UnaryStreamClientInterceptor,
    grpc.StreamUnaryClientInterceptor,
    grpc.StreamStreamClientInterceptor,
):
    @staticmethod
    def _inject_metadata(client_call_details: grpc.ClientCallDetails):
        carrier: dict[str, str] = {}
        inject(carrier)

        existing_metadata = list(client_call_details.metadata or [])
        metadata = [
            (key, value)
            for key, value in existing_metadata
            if key.lower() not in {"traceparent", "tracestate", "baggage"}
        ]
        metadata.extend((key, value) for key, value in carrier.items() if value)

        return _ClientCallDetails(
            method=client_call_details.method,
            timeout=client_call_details.timeout,
            metadata=metadata,
            credentials=client_call_details.credentials,
            wait_for_ready=client_call_details.wait_for_ready,
            compression=client_call_details.compression,
        )

    def intercept_unary_unary(self, continuation, client_call_details, request):
        updated_details = self._inject_metadata(client_call_details)
        return continuation(updated_details, request)

    def intercept_unary_stream(
        self, continuation, client_call_details, request
    ):
        updated_details = self._inject_metadata(client_call_details)
        return continuation(updated_details, request)

    def intercept_stream_unary(
        self, continuation, client_call_details, request_iterator
    ):
        updated_details = self._inject_metadata(client_call_details)
        return continuation(updated_details, request_iterator)

    def intercept_stream_stream(
        self, continuation, client_call_details, request_iterator
    ):
        updated_details = self._inject_metadata(client_call_details)
        return continuation(updated_details, request_iterator)


def _create_channel(target: str) -> grpc.Channel:
    channel = grpc.insecure_channel(target)
    return grpc.intercept_channel(channel, TraceContextClientInterceptor())


def get_formula_parser_stub() -> Generator[
    formula_parser_pb2_grpc.FormulaParserStub,
    None,
    None,
]:
    """Create and yield a gRPC stub for the Formula Parser service."""
    channel = _create_channel(settings.FORMULA_PARSER_CHANNEL)
    stub = formula_parser_pb2_grpc.FormulaParserStub(channel)
    try:
        yield stub
    finally:
        channel.close()


def get_ddl_generator_stub() -> Generator[
    ddl_generator_pb2_grpc.DDLGeneratorStub,
    None,
    None,
]:
    """Create and yield a gRPC stub for the DDL Generator service."""
    channel = _create_channel(settings.DDL_GENERATOR_CHANNEL)
    stub = ddl_generator_pb2_grpc.DDLGeneratorStub(channel)
    try:
        yield stub
    finally:
        channel.close()


def get_sql_builder_stub() -> Generator[
    sql_builder_pb2_grpc.SQLBuilderStub,
    None,
    None,
]:
    """Create and yield a gRPC stub for the SQL Builder service."""
    channel = _create_channel(settings.SQL_BUILDER_CHANNEL)
    stub = sql_builder_pb2_grpc.SQLBuilderStub(channel)
    try:
        yield stub
    finally:
        channel.close()
