"""Schema Routes Module.

This module provides RESTful API endpoints for schema management operations.
Schemas are JSON Schema documents used for data validation and structure definition.

All operations are synchronous and interact directly with the database service
via gRPC, providing immediate responses without message queue overhead.
"""

# TODO: This can be improved by adding more detailed error handling, logging, better response
# schemas, and a bunch of things, but I'll keep it simple for now to focus on core functionality

from fastapi import APIRouter
from proto_utils.database import dtypes

from src import models, repositories, schemas
from src.api.deps import CurrentUser, DatabaseClientDep, ProjectServiceDep
from src.core.domain import get_import_name
from src.exceptions import (
    AppException,
    ForbiddenException,
    ProjectNotFoundException,
    SchemaNotFoundException,
    SchemaNotProvidedException,
)
from src.services import Action, ModelKeys, PermissionService, SchemaService

router = APIRouter()


@router.post("/{project_id}")
async def create_or_update_schema(
    current_user: CurrentUser,
    database_client: DatabaseClientDep,
    project_service: ProjectServiceDep,
    project_id: str,
    table_name: str,
    schema: schemas.JsonSchemaRequest,
) -> dtypes.ApiResponse:
    """
    Create or update a schema.

    This endpoint creates a new schema or updates an existing one for the specified
    import name. The schema is validated and saved directly to the database.

    Args:
        database_client: Database client dependency for MongoDB operations.
        import_name: Unique identifier for the schema.
        schema: JSON schema definition (as a dictionary).
        table_name: The name of the table associated with the schema
            (used for validation context).

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

    if not project_service.get_project_by_id(project_id=project_id):
        raise ProjectNotFoundException()

    import_name = get_import_name(project_id=project_id, table_name=table_name)
    try:
        # Save to database
        db_response = await SchemaService.save_schema(
            orig_schema=schema,
            import_name=import_name,
            database_client=database_client,
        )

        # Map database response to API response
        response = SchemaService.map_db_response_to_api(
            db_response=db_response,
            operation="save",
            import_name=import_name,
        )
        if response["code"] == 500:
            raise AppException(message=response["message"])

        return response
    except AppException:
        raise
    except Exception as e:
        raise AppException(message=f"Failed to save schema: {repr(e)}") from e


@router.get("/{project_id}/raw")
async def get_raw_schema(
    current_user: CurrentUser,
    database_client: DatabaseClientDep,
    project_service: ProjectServiceDep,
    project_id: str,
    table_name: str,
) -> schemas.MongoSchemasResponse:
    """
    Retrieve the raw schema document for a given import name.

    This endpoint fetches the raw JSON schema document associated with the specified
    import name from the database, without any additional processing or formatting.

    Args:
        database_client: Database client dependency for MongoDB operations.
        project_id: Unique identifier for the schema to retrieve.
        table_name: The name of the table associated with the schema
            (used to construct import_name).
    Returns:
        schemas.MongoSchemasResponse
    """
    has_permission = PermissionService.has_permission(
        user=current_user,
        action=Action.view,
        model_key=ModelKeys.schemas,
        model=models.UserProject(user_id=current_user.id, project_id=project_id),
    )
    if not has_permission:
        raise ForbiddenException()

    if not project_service.get_project_by_id(project_id=project_id):
        raise ProjectNotFoundException()

    import_name = get_import_name(project_id=project_id, table_name=table_name)
    try:
        # Retrieve raw schema from database
        raw_schema = await SchemaService.get_raw_schema(
            import_name=import_name,
            database_client=database_client,
        )
    except Exception as e:
        raise AppException() from e

    # Raise AppException for 404 to match FastAPI conventions
    if raw_schema is None:
        raise SchemaNotFoundException()

    return raw_schema


@router.get("/search/{project_id}")
async def search_schemas(
    current_user: CurrentUser,
    database_client: DatabaseClientDep,
    project_service: ProjectServiceDep,
    project_id: str,
) -> schemas.MongoGetSchemasByImportResponse:
    """
    Search for schemas matching the given criteria.

    This endpoint allows searching for schemas based on the provided project ID and
    table name. It returns a list of matching schemas with their details.

    Args:
        database_client: Database client dependency for MongoDB operations.
        project_id: Unique identifier for the project to search within.
        table_name: The name of the table to filter schemas by.
    Returns:
        schemas.MongoGetSchemasByImportResponse
    """
    has_permission = PermissionService.has_permission(
        user=current_user,
        action=Action.view,
        model_key=ModelKeys.schemas,
        model=models.UserProject(user_id=current_user.id, project_id=project_id),
    )
    if not has_permission:
        raise ForbiddenException()

    if not project_service.get_project_by_id(project_id=project_id):
        raise ProjectNotFoundException()

    try:
        # Search for schemas in the database
        search_results = await SchemaService.get_schemas_by_project_id(
            project_id=project_id,
            database_client=database_client,
        )
    except Exception as e:
        raise AppException() from e

    return search_results


@router.get("/{project_id}")
async def get_schema(
    current_user: CurrentUser,
    database_client: DatabaseClientDep,
    project_service: ProjectServiceDep,
    project_id: str,
    table_name: str,
) -> schemas.JsonSchemaRequest:
    """
    Retrieve the active schema for a given import name.

    This endpoint fetches the currently active JSON schema associated with
    the specified import name from the database.

    Args:
        database_client: Database client dependency for MongoDB operations.
        project_id: Unique identifier for the schema to retrieve.
        table_name: The name of the table associated with the schema
            (used to construct import_name).

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

    if not project_service.get_project_by_id(project_id=project_id):
        raise ProjectNotFoundException()

    import_name = get_import_name(project_id=project_id, table_name=table_name)
    try:
        # Retrieve schema from database
        active_schema = await SchemaService.get_active_schema(
            import_name=import_name,
            database_client=database_client,
        )
    except Exception as e:
        raise AppException(message=f"Failed to retrieve schema: {repr(e)}") from e

    # Raise AppException for 404 to match FastAPI conventions
    if active_schema is None:
        raise SchemaNotFoundException()

    return active_schema


@router.delete("/{project_id}")
async def delete_schema(
    project_id: str,
    current_user: CurrentUser,
    database_client: DatabaseClientDep,
    project_service: ProjectServiceDep,
    table_name: str,
) -> dtypes.ApiResponse:
    """
    Delete or revert a schema.

    This endpoint removes a schema from the system. If the schema has release
    history, it reverts to the previous version. If no releases exist, the
    schema is completely deleted.

    Args:
        database_client: Database client dependency for MongoDB operations.
        import_name: Unique identifier for the schema to remove.
        table_name (str): The name of the table associated with the schema
            (used to construct import_name).

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

    if not project_service.get_project_by_id(project_id=project_id):
        raise ProjectNotFoundException()

    import_name = get_import_name(project_id=project_id, table_name=table_name)
    try:
        # Remove schema from database
        db_response = await SchemaService.remove_schema(
            project_id=project_id,
            table_name=table_name,
            database_client=database_client,
            upload_repository=repositories.UploadRepository(
                db=project_service.repository.db
            ),
        )
    except Exception as e:
        raise AppException(message=f"Failed to remove schema: {repr(e)}") from e

    # Map database response to API response
    response = SchemaService.map_db_response_to_api(
        db_response=db_response,
        operation="remove",
        import_name=import_name,
    )

    # Raise AppException for 404 to match FastAPI conventions
    if response["code"] == 404:
        raise SchemaNotFoundException()

    # TODO: Remove Tasks related to the import_name

    return response
