"""Schema Handlers Module.

This module provides handler functions for schema operations that interact
directly with the database service. These functions are used by the API
endpoints to perform synchronous schema operations without requiring RabbitMQ.

The handlers manage JSON schema validation, creation, storage, and retrieval
using the DatabaseClient to communicate with the MongoDB service via gRPC.
"""

from typing import Any, Dict, Literal, Optional

from jsonschema import (
    Draft3Validator,
    Draft4Validator,
    Draft6Validator,
    Draft7Validator,
    Draft201909Validator,
    Draft202012Validator,
    SchemaError,
)
from proto_utils.database import dtypes
from proto_utils.database.base_client import DatabaseClient

from src import schemas
from src.exceptions import (
    InvalidJsonSchemaDraftException,
    InvalidJsonSchemaException,
    InvalidJsonSchemaTypeException,
    MissingJsonSchemaDraftException,
)
from src.utils import utc_now_iso


class SchemaService:
    @staticmethod
    def parse_raw_schema_to_api(
        raw_schema: dtypes.JsonSchema,
    ) -> schemas.JsonSchemaRequest:
        """
        Convert a raw schema from the database format to the API response format.

        This function transforms the raw schema document retrieved from the database
        into the format expected by the API clients, including restructuring properties
        and ensuring the $schema field is included.

        Args:
            raw_schema (dtypes.JsonSchema): The raw schema document from the database.
        Returns:
            schemas.JsonSchemaRequest: The schema formatted for API responses.
        """
        # Start with the base structure
        api_schema: schemas.JsonSchemaRequest = {
            "$schema": raw_schema.get(
                "schema", "https://json-schema.org/draft-07/schema"
            ),
            "type": "object",  # Assuming root type is always object for our use case
            "properties": {},
            "required": raw_schema.get("required", []),
        }

        # Transform properties back to API format
        for prop_name, prop_info in raw_schema.get("properties", {}).items():
            api_schema["properties"][prop_name] = {
                "type": prop_info.get(
                    "type", "string"
                ),  # Default to string if type is missing
                **prop_info.get("extra", {}),  # Include any extra properties
            }

        return api_schema

    @staticmethod
    def parse_get_raw_schema(
        schema_doc: dtypes.MongoGetRawSchemasResponse,
    ) -> schemas.MongoSchemasResponse:
        return schemas.MongoSchemasResponse(
            id=schema_doc["id"],
            import_name=schema_doc["import_name"],
            created_at=schema_doc["created_at"],
            active_schema=SchemaService.parse_raw_schema_to_api(
                raw_schema=schema_doc["active_schema"]
            ),
            schemas_releases=list(
                map(
                    lambda release: schemas.MongoSchemasResponseSchemaRelease(
                        created_at=release["created_at"],
                        schema=SchemaService.parse_raw_schema_to_api(
                            raw_schema=release["schema"]
                        ),
                    ),
                    schema_doc.get("schemas_releases", []),
                )
            ),
        )

    @staticmethod
    async def get_raw_schema(
        import_name: str, database_client: DatabaseClient
    ) -> Optional[schemas.MongoSchemasResponse]:
        """
        Fetch the raw JSON schema for a given import name.

        Args:
            import_name (str): The name of the import to fetch the schema for.
            database_client (DatabaseClient): The database client to use for fetching the schema.
        Returns:
            schemas.MongoSchemasResponse | None: The raw schema response if found, None otherwise.
        """
        schema_doc = await database_client.mongo_get_raw_schemas_async(
            dtypes.MongoGetRawSchemasRequest(import_name=import_name)
        )

        if schema_doc["id"] == "":
            return None
        return SchemaService.parse_get_raw_schema(schema_doc)

    @staticmethod
    async def get_schemas_by_project_id(
        project_id: str, database_client: DatabaseClient
    ) -> schemas.MongoGetSchemasByImportResponse:
        """
        Fetch schemas that match a given regular expression.

        Args:
            project_id (str): The project ID to match in the import name.
            database_client (DatabaseClient): The database client to use for fetching the schemas.

        Returns:
            schemas.MongoGetSchemasByImportResponse: The response containing matching schemas.
        """
        response = await database_client.mongo_get_schemas_by_import_regex_async(
            dtypes.MongoGetSchemasByImportRegexRequest(import_name=f"{project_id}")
        )

        return schemas.MongoGetSchemasByImportResponse(
            schemas=list(
                map(SchemaService.parse_get_raw_schema, response.get("schemas", []))
            )
        )

    @staticmethod
    async def get_active_schema(
        import_name: str, database_client: DatabaseClient
    ) -> Optional[schemas.JsonSchemaRequest]:
        """
        Get the active schema for a given import name.

        Args:
            import_name (str): The name of the import.
            database_client (DatabaseClient): The database client to use for fetching the schema.

        Returns:
            schemas.JsonSchemaRequest | None: The active schema if found, None otherwise.
        """
        schema_doc = await database_client.mongo_find_jsonschema_async(
            dtypes.MongoFindJsonSchemaRequest(import_name=import_name)
        )

        # return schema_doc["schema"] if schema_doc["status"] == "found" else None
        if schema_doc["status"] != "found" or schema_doc.get("schema", None) is None:
            return None

        return SchemaService.parse_raw_schema_to_api(raw_schema=schema_doc["schema"])  # type: ignore

    @staticmethod
    def _validate_jsonschema(schema: schemas.JsonSchemaRequest) -> None:
        # Ensure the schema is of type 'object' at the root level
        if schema.get("type", "") != "object":
            raise InvalidJsonSchemaTypeException()

        schema_value = schema.get("$schema", None)
        if schema_value is None:
            raise MissingJsonSchemaDraftException()

        # TODO: Make this more robust to handle different URL formats and potential variations in the $schema field
        # This is a simplified parsing logic that assumes the $schema field follows the standard format.
        draft_version = schema_value.split("json-schema.org/", 1)[-1].split(
            "/schema", 1
        )[0]

        validator_cls = {
            "draft-07": Draft7Validator,
            "draft/2019-09": Draft201909Validator,
            "draft/2020-12": Draft202012Validator,
            "draft-06": Draft6Validator,
            "draft-05": Draft4Validator,  # Just in case someone uses: https://json-schema.org/draft-05
            "draft-04": Draft4Validator,
            "draft-03": Draft3Validator,
        }.get(draft_version, None)
        if validator_cls is None:
            raise InvalidJsonSchemaDraftException()

        try:
            validator_cls.check_schema(schema)
        except SchemaError:
            raise InvalidJsonSchemaException()

    @staticmethod
    async def save_schema(
        orig_schema: schemas.JsonSchemaRequest,
        import_name: str,
        database_client: DatabaseClient,
    ) -> dtypes.MongoInsertOneSchemaResponse:
        """
        Save the schema to the MongoDB collection.

        This function processes the schema and saves it to the database. If a schema
        with the same import_name already exists, it will be updated. The function
        transforms the schema properties into a storage-friendly format.

        Args:
            schema (dict): The JSON schema to save.
            import_name (str): The name of the import, used as a unique identifier.
            database_client (DatabaseClient): The database client to use for saving the schema.

        Returns:
            dtypes.MongoInsertOneSchemaResponse: The result of the insert or update operation
                with status ('inserted', 'no_change', 'updated', or 'error').
        """
        SchemaService._validate_jsonschema(orig_schema)

        # Extract and normalize the $schema field
        schema_key_value = orig_schema.pop(
            "$schema", "https://json-schema.org/draft-07/schema"
        )

        # Create a copy to avoid mutating the original input
        schema: Dict[str, Any] = dict(orig_schema.copy())
        schema["schema"] = schema_key_value

        # Transform properties to storage format
        # Separates 'type' from other properties (stored in 'extra')
        schema["properties"] = dict(
            map(
                lambda item: (
                    item[0],
                    {
                        "type": item[1]["type"],
                        "extra": {k: str(v) for k, v in item[1].items() if k != "type"},
                    },
                ),
                schema["properties"].items(),
            )
        )

        return await database_client.mongo_insert_one_schema_async(
            dtypes.MongoInsertOneSchemaRequest(
                import_name=import_name,
                created_at=utc_now_iso(),
                active_schema=schema,  # type: ignore[arg-type]
                schemas_releases=[],
            )
        )

    @staticmethod
    async def remove_schema(
        import_name: str,
        database_client: DatabaseClient,
    ) -> dtypes.MongoDeleteOneJsonSchemaResponse:
        """
        Remove or revert a schema based on its import name.

        This function delegates to the database service which handles schema removal
        by either deleting the entire schema document if no releases exist, or
        reverting to the previous schema release.

        Args:
            import_name (str): The unique identifier for the schema to be removed.
            database_client (DatabaseClient): The database client to use for the operation.

        Returns:
            dtypes.MongoDeleteOneJsonSchemaResponse: Response containing:
                - success (bool): Whether the operation succeeded
                - status ('deleted', 'reverted', or 'error')
                - message (str): Description of the result
                - extra (dict): Additional metadata
        """
        return await database_client.mongo_delete_one_jsonschema_async(
            dtypes.MongoDeleteOneJsonSchemaRequest(import_name=import_name)
        )

    @staticmethod
    def map_db_response_to_api(
        db_response: (
            dtypes.MongoInsertOneSchemaResponse
            | dtypes.MongoDeleteOneJsonSchemaResponse
            | dtypes.MongoFindJsonSchemaResponse
        ),
        operation: Literal["save", "remove", "get"],
        import_name: str,
    ) -> dtypes.ApiResponse:
        """
        Map database responses to standardized API responses.

        Converts database-specific response structures into the ApiResponse format
        used by the API endpoints, including appropriate HTTP status codes and messages.

        Args:
            db_response: The database response object (Insert/Delete/Find response).
            operation: The operation type ('save', 'remove', or 'get').
            import_name: The schema import name for context in messages.

        Returns:
            dtypes.ApiResponse: Standardized API response with status, code, message, and data.
        """
        # Handle save operation responses
        if operation == "save":
            status_map = {
                "inserted": (200, "success", "Schema created successfully"),
                "updated": (200, "success", "Schema updated successfully"),
                "no_change": (200, "success", "Schema unchanged - no update needed"),
                "error": (500, "error", "Failed to save schema"),
            }

            code, status, message = status_map.get(
                db_response["status"], (500, "error", "Unknown status")
            )

            return dtypes.ApiResponse(
                status=status,
                code=code,
                message=message,
                data={
                    "import_name": import_name,
                    "operation": db_response["status"],
                    "result": str(db_response.get("result", {})),
                },
            )

        # Handle remove operation responses
        elif operation == "remove":
            # Type narrowing: we know this is a delete response for remove operation
            delete_response: dtypes.MongoDeleteOneJsonSchemaResponse = db_response  # type: ignore[assignment]

            if delete_response["success"]:
                status_map = {
                    "deleted": (200, "success", "Schema deleted successfully"),
                    "reverted": (
                        200,
                        "success",
                        "Schema reverted to previous version",
                    ),
                }
                code, status, message = status_map.get(
                    delete_response["status"], (200, "success", "Schema removed")
                )
            else:
                if "not found" in delete_response.get("message", "").lower():
                    code, status, message = (
                        404,
                        "error",
                        f"Schema '{import_name}' not found",
                    )
                else:
                    code, status, message = (500, "error", "Failed to remove schema")

            return dtypes.ApiResponse(
                status=status,
                code=code,
                message=message,
                data={
                    "import_name": import_name,
                    "operation": delete_response["status"],
                    "details": delete_response.get("message", ""),
                },
            )

        # Handle get operation responses
        elif operation == "get":
            if db_response["status"] == "found":
                return dtypes.ApiResponse(
                    status="success",
                    code=200,
                    message=f"Schema '{import_name}' retrieved successfully",
                    data={
                        "import_name": import_name,
                        "schema": str(db_response["schema"]),
                    },
                )
            elif db_response["status"] == "not_found":
                return dtypes.ApiResponse(
                    status="error",
                    code=404,
                    message=f"Schema '{import_name}' not found",
                    data={"import_name": import_name},
                )
            else:  # error
                return dtypes.ApiResponse(
                    status="error",
                    code=500,
                    message="Failed to retrieve schema",
                    data={
                        "import_name": import_name,
                        "error": str(db_response.get("extra", {})),
                    },
                )

        # Unknown operation
        return dtypes.ApiResponse(
            status="error",
            code=500,
            message="Unknown operation",
            data={"operation": operation},
        )
