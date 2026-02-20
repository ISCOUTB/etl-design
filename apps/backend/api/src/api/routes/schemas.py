"""Schema Routes Module.

This module provides RESTful API endpoints for schema management operations.
Schemas are JSON Schema documents used for data validation and structure definition.

All operations are synchronous and interact directly with the database service
via gRPC, providing immediate responses without message queue overhead.
"""

# TODO: This can be improved by adding more detailed error handling, logging, better response
# schemas, and a bunch of things, but I'll keep it simple for now to focus on core functionality

from typing import Any, Dict

from fastapi import APIRouter
from jsonschema import Draft7Validator, SchemaError
from proto_utils.database import dtypes

from src import models
from src.api.deps import CurrentUser, DatabaseClientDep
from src.exceptions import (
    ForbiddenException,
    InvalidJsonSchemaException,
    SchemaNotFoundException,
    SchemaNotProvidedException,
)
from src.services import Action, ModelKeys, PermissionService, SchemaService

router = APIRouter()


@router.post("/{project_id}")
async def create_or_update_schema(
    current_user: CurrentUser,
    database_client: DatabaseClientDep,
    project_id: str,
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
        AppException: If import_name is empty or schema validation fails.
    """
    has_permission = PermissionService.has_permission(
        user=current_user,
        action=Action.create,
        model_key=ModelKeys.schemas,
        model=models.Project(id=project_id),
    )
    if not has_permission:
        raise ForbiddenException()

    if not schema:
        raise SchemaNotProvidedException()

    try:
        # Create and validate the schema
        # This will raise SchemaError if invalid
        Draft7Validator.check_schema(schema)

        # Save to database
        db_response = SchemaService.save_schema(
            schema=schema,
            import_name=project_id,
            database_client=database_client,
        )

        # Map database response to API response
        response = SchemaService.map_db_response_to_api(
            db_response=db_response,
            operation="save",
            import_name=project_id,
        )

        return response

    except SchemaError:
        raise InvalidJsonSchemaException()
    except Exception as e:
        return dtypes.ApiResponse(
            status="error",
            code=500,
            message=f"Failed to save schema: {str(e)}",
            data={"import_name": project_id},
        )


@router.get("/{project_id}", response_model=dtypes.ApiResponse)
async def get_schema(
    current_user: CurrentUser,
    database_client: DatabaseClientDep,
    project_id: str,
) -> dtypes.ApiResponse:
    """
    Retrieve the active schema for a given import name.

    This endpoint fetches the currently active JSON schema associated with
    the specified import name from the database.

    Args:
        database_client: Database client dependency for MongoDB operations.
        project_id: Unique identifier for the schema to retrieve.

    Returns:
        ApiResponse with:
        - 200: Schema found and returned in data.schema
        - 404: Schema not found
        - 500: Database operation failed

    Raises:
        AppException: If project_id is empty.
    """
    has_permission = PermissionService.has_permission(
        user=current_user,
        action=Action.view,
        model_key=ModelKeys.schemas,
        model=models.UserProject(user_id=current_user.id, project_id=project_id),
    )
    if not has_permission:
        raise ForbiddenException()

    try:
        # Retrieve schema from database
        db_response = database_client.mongo_find_jsonschema(
            dtypes.MongoFindJsonSchemaRequest(import_name=project_id)
        )

        # Map database response to API response
        response = SchemaService.map_db_response_to_api(
            db_response=db_response,
            operation="get",
            import_name=project_id,
        )
    except Exception as e:
        return dtypes.ApiResponse(
            status="error",
            code=500,
            message=f"Failed to retrieve schema: {str(e)}",
            data={"import_name": project_id},
        )

    # Raise AppException for 404 to match FastAPI conventions
    if response["code"] == 404:
        raise SchemaNotFoundException()

    return response


@router.delete("/{project_id}")
async def delete_schema(
    project_id: str,
    current_user: CurrentUser,
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
        AppException: If import_name is empty or schema not found.
    """
    has_permission = PermissionService.has_permission(
        user=current_user,
        action=Action.delete,
        model_key=ModelKeys.schemas,
        model=models.UserProject(user_id=current_user.id, project_id=project_id),
    )
    if not has_permission:
        raise ForbiddenException()

    try:
        # Remove schema from database
        db_response = SchemaService.remove_schema(
            import_name=project_id,
            database_client=database_client,
        )

        # Map database response to API response
        response = SchemaService.map_db_response_to_api(
            db_response=db_response,
            operation="remove",
            import_name=project_id,
        )
    except Exception as e:
        return dtypes.ApiResponse(
            status="error",
            code=500,
            message=f"Failed to remove schema: {str(e)}",
            data={"import_name": project_id},
        )

    # Raise AppException for 404 to match FastAPI conventions
    if response["code"] == 404:
        raise SchemaNotFoundException()

    return response
