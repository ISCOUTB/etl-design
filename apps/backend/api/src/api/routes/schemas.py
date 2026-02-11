"""Schema Routes Module.

This module provides RESTful API endpoints for schema management operations.
Schemas are JSON Schema documents used for data validation and structure definition.

All operations are synchronous and interact directly with the database service
via gRPC, providing immediate responses without message queue overhead.
"""

# TODO: This can be improved by adding more detailed error handling, logging, better response
# schemas, and a bunch of things, but I'll keep it simple for now to focus on core functionality

from typing import Any, Dict

from fastapi import APIRouter, HTTPException
from jsonschema import Draft7Validator, SchemaError
from proto_utils.database import dtypes

from src.api.deps import DatabaseClientDep
from src.services.schemas import SchemaService

router = APIRouter()


@router.post("/{import_name}")
async def create_or_update_schema(
    database_client: DatabaseClientDep,
    import_name: str,
    schema: Dict[str, Any],
) -> dtypes.ApiResponse:
    """
    Create or update a schema.

    This endpoint creates a new schema or updates an existing one for the specified
    import name. The schema is validated and saved directly to the database.

    Args:
        database_client: Database client dependency for MongoDB operations.
        import_name: Unique identifier for the schema.
        schema: JSON schema definition (as a dictionary).
        raw: If True, treats schema as raw JSON Schema (validates with Draft7).
             If False, creates a simple object schema from the provided properties.

    Returns:
        ApiResponse with:
        - 200: Schema created/updated successfully
        - 400: Invalid schema format
        - 500: Database operation failed

    Raises:
        HTTPException: If import_name is empty or schema validation fails.
    """
    if not import_name:
        raise HTTPException(400, "import_name must be provided.")

    if not schema:
        raise HTTPException(400, "schema data must be provided.")

    try:
        # Create and validate the schema
        Draft7Validator.check_schema(schema)  # This will raise SchemaError if invalid

        # Save to database
        db_response = SchemaService.save_schema(
            schema=schema,
            import_name=import_name,
            database_client=database_client,
        )

        # Map database response to API response
        response = SchemaService.map_db_response_to_api(
            db_response=db_response,
            operation="save",
            import_name=import_name,
        )

        return response

    except SchemaError as e:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid JSON schema: {str(e)}",
        )
    except Exception as e:
        return dtypes.ApiResponse(
            status="error",
            code=500,
            message=f"Failed to save schema: {str(e)}",
            data={"import_name": import_name},
        )


@router.get("/{import_name}")
async def get_schema(
    database_client: DatabaseClientDep,
    import_name: str,
) -> dtypes.ApiResponse:
    """
    Retrieve the active schema for a given import name.

    This endpoint fetches the currently active JSON schema associated with
    the specified import name from the database.

    Args:
        database_client: Database client dependency for MongoDB operations.
        import_name: Unique identifier for the schema to retrieve.

    Returns:
        ApiResponse with:
        - 200: Schema found and returned in data.schema
        - 404: Schema not found
        - 500: Database operation failed

    Raises:
        HTTPException: If import_name is empty.
    """
    if not import_name:
        raise HTTPException(400, "import_name must be provided.")

    try:
        # Retrieve schema from database
        db_response = database_client.mongo_find_jsonschema(
            dtypes.MongoFindJsonSchemaRequest(import_name=import_name)
        )

        # Map database response to API response
        response = SchemaService.map_db_response_to_api(
            db_response=db_response,
            operation="get",
            import_name=import_name,
        )

        # Raise HTTPException for 404 to match FastAPI conventions
        if response["code"] == 404:
            raise HTTPException(
                status_code=404,
                detail=f"Schema '{import_name}' not found",
            )

        return response
    except HTTPException:
        raise
    except Exception as e:
        return dtypes.ApiResponse(
            status="error",
            code=500,
            message=f"Failed to retrieve schema: {str(e)}",
            data={"import_name": import_name},
        )


@router.delete("/{import_name}")
async def delete_schema(
    import_name: str,
    database_client: DatabaseClientDep,
) -> dtypes.ApiResponse:
    """
    Delete or revert a schema.

    This endpoint removes a schema from the system. If the schema has release
    history, it reverts to the previous version. If no releases exist, the
    schema is completely deleted.

    Args:
        database_client: Database client dependency for MongoDB operations.
        import_name: Unique identifier for the schema to remove.

    Returns:
        ApiResponse with:
        - 200: Schema deleted or reverted successfully
        - 404: Schema not found
        - 500: Database operation failed

    Raises:
        HTTPException: If import_name is empty or schema not found.
    """
    if not import_name:
        raise HTTPException(400, "import_name must be provided.")

    try:
        # Remove schema from database
        db_response = SchemaService.remove_schema(
            import_name=import_name,
            database_client=database_client,
        )

        # Map database response to API response
        response = SchemaService.map_db_response_to_api(
            db_response=db_response,
            operation="remove",
            import_name=import_name,
        )

        # Raise HTTPException for 404 to match FastAPI conventions
        if response["code"] == 404:
            raise HTTPException(
                status_code=404,
                detail=f"Schema '{import_name}' not found",
            )

        return response
    except HTTPException:
        raise
    except Exception as e:
        return dtypes.ApiResponse(
            status="error",
            code=500,
            message=f"Failed to remove schema: {str(e)}",
            data={"import_name": import_name},
        )
