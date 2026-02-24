"""Schema Handlers Module.

This module provides handler functions for schema operations that interact
directly with the database service. These functions are used by the API
endpoints to perform synchronous schema operations without requiring RabbitMQ.

The handlers manage JSON schema validation, creation, storage, and retrieval
using the DatabaseClient to communicate with the MongoDB service via gRPC.
"""

from typing import Any, Dict, Literal

from proto_utils.database import dtypes
from proto_utils.database.base_client import DatabaseClient

from src.utils import utc_now_iso


class SchemaService:
    @staticmethod
    def get_active_schema(
        import_name: str, database_client: DatabaseClient
    ) -> dtypes.JsonSchema | None:
        """
        Get the active schema for a given import name.

        Args:
            import_name (str): The name of the import.
            database_client (DatabaseClient): The database client to use for fetching the schema.

        Returns:
            dtypes.JsonSchema | None: The active schema if found, None otherwise.
        """
        schema_doc = database_client.mongo_find_jsonschema(
            dtypes.MongoFindJsonSchemaRequest(import_name=import_name)
        )

        return schema_doc["schema"] if schema_doc["status"] == "found" else None

    @staticmethod
    def save_schema(
        schema: Dict[str, Any], import_name: str, database_client: DatabaseClient
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
        # Extract and normalize the $schema field
        schema_key_value = schema.pop(
            "$schema", "http://json-schema.org/draft-07/schema#"
        )
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

        return database_client.mongo_insert_one_schema(
            dtypes.MongoInsertOneSchemaRequest(
                import_name=import_name,
                created_at=utc_now_iso(),
                active_schema=schema,  # type: ignore[arg-type]
                schemas_releases=[],
            )
        )

    # TODO: This is deleting all schema versions even if there are releases,
    # we should only delete the active one and keep the history
    # Change this
    @staticmethod
    def remove_schema(
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
        return database_client.mongo_delete_one_jsonschema(
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
