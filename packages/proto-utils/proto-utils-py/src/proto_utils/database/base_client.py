import asyncio
import logging
import time
from typing import Any, Awaitable, Callable, Optional, TypeVar

import grpc
from opentelemetry.propagate import inject
from proto_utils.database import dtypes
from proto_utils.database.database_serde import DatabaseSerde
from proto_utils.database.mongo_serde import MongoSerde
from proto_utils.database.redis_serde import RedisSerde
from proto_utils.generated.database.database_pb2_grpc import DatabaseServiceStub

T = TypeVar("T")


class DatabaseClient:
    # Retry only transient transport/capacity errors by default.
    DEFAULT_RETRYABLE_STATUS_CODES = {
        grpc.StatusCode.UNAVAILABLE,
        grpc.StatusCode.DEADLINE_EXCEEDED,
        grpc.StatusCode.RESOURCE_EXHAUSTED,
        grpc.StatusCode.ABORTED,
    }

    def __init__(
        self,
        channel_address: str,
        max_retries: int,
        retry_delay: float,
        backoff: float,
        logger: Optional[logging.Logger] = None,
        retryable_status_codes: Optional[set[grpc.StatusCode]] = None,
        rpc_timeout: Optional[float] = None,
        trace_context_enabled: bool = False,
    ) -> None:
        self._channel_address = channel_address
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.backoff = backoff
        self.rpc_timeout = rpc_timeout
        self.trace_context_enabled = trace_context_enabled

        if logger is None:
            logger = logging.getLogger(__name__)
        self.logger = logger

        self.retryable_status_codes = (
            retryable_status_codes
            if retryable_status_codes is not None
            else self.DEFAULT_RETRYABLE_STATUS_CODES
        )

        self._sync_channel: Optional[grpc.Channel] = None
        self._sync_stub: Optional[DatabaseServiceStub] = None
        self._async_channel: Optional[grpc.aio.Channel] = None
        self._async_stub: Optional[DatabaseServiceStub] = None

        self._initialize_sync_channel()

    def _trace_metadata(self) -> list[tuple[str, str]]:
        if not self.trace_context_enabled:
            return []

        carrier: dict[str, str] = {}
        inject(carrier)
        return [(key, value) for key, value in carrier.items() if value]

    def _rpc_kwargs(self) -> dict[str, Any]:
        kwargs: dict[str, Any] = {}
        if self.rpc_timeout is not None:
            kwargs["timeout"] = self.rpc_timeout

        trace_metadata = self._trace_metadata()
        if trace_metadata:
            kwargs["metadata"] = trace_metadata

        return kwargs

    def _is_retryable_rpc_error(self, error: grpc.RpcError) -> bool:
        return error.code() in self.retryable_status_codes

    def close(self) -> None:
        if self._sync_channel is not None:
            self._sync_channel.close()
            self._sync_channel = None
            self._sync_stub = None

    async def aclose(self) -> None:
        if self._async_channel is not None:
            await self._async_channel.close()
            self._async_channel = None
            self._async_stub = None

        self.close()

    def _initialize_sync_channel(self) -> None:
        if self._sync_channel:
            try:
                self.close()
            except Exception:
                pass

        self._sync_channel = grpc.insecure_channel(self._channel_address)
        self._sync_stub = DatabaseServiceStub(self._sync_channel)

    def _initialize_async_channel(self) -> None:
        self._async_channel = grpc.aio.insecure_channel(self._channel_address)
        self._async_stub = DatabaseServiceStub(self._async_channel)

    def _execute_with_retry(self, operation: Callable[[], T], operation_name: str) -> T:
        current_delay = self.retry_delay
        last_exception = None

        for attempt in range(1, self.max_retries + 1):
            try:
                if attempt > 1:
                    self.logger.info(
                        f"[DatabaseClient] Reinitializing channel for {operation_name} "
                        f"(attempt {attempt}/{self.max_retries})"
                    )
                    self._initialize_sync_channel()

                return operation()

            except grpc.RpcError as e:
                last_exception = e

                if not self._is_retryable_rpc_error(e):
                    self.logger.warning(
                        f"[DatabaseClient] {operation_name} failed with non-retryable "
                        f"error: {e.code()} - {e.details()}"
                    )
                    raise

                if attempt == self.max_retries:
                    self.logger.warning(
                        f"[DatabaseClient] {operation_name} failed after "
                        f"{self.max_retries} attempts: {e.code()} - {e.details()}"
                    )
                    raise

                self.logger.warning(
                    f"[DatabaseClient] {operation_name} failed "
                    f"(attempt {attempt}/{self.max_retries}): "
                    f"{e.code()} - {e.details()}. "
                    f"Retrying in {current_delay}s..."
                )
                time.sleep(current_delay)
                current_delay *= self.backoff

        raise (
            last_exception
            if last_exception
            else RuntimeError(f"{operation_name} failed without exception details.")
        )

    async def _execute_with_retry_async(
        self, operation: Callable[[], Awaitable[T]], operation_name: str
    ) -> T:
        current_delay = self.retry_delay
        last_exception = None

        for attempt in range(1, self.max_retries + 1):
            try:
                if self._async_stub is None:
                    self._initialize_async_channel()

                if attempt > 1:
                    self.logger.info(
                        f"[DatabaseClient] Reinitializing async channel for {operation_name} "
                        f"(attempt {attempt}/{self.max_retries})"
                    )
                    if self._async_channel is not None:
                        await self._async_channel.close()
                    self._initialize_async_channel()

                return await operation()

            except grpc.RpcError as e:
                last_exception = e

                if not self._is_retryable_rpc_error(e):
                    self.logger.warning(
                        f"[DatabaseClient] {operation_name} failed with non-retryable "
                        f"error: {e.code()} - {e.details()}"
                    )
                    raise

                if attempt == self.max_retries:
                    self.logger.warning(
                        f"[DatabaseClient] {operation_name} failed after "
                        f"{self.max_retries} attempts: {e.code()} - {e.details()}"
                    )
                    raise

                self.logger.warning(
                    f"[DatabaseClient] {operation_name} failed "
                    f"(attempt {attempt}/{self.max_retries}): "
                    f"{e.code()} - {e.details()}. "
                    f"Retrying in {current_delay}s..."
                )
                await asyncio.sleep(current_delay)
                current_delay *= self.backoff

        raise (
            last_exception
            if last_exception
            else RuntimeError(f"{operation_name} failed without exception details.")
        )

    def _sync_call(self, method_name: str, request_proto) -> Any:
        if self._sync_stub is None:
            raise RuntimeError("gRPC stub is not initialized.")
        return getattr(self._sync_stub, method_name)(request_proto, **self._rpc_kwargs())

    async def _async_call(self, method_name: str, request_proto) -> Any:
        if self._async_stub is None:
            self._initialize_async_channel()
        if self._async_stub is None:
            raise RuntimeError("gRPC async stub is not initialized.")
        return await getattr(self._async_stub, method_name)(
            request_proto, **self._rpc_kwargs()
        )

    def redis_get_keys(
        self, request: dtypes.RedisGetKeysRequest, retry_on_failure: bool = True
    ) -> dtypes.RedisGetKeysResponse:
        def _operation() -> dtypes.RedisGetKeysResponse:
            request_proto = RedisSerde.serialize_get_keys_request(request)
            response = self._sync_call("RedisGetKeys", request_proto)
            return RedisSerde.deserialize_get_keys_response(response)

        if retry_on_failure:
            return self._execute_with_retry(_operation, "RedisGetKeys")
        return _operation()

    async def redis_get_keys_async(
        self, request: dtypes.RedisGetKeysRequest, retry_on_failure: bool = True
    ) -> dtypes.RedisGetKeysResponse:
        async def _operation() -> dtypes.RedisGetKeysResponse:
            request_proto = RedisSerde.serialize_get_keys_request(request)
            response = await self._async_call("RedisGetKeys", request_proto)
            return RedisSerde.deserialize_get_keys_response(response)

        if retry_on_failure:
            return await self._execute_with_retry_async(_operation, "RedisGetKeys")
        return await _operation()

    def redis_set(
        self, request: dtypes.RedisSetRequest, retry_on_failure: bool = True
    ) -> dtypes.RedisSetResponse:
        def _operation() -> dtypes.RedisSetResponse:
            request_proto = RedisSerde.serialize_set_request(request)
            response = self._sync_call("RedisSet", request_proto)
            return RedisSerde.deserialize_set_response(response)

        if retry_on_failure:
            return self._execute_with_retry(_operation, "RedisSet")
        return _operation()

    async def redis_set_async(
        self, request: dtypes.RedisSetRequest, retry_on_failure: bool = True
    ) -> dtypes.RedisSetResponse:
        async def _operation() -> dtypes.RedisSetResponse:
            request_proto = RedisSerde.serialize_set_request(request)
            response = await self._async_call("RedisSet", request_proto)
            return RedisSerde.deserialize_set_response(response)

        if retry_on_failure:
            return await self._execute_with_retry_async(_operation, "RedisSet")
        return await _operation()

    def redis_get(
        self, request: dtypes.RedisGetRequest, retry_on_failure: bool = True
    ) -> dtypes.RedisGetResponse:
        def _operation() -> dtypes.RedisGetResponse:
            request_proto = RedisSerde.serialize_get_request(request)
            response = self._sync_call("RedisGet", request_proto)
            return RedisSerde.deserialize_get_response(response)

        if retry_on_failure:
            return self._execute_with_retry(_operation, "RedisGet")
        return _operation()

    async def redis_get_async(
        self, request: dtypes.RedisGetRequest, retry_on_failure: bool = True
    ) -> dtypes.RedisGetResponse:
        async def _operation() -> dtypes.RedisGetResponse:
            request_proto = RedisSerde.serialize_get_request(request)
            response = await self._async_call("RedisGet", request_proto)
            return RedisSerde.deserialize_get_response(response)

        if retry_on_failure:
            return await self._execute_with_retry_async(_operation, "RedisGet")
        return await _operation()

    def redis_delete(
        self, request: dtypes.RedisDeleteRequest, retry_on_failure: bool = True
    ) -> dtypes.RedisDeleteResponse:
        def _operation() -> dtypes.RedisDeleteResponse:
            request_proto = RedisSerde.serialize_delete_request(request)
            response = self._sync_call("RedisDelete", request_proto)
            return RedisSerde.deserialize_delete_response(response)

        if retry_on_failure:
            return self._execute_with_retry(_operation, "RedisDelete")
        return _operation()

    async def redis_delete_async(
        self, request: dtypes.RedisDeleteRequest, retry_on_failure: bool = True
    ) -> dtypes.RedisDeleteResponse:
        async def _operation() -> dtypes.RedisDeleteResponse:
            request_proto = RedisSerde.serialize_delete_request(request)
            response = await self._async_call("RedisDelete", request_proto)
            return RedisSerde.deserialize_delete_response(response)

        if retry_on_failure:
            return await self._execute_with_retry_async(_operation, "RedisDelete")
        return await _operation()

    def redis_ping(
        self,
        request: Optional[dtypes.RedisPingRequest] = None,
        retry_on_failure: bool = True,
    ) -> dtypes.RedisPingResponse:
        def _operation() -> dtypes.RedisPingResponse:
            local_request = request if request is not None else dtypes.RedisPingRequest()
            request_proto = RedisSerde.serialize_ping_request(local_request)
            response = self._sync_call("RedisPing", request_proto)
            return RedisSerde.deserialize_ping_response(response)

        if retry_on_failure:
            return self._execute_with_retry(_operation, "RedisPing")
        return _operation()

    async def redis_ping_async(
        self,
        request: Optional[dtypes.RedisPingRequest] = None,
        retry_on_failure: bool = True,
    ) -> dtypes.RedisPingResponse:
        async def _operation() -> dtypes.RedisPingResponse:
            local_request = request if request is not None else dtypes.RedisPingRequest()
            request_proto = RedisSerde.serialize_ping_request(local_request)
            response = await self._async_call("RedisPing", request_proto)
            return RedisSerde.deserialize_ping_response(response)

        if retry_on_failure:
            return await self._execute_with_retry_async(_operation, "RedisPing")
        return await _operation()

    def redis_get_cache(
        self,
        request: Optional[dtypes.RedisGetCacheRequest] = None,
        retry_on_failure: bool = True,
    ) -> dtypes.RedisGetCacheResponse:
        def _operation() -> dtypes.RedisGetCacheResponse:
            local_request = (
                request if request is not None else dtypes.RedisGetCacheRequest()
            )
            request_proto = RedisSerde.serialize_get_cache_request(local_request)
            response = self._sync_call("RedisGetCache", request_proto)
            return RedisSerde.deserialize_get_cache_response(response)

        if retry_on_failure:
            return self._execute_with_retry(_operation, "RedisGetCache")
        return _operation()

    async def redis_get_cache_async(
        self,
        request: Optional[dtypes.RedisGetCacheRequest] = None,
        retry_on_failure: bool = True,
    ) -> dtypes.RedisGetCacheResponse:
        async def _operation() -> dtypes.RedisGetCacheResponse:
            local_request = (
                request if request is not None else dtypes.RedisGetCacheRequest()
            )
            request_proto = RedisSerde.serialize_get_cache_request(local_request)
            response = await self._async_call("RedisGetCache", request_proto)
            return RedisSerde.deserialize_get_cache_response(response)

        if retry_on_failure:
            return await self._execute_with_retry_async(_operation, "RedisGetCache")
        return await _operation()

    def clear_cache(
        self,
        request: Optional[dtypes.RedisClearCacheRequest] = None,
        retry_on_failure: bool = True,
    ) -> dtypes.RedisClearCacheResponse:
        def _operation() -> dtypes.RedisClearCacheResponse:
            local_request = (
                request if request is not None else dtypes.RedisClearCacheRequest()
            )
            request_proto = RedisSerde.serialize_clear_cache_request(local_request)
            response = self._sync_call("RedisClearCache", request_proto)
            return RedisSerde.deserialize_clear_cache_response(response)

        if retry_on_failure:
            return self._execute_with_retry(_operation, "RedisClearCache")
        return _operation()

    async def clear_cache_async(
        self,
        request: Optional[dtypes.RedisClearCacheRequest] = None,
        retry_on_failure: bool = True,
    ) -> dtypes.RedisClearCacheResponse:
        async def _operation() -> dtypes.RedisClearCacheResponse:
            local_request = (
                request if request is not None else dtypes.RedisClearCacheRequest()
            )
            request_proto = RedisSerde.serialize_clear_cache_request(local_request)
            response = await self._async_call("RedisClearCache", request_proto)
            return RedisSerde.deserialize_clear_cache_response(response)

        if retry_on_failure:
            return await self._execute_with_retry_async(_operation, "RedisClearCache")
        return await _operation()

    def mongo_ping(
        self,
        request: Optional[dtypes.MongoPingRequest] = None,
        retry_on_failure: bool = True,
    ) -> dtypes.MongoPingResponse:
        def _operation() -> dtypes.MongoPingResponse:
            local_request = request if request is not None else dtypes.MongoPingRequest()
            request_proto = MongoSerde.serialize_ping_request(local_request)
            response = self._sync_call("MongoPing", request_proto)
            return MongoSerde.deserialize_ping_response(response)

        if retry_on_failure:
            return self._execute_with_retry(_operation, "MongoPing")
        return _operation()

    async def mongo_ping_async(
        self,
        request: Optional[dtypes.MongoPingRequest] = None,
        retry_on_failure: bool = True,
    ) -> dtypes.MongoPingResponse:
        async def _operation() -> dtypes.MongoPingResponse:
            local_request = request if request is not None else dtypes.MongoPingRequest()
            request_proto = MongoSerde.serialize_ping_request(local_request)
            response = await self._async_call("MongoPing", request_proto)
            return MongoSerde.deserialize_ping_response(response)

        if retry_on_failure:
            return await self._execute_with_retry_async(_operation, "MongoPing")
        return await _operation()

    def mongo_get_raw_schemas(
        self, request: dtypes.MongoGetRawSchemasRequest, retry_on_failure: bool = True
    ) -> dtypes.MongoGetRawSchemasResponse:
        def _operation() -> dtypes.MongoGetRawSchemasResponse:
            request_proto = MongoSerde.serialize_get_raw_schemas_request(request)
            response = self._sync_call("MongoGetRawSchemas", request_proto)
            return MongoSerde.deserialize_get_raw_schemas_response(response)

        if retry_on_failure:
            return self._execute_with_retry(_operation, "MongoGetRawSchemas")
        return _operation()

    async def mongo_get_raw_schemas_async(
        self, request: dtypes.MongoGetRawSchemasRequest, retry_on_failure: bool = True
    ) -> dtypes.MongoGetRawSchemasResponse:
        async def _operation() -> dtypes.MongoGetRawSchemasResponse:
            request_proto = MongoSerde.serialize_get_raw_schemas_request(request)
            response = await self._async_call("MongoGetRawSchemas", request_proto)
            return MongoSerde.deserialize_get_raw_schemas_response(response)

        if retry_on_failure:
            return await self._execute_with_retry_async(_operation, "MongoGetRawSchemas")
        return await _operation()

    def mongo_get_schemas_by_import_regex(
        self,
        request: dtypes.MongoGetSchemasByImportRegexRequest,
        retry_on_failure: bool = True,
    ) -> dtypes.MongoGetSchemasByImportRegexResponse:
        def _operation() -> dtypes.MongoGetSchemasByImportRegexResponse:
            request_proto = MongoSerde.serialize_get_schemas_by_import_regex_request(
                request
            )
            response = self._sync_call("MongoGetSchemasByImportRegex", request_proto)
            return MongoSerde.deserialize_get_schemas_by_import_regex_response(response)

        if retry_on_failure:
            return self._execute_with_retry(_operation, "MongoGetSchemasByImportRegex")
        return _operation()

    async def mongo_get_schemas_by_import_regex_async(
        self,
        request: dtypes.MongoGetSchemasByImportRegexRequest,
        retry_on_failure: bool = True,
    ) -> dtypes.MongoGetSchemasByImportRegexResponse:
        async def _operation() -> dtypes.MongoGetSchemasByImportRegexResponse:
            request_proto = MongoSerde.serialize_get_schemas_by_import_regex_request(
                request
            )
            response = await self._async_call("MongoGetSchemasByImportRegex", request_proto)
            return MongoSerde.deserialize_get_schemas_by_import_regex_response(response)

        if retry_on_failure:
            return await self._execute_with_retry_async(
                _operation, "MongoGetSchemasByImportRegex"
            )
        return await _operation()

    def mongo_insert_one_schema(
        self, request: dtypes.MongoInsertOneSchemaRequest, retry_on_failure: bool = True
    ) -> dtypes.MongoInsertOneSchemaResponse:
        def _operation() -> dtypes.MongoInsertOneSchemaResponse:
            request_proto = MongoSerde.serialize_insert_one_schema_request(request)
            response = self._sync_call("MongoInsertOneSchema", request_proto)
            return MongoSerde.deserialize_insert_one_schema_response(response)

        if retry_on_failure:
            return self._execute_with_retry(_operation, "MongoInsertOneSchema")
        return _operation()

    async def mongo_insert_one_schema_async(
        self, request: dtypes.MongoInsertOneSchemaRequest, retry_on_failure: bool = True
    ) -> dtypes.MongoInsertOneSchemaResponse:
        async def _operation() -> dtypes.MongoInsertOneSchemaResponse:
            request_proto = MongoSerde.serialize_insert_one_schema_request(request)
            response = await self._async_call("MongoInsertOneSchema", request_proto)
            return MongoSerde.deserialize_insert_one_schema_response(response)

        if retry_on_failure:
            return await self._execute_with_retry_async(_operation, "MongoInsertOneSchema")
        return await _operation()

    def mongo_count_all_documents(
        self,
        request: Optional[dtypes.MongoCountAllDocumentsRequest] = None,
        retry_on_failure: bool = True,
    ) -> dtypes.MongoCountAllDocumentsResponse:
        def _operation() -> dtypes.MongoCountAllDocumentsResponse:
            local_request = (
                request if request is not None else dtypes.MongoCountAllDocumentsRequest()
            )
            request_proto = MongoSerde.serialize_count_all_documents_request(
                local_request
            )
            response = self._sync_call("MongoCountAllDocuments", request_proto)
            return MongoSerde.deserialize_count_all_documents_response(response)

        if retry_on_failure:
            return self._execute_with_retry(_operation, "MongoCountAllDocuments")
        return _operation()

    async def mongo_count_all_documents_async(
        self,
        request: Optional[dtypes.MongoCountAllDocumentsRequest] = None,
        retry_on_failure: bool = True,
    ) -> dtypes.MongoCountAllDocumentsResponse:
        async def _operation() -> dtypes.MongoCountAllDocumentsResponse:
            local_request = (
                request if request is not None else dtypes.MongoCountAllDocumentsRequest()
            )
            request_proto = MongoSerde.serialize_count_all_documents_request(
                local_request
            )
            response = await self._async_call("MongoCountAllDocuments", request_proto)
            return MongoSerde.deserialize_count_all_documents_response(response)

        if retry_on_failure:
            return await self._execute_with_retry_async(_operation, "MongoCountAllDocuments")
        return await _operation()

    def mongo_find_jsonschema(
        self, request: dtypes.MongoFindJsonSchemaRequest, retry_on_failure: bool = True
    ) -> dtypes.MongoFindJsonSchemaResponse:
        def _operation() -> dtypes.MongoFindJsonSchemaResponse:
            request_proto = MongoSerde.serialize_find_jsonschema_request(request)
            response = self._sync_call("MongoFindJsonSchema", request_proto)
            return MongoSerde.deserialize_find_jsonschema_response(response)

        if retry_on_failure:
            return self._execute_with_retry(_operation, "MongoFindJsonSchema")
        return _operation()

    async def mongo_find_jsonschema_async(
        self, request: dtypes.MongoFindJsonSchemaRequest, retry_on_failure: bool = True
    ) -> dtypes.MongoFindJsonSchemaResponse:
        async def _operation() -> dtypes.MongoFindJsonSchemaResponse:
            request_proto = MongoSerde.serialize_find_jsonschema_request(request)
            response = await self._async_call("MongoFindJsonSchema", request_proto)
            return MongoSerde.deserialize_find_jsonschema_response(response)

        if retry_on_failure:
            return await self._execute_with_retry_async(_operation, "MongoFindJsonSchema")
        return await _operation()

    def mongo_update_one_jsonschema(
        self,
        request: dtypes.MongoUpdateOneJsonSchemaRequest,
        retry_on_failure: bool = True,
    ) -> dtypes.MongoUpdateOneJsonSchemaResponse:
        def _operation() -> dtypes.MongoUpdateOneJsonSchemaResponse:
            request_proto = MongoSerde.serialize_update_one_jsonschema_request(request)
            response = self._sync_call("MongoUpdateOneJsonSchema", request_proto)
            return MongoSerde.deserialize_update_one_jsonschema_response(response)

        if retry_on_failure:
            return self._execute_with_retry(_operation, "MongoUpdateOneJsonSchema")
        return _operation()

    async def mongo_update_one_jsonschema_async(
        self,
        request: dtypes.MongoUpdateOneJsonSchemaRequest,
        retry_on_failure: bool = True,
    ) -> dtypes.MongoUpdateOneJsonSchemaResponse:
        async def _operation() -> dtypes.MongoUpdateOneJsonSchemaResponse:
            request_proto = MongoSerde.serialize_update_one_jsonschema_request(request)
            response = await self._async_call("MongoUpdateOneJsonSchema", request_proto)
            return MongoSerde.deserialize_update_one_jsonschema_response(response)

        if retry_on_failure:
            return await self._execute_with_retry_async(
                _operation, "MongoUpdateOneJsonSchema"
            )
        return await _operation()

    def mongo_delete_one_jsonschema(
        self,
        request: dtypes.MongoDeleteOneJsonSchemaRequest,
        retry_on_failure: bool = True,
    ) -> dtypes.MongoDeleteOneJsonSchemaResponse:
        def _operation() -> dtypes.MongoDeleteOneJsonSchemaResponse:
            request_proto = MongoSerde.serialize_delete_one_jsonschema_request(request)
            response = self._sync_call("MongoDeleteOneJsonSchema", request_proto)
            return MongoSerde.deserialize_delete_one_jsonschema_response(response)

        if retry_on_failure:
            return self._execute_with_retry(_operation, "MongoDeleteOneJsonSchema")
        return _operation()

    async def mongo_delete_one_jsonschema_async(
        self,
        request: dtypes.MongoDeleteOneJsonSchemaRequest,
        retry_on_failure: bool = True,
    ) -> dtypes.MongoDeleteOneJsonSchemaResponse:
        async def _operation() -> dtypes.MongoDeleteOneJsonSchemaResponse:
            request_proto = MongoSerde.serialize_delete_one_jsonschema_request(request)
            response = await self._async_call("MongoDeleteOneJsonSchema", request_proto)
            return MongoSerde.deserialize_delete_one_jsonschema_response(response)

        if retry_on_failure:
            return await self._execute_with_retry_async(
                _operation, "MongoDeleteOneJsonSchema"
            )
        return await _operation()

    def mongo_delete_import_name(
        self,
        request: dtypes.MongoDeleteImportNameRequest,
        retry_on_failure: bool = True,
    ) -> dtypes.MongoDeleteImportNameResponse:
        def _operation() -> dtypes.MongoDeleteImportNameResponse:
            request_proto = MongoSerde.serialize_delete_import_name_request(request)
            response = self._sync_call("MongoDeleteImportName", request_proto)
            return MongoSerde.deserialize_delete_import_name_response(response)

        if retry_on_failure:
            return self._execute_with_retry(_operation, "MongoDeleteImportName")
        return _operation()

    async def mongo_delete_import_name_async(
        self,
        request: dtypes.MongoDeleteImportNameRequest,
        retry_on_failure: bool = True,
    ) -> dtypes.MongoDeleteImportNameResponse:
        async def _operation() -> dtypes.MongoDeleteImportNameResponse:
            request_proto = MongoSerde.serialize_delete_import_name_request(request)
            response = await self._async_call("MongoDeleteImportName", request_proto)
            return MongoSerde.deserialize_delete_import_name_response(response)

        if retry_on_failure:
            return await self._execute_with_retry_async(_operation, "MongoDeleteImportName")
        return await _operation()

    def update_task_id(
        self, request: dtypes.UpdateTaskIdRequest, retry_on_failure: bool = True
    ) -> dtypes.UpdateTaskIdResponse:
        def _operation() -> dtypes.UpdateTaskIdResponse:
            request_proto = DatabaseSerde.serialize_update_task_id_request(request)
            response = self._sync_call("UpdateTaskId", request_proto)
            return DatabaseSerde.deserialize_update_task_id_response(response)

        if retry_on_failure:
            return self._execute_with_retry(_operation, "UpdateTaskId")
        return _operation()

    async def update_task_id_async(
        self, request: dtypes.UpdateTaskIdRequest, retry_on_failure: bool = True
    ) -> dtypes.UpdateTaskIdResponse:
        async def _operation() -> dtypes.UpdateTaskIdResponse:
            request_proto = DatabaseSerde.serialize_update_task_id_request(request)
            response = await self._async_call("UpdateTaskId", request_proto)
            return DatabaseSerde.deserialize_update_task_id_response(response)

        if retry_on_failure:
            return await self._execute_with_retry_async(_operation, "UpdateTaskId")
        return await _operation()

    def get_task_id(
        self, request: dtypes.GetTaskIdRequest, retry_on_failure: bool = True
    ) -> dtypes.GetTaskIdResponse:
        def _operation() -> dtypes.GetTaskIdResponse:
            request_proto = DatabaseSerde.serialize_get_task_id_request(request)
            response = self._sync_call("GetTaskId", request_proto)
            return DatabaseSerde.deserialize_get_task_id_response(response)

        if retry_on_failure:
            return self._execute_with_retry(_operation, "GetTaskId")
        return _operation()

    async def get_task_id_async(
        self, request: dtypes.GetTaskIdRequest, retry_on_failure: bool = True
    ) -> dtypes.GetTaskIdResponse:
        async def _operation() -> dtypes.GetTaskIdResponse:
            request_proto = DatabaseSerde.serialize_get_task_id_request(request)
            response = await self._async_call("GetTaskId", request_proto)
            return DatabaseSerde.deserialize_get_task_id_response(response)

        if retry_on_failure:
            return await self._execute_with_retry_async(_operation, "GetTaskId")
        return await _operation()

    def get_tasks_by_import_name(
        self, request: dtypes.GetTasksByImportNameRequest, retry_on_failure: bool = True
    ) -> dtypes.GetTasksByImportNameResponse:
        def _operation() -> dtypes.GetTasksByImportNameResponse:
            request_proto = DatabaseSerde.serialize_get_tasks_by_import_name_request(
                request
            )
            response = self._sync_call("GetTasksByImportName", request_proto)
            return DatabaseSerde.deserialize_get_tasks_by_import_name_response(response)

        if retry_on_failure:
            return self._execute_with_retry(_operation, "GetTasksByImportName")
        return _operation()

    async def get_tasks_by_import_name_async(
        self, request: dtypes.GetTasksByImportNameRequest, retry_on_failure: bool = True
    ) -> dtypes.GetTasksByImportNameResponse:
        async def _operation() -> dtypes.GetTasksByImportNameResponse:
            request_proto = DatabaseSerde.serialize_get_tasks_by_import_name_request(
                request
            )
            response = await self._async_call("GetTasksByImportName", request_proto)
            return DatabaseSerde.deserialize_get_tasks_by_import_name_response(response)

        if retry_on_failure:
            return await self._execute_with_retry_async(
                _operation, "GetTasksByImportName"
            )
        return await _operation()

    def set_task_id(
        self, request: dtypes.SetTaskIdRequest, retry_on_failure: bool = True
    ) -> dtypes.SetTaskIdResponse:
        def _operation() -> dtypes.SetTaskIdResponse:
            request_proto = DatabaseSerde.serialize_set_task_id_request(request)
            response = self._sync_call("SetTaskId", request_proto)
            return DatabaseSerde.deserialize_set_task_id_response(response)

        if retry_on_failure:
            return self._execute_with_retry(_operation, "SetTaskId")
        return _operation()

    async def set_task_id_async(
        self, request: dtypes.SetTaskIdRequest, retry_on_failure: bool = True
    ) -> dtypes.SetTaskIdResponse:
        async def _operation() -> dtypes.SetTaskIdResponse:
            request_proto = DatabaseSerde.serialize_set_task_id_request(request)
            response = await self._async_call("SetTaskId", request_proto)
            return DatabaseSerde.deserialize_set_task_id_response(response)

        if retry_on_failure:
            return await self._execute_with_retry_async(_operation, "SetTaskId")
        return await _operation()

    def remove_task_id(
        self, request: dtypes.RemoveTaskIdRequest, retry_on_failure: bool = True
    ) -> dtypes.RemoveTaskIdResponse:
        def _operation() -> dtypes.RemoveTaskIdResponse:
            request_proto = DatabaseSerde.serialize_remove_task_id_request(request)
            response = self._sync_call("RemoveTaskId", request_proto)
            return DatabaseSerde.deserialize_remove_task_id_response(response)

        if retry_on_failure:
            return self._execute_with_retry(_operation, "RemoveTaskId")
        return _operation()

    async def remove_task_id_async(
        self, request: dtypes.RemoveTaskIdRequest, retry_on_failure: bool = True
    ) -> dtypes.RemoveTaskIdResponse:
        async def _operation() -> dtypes.RemoveTaskIdResponse:
            request_proto = DatabaseSerde.serialize_remove_task_id_request(request)
            response = await self._async_call("RemoveTaskId", request_proto)
            return DatabaseSerde.deserialize_remove_task_id_response(response)

        if retry_on_failure:
            return await self._execute_with_retry_async(_operation, "RemoveTaskId")
        return await _operation()
