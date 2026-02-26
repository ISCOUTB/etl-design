# Idempotency is now handled by IdempotencyService which ensures atomicity
# across database, Redis cache, and RabbitMQ operations.
# All upload operations (validate, insert, process) use idempotency keys
# to prevent duplicate requests within a configurable time window.

from typing import Annotated

import httpx
import psycopg2
from fastapi import APIRouter, Form, HTTPException, UploadFile
from proto_utils.database import dtypes

from src.api.deps import (
    CurrentUser,
    DatabaseClientDep,
    IdempotencyServiceDep,
    ProjectServiceDep,
    PublisherDep,
)
from src.core.config import settings
from src.exceptions import ForbiddenException
from src.models import Project
from src.services.permissions import Action, ModelKeys, PermissionService

router = APIRouter()

HTTPX_CLIENT = httpx.AsyncClient(timeout=settings.EXCEL_READER_TIMEOUT_SECONDS)


@router.post("/validate")
async def validate(
    current_user: CurrentUser,
    publisher: PublisherDep,
    database_client: DatabaseClientDep,
    idempotency_service: IdempotencyServiceDep,
    spreadsheet_file: Annotated[UploadFile, Form()],
    project_id: Annotated[str, Form()],
    table_name: Annotated[str, Form()],
) -> dtypes.ApiResponse:
    """
    Upload a spreadsheet file in order to be validated.
    """
    has_permission = PermissionService.has_permission(
        user=current_user,
        action=Action.validate,
        model_key=ModelKeys.upload,
        model=Project(id=project_id),
    )
    if not has_permission:
        raise ForbiddenException()

    try:
        response = await idempotency_service.validate_task(
            db_client=database_client,
            publisher=publisher,
            spreadsheet_file=spreadsheet_file,
            user_id=current_user.id,
            project_id=project_id,
            table_name=table_name,
        )
        return response
    except Exception:
        # Exception handlers will manage this
        raise


@router.post("/insert")
async def insert(
    current_user: CurrentUser,
    publisher: PublisherDep,
    database_client: DatabaseClientDep,
    project_service: ProjectServiceDep,
    idempotency_service: IdempotencyServiceDep,
    spreadsheet_file: Annotated[UploadFile, Form()],
    project_id: Annotated[str, Form()],
    table_name: Annotated[str, Form()],
    overwrite: bool = False,
):
    """Insert data from a validated spreadsheet file into the database.
    this is not intented to be used always, just in specific cases, where all the
    pipeline (validation + insert) cannot be used.
    """
    has_permission = PermissionService.has_permission(
        user=current_user,
        action=Action.insert,
        model_key=ModelKeys.upload,
        model=Project(id=project_id),
    )
    if not has_permission:
        raise ForbiddenException()

    # Fetch db credentials of the project
    db_uri = project_service.get_project_db_uri(project_id)

    try:
        response = await idempotency_service.insert_task(
            db_client=database_client,
            publisher=publisher,
            spreadsheet_file=spreadsheet_file,
            user_id=current_user.id,
            project_id=project_id,
            table_name=table_name,
            db_uri=db_uri,
            overwrite=overwrite,
        )
        return response
    except Exception:
        # Exception handlers will manage this
        raise


@router.post("/process")
async def process(
    current_user: CurrentUser,
    publisher: PublisherDep,
    database_client: DatabaseClientDep,
    project_service: ProjectServiceDep,
    idempotency_service: IdempotencyServiceDep,
    spreadsheet_file: Annotated[UploadFile, Form()],
    project_id: Annotated[str, Form()],
    table_name: Annotated[str, Form()],
    overwrite: bool = False,
):
    """Validates and inserts data from a spreadsheet file into the database.
    Actually, it just publish the task to the mq, the worker will do the rest.
    """
    has_permission = PermissionService.has_permission(
        user=current_user,
        action=Action.process,
        model_key=ModelKeys.upload,
        model=Project(id=project_id),
    )
    if not has_permission:
        raise ForbiddenException()

    # Fetch db credentials of the project
    db_uri = project_service.get_project_db_uri(project_id)

    try:
        response = await idempotency_service.process_task(
            db_client=database_client,
            publisher=publisher,
            spreadsheet_file=spreadsheet_file,
            user_id=current_user.id,
            project_id=project_id,
            table_name=table_name,
            db_uri=db_uri,
            overwrite=overwrite,
        )
        return response
    except Exception:
        # Exception handlers will manage this
        raise


@router.post("/table")
async def create_table(
    current_user: CurrentUser,
    project_service: ProjectServiceDep,
    spreadsheet: UploadFile,
    project_id: Annotated[str, Form()],
    table_name: Annotated[str, Form()],
    dtypes: Annotated[str, Form()],
):
    has_permission = PermissionService.has_permission(
        user=current_user,
        action=Action.table,
        model_key=ModelKeys.upload,
        model=Project(id=project_id),
    )
    if not has_permission:
        raise ForbiddenException()

    # Example of `dtypes`:
    # {"Sheet1": {"name": {"type": "TEXT", "extra": "NOT NULL"},
    # "age": {"type": "INTEGER", "extra": "NOT NULL"}, "is_adult": {"type": "TEXT"}}}
    fill_spaces = "_"
    try:
        response = await HTTPX_CLIENT.post(
            f"{settings.EXCEL_READER_URL}/excel-parser",
            files={
                "spreadsheet": (
                    spreadsheet.filename,
                    await spreadsheet.read(),
                    spreadsheet.content_type,
                )
            },
            data={
                "table_name": table_name,
                "dtypes_str": dtypes,
            },
            params={"fill_spaces": fill_spaces, "limit": 5},
        )

        response.raise_for_status()
        sql_per_sheet = response.json()
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to communicate with Excel Reader service: {str(e)}",
        )

    try:
        with psycopg2.connect(project_service.get_project_db_uri(project_id)) as conn:
            cur = conn.cursor()
            for _, sql in sql_per_sheet.items():
                cur.execute(sql)
            conn.commit()
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create table in the database: {str(e)}",
        )

    return {"message": "Table created successfully", "sql_per_sheet": sql_per_sheet}
