import time
from typing import Protocol, runtime_checkable

import pymongo.errors
from proto_utils.database.mongo_serde import MongoSerde
from proto_utils.generated.database import mongo_pb2

from src.core.database_mongo import MongoConnection
from src.handlers.base import BaseHandler, RequestT, ResponseT
from src.services.mongo import MongoSchemasService


@runtime_checkable
class MongoOperation(Protocol[RequestT, ResponseT]):
    def __call__(
        self,
        request: RequestT,
        /,
        *,
        mongo_schemas_connection: MongoConnection,
    ) -> ResponseT: ...


class MongoHandler(BaseHandler):
    def __init__(self):
        super().__init__()

    def _execute_with_retry(
        self,
        operation: MongoOperation[RequestT, ResponseT],
        request: RequestT,
        retry_on_failure: bool = False,
    ) -> ResponseT:
        current_delay = self.retry_delay_mongo
        last_exception = None
        retries = self.max_retries_mongo if retry_on_failure else 1

        for attempt in range(1, retries + 1):
            try:
                mongo_db = self.manager.get_mongo_schemas_connection(attempt > 1)
                return operation(request, mongo_schemas_connection=mongo_db)
            except (
                pymongo.errors.ConnectionFailure,
                pymongo.errors.ServerSelectionTimeoutError,
            ) as e:
                last_exception = e
                if attempt == retries:
                    raise

                time.sleep(current_delay)
                current_delay *= self.backoff_mongo

        # just in case
        if last_exception:
            raise last_exception
        raise Exception("Unknown error during MongoDB operation")

    def ping(self, request: mongo_pb2.MongoPingRequest) -> mongo_pb2.MongoPingResponse:
        deserialized_request = MongoSerde.deserialize_ping_request(request)
        service_response = self._execute_with_retry(
            MongoSchemasService.ping, deserialized_request
        )
        return MongoSerde.serialize_ping_response(service_response)

    def get_raw_schemas(
        self,
        request: mongo_pb2.MongoGetRawSchemasRequest,
    ) -> mongo_pb2.MongoGetRawSchemasResponse:
        deserialized_request = MongoSerde.deserialize_get_raw_schemas_request(request)

        service_response = self._execute_with_retry(
            MongoSchemasService.get_raw_schemas,
            deserialized_request,
        )
        if service_response is None:
            return mongo_pb2.MongoGetRawSchemasResponse()
        return MongoSerde.serialize_get_raw_schemas_response(service_response)

    def get_schemas_by_import_regex(
        self,
        request: mongo_pb2.MongoGetSchemasByImportRegexRequest,
    ) -> mongo_pb2.MongoGetSchemasByImportRegexResponse:
        deserialized_request = (
            MongoSerde.deserialize_get_schemas_by_import_regex_request(request)
        )

        service_response = self._execute_with_retry(
            MongoSchemasService.get_schemas_by_import_regex,
            deserialized_request,
        )
        if service_response is None:
            return mongo_pb2.MongoGetSchemasByImportRegexResponse(schemas=[])

        return MongoSerde.serialize_get_schemas_by_import_regex_response(
            service_response
        )

    def insert_one_schema(
        self,
        request: mongo_pb2.MongoInsertOneSchemaRequest,
    ) -> mongo_pb2.MongoInsertOneSchemaResponse:
        deserialized_request = MongoSerde.deserialize_insert_one_schema_request(request)

        service_response = self._execute_with_retry(
            MongoSchemasService.insert_one_schema,
            deserialized_request,
        )
        return MongoSerde.serialize_insert_one_schema_response(service_response)

    def count_all_documents(
        self,
        request: mongo_pb2.MongoCountAllDocumentsRequest,
    ) -> mongo_pb2.MongoCountAllDocumentsResponse:
        deserialized_request = MongoSerde.deserialize_count_all_documents_request(
            request
        )

        service_response = self._execute_with_retry(
            MongoSchemasService.count_all_documents,
            deserialized_request,
        )
        return MongoSerde.serialize_count_all_documents_response(service_response)

    def find_jsonschema(
        self,
        request: mongo_pb2.MongoFindJsonSchemaRequest,
    ) -> mongo_pb2.MongoFindJsonSchemaResponse:
        deserialized_request = MongoSerde.deserialize_find_jsonschema_request(request)

        service_response = self._execute_with_retry(
            MongoSchemasService.find_one_jsonschema,
            deserialized_request,
        )
        return MongoSerde.serialize_find_jsonschema_response(service_response)

    def update_one_jsonschema(
        self,
        request: mongo_pb2.MongoUpdateOneJsonSchemaRequest,
    ) -> mongo_pb2.MongoUpdateOneJsonSchemaResponse:
        deserialized_request = MongoSerde.deserialize_update_one_jsonschema_request(
            request
        )

        service_response = self._execute_with_retry(
            MongoSchemasService.update_one_schema,
            deserialized_request,
        )
        return MongoSerde.serialize_update_one_jsonschema_response(service_response)

    def delete_one_jsonschema(
        self,
        request: mongo_pb2.MongoDeleteOneJsonSchemaRequest,
    ) -> mongo_pb2.MongoDeleteOneJsonSchemaResponse:
        deserialized_request = MongoSerde.deserialize_delete_one_jsonschema_request(
            request
        )

        service_response = self._execute_with_retry(
            MongoSchemasService.delete_one_schema,
            deserialized_request,
        )
        return MongoSerde.serialize_delete_one_jsonschema_response(service_response)

    def delete_import_name(
        self,
        request: mongo_pb2.MongoDeleteImportNameRequest,
    ) -> mongo_pb2.MongoDeleteImportNameResponse:
        deserialized_request = MongoSerde.deserialize_delete_import_name_request(
            request
        )

        service_response = self._execute_with_retry(
            MongoSchemasService.delete_import_name,
            deserialized_request,
        )
        return MongoSerde.serialize_delete_import_name_response(service_response)
