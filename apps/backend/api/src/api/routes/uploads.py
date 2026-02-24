# TODO: Find a way to make all these function atomic
# in case the database or rabbit is down, we don't want to end up in a state
# where the task is published but not saved in the database, or vice versa.
# For that, we could use idempotency keys, or we could use a two-phase commit protocol,
# but that might be an overkill for now.

from typing import Annotated, List

import httpx
import psycopg2
from fastapi import APIRouter, Form, HTTPException, UploadFile
from messaging_utils.core.config import settings as mq_settings
from messaging_utils.schemas import Metadata
from proto_utils.database import dtypes

from src.api.deps import CurrentUser, DatabaseClientDep, ProjectServiceDep, PublisherDep
from src.core.config import settings
from src.core.constants import INSERTION_TASK, VALIDATION_TASK
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
    spreadsheet_file: Annotated[UploadFile, Form()],
    project_id: Annotated[str, Form()],
    table_name: Annotated[str, Form()],
    force_new: bool = False,
) -> List[dtypes.ApiResponse]:
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

    if not force_new and (
        cached_response := database_client.get_tasks_by_import_name(
            dtypes.GetTasksByImportNameRequest(
                import_name=project_id, task=VALIDATION_TASK
            )
        )
    ):
        return cached_response["tasks"]

    try:
        # Read the file content
        file_content = await spreadsheet_file.read()

        assert file_content, "File content is empty."
        assert spreadsheet_file.filename, "Filename is missing."
        assert spreadsheet_file.content_type, "Content type is missing."

        # Metadata
        metadata = Metadata(
            filename=spreadsheet_file.filename,
            content_type=spreadsheet_file.content_type,
            size=len(file_content),
        )

        # Publish in RabbitMQ
        task_id = publisher.publish_validation_request(
            routing_key=mq_settings.RABBITMQ_PUBLISHERS_ROUTING_KEY_VALIDATIONS,
            file_data=file_content,
            project_id=project_id,
            table_name=table_name,
            metadata=metadata,
            task="sample_validation",
        )

        response = dtypes.ApiResponse(
            status="accepted",
            code=202,
            message="Validation request submitted successfully",
            data={"task_id": task_id, "project_id": project_id},
        )

    except Exception as e:
        response = dtypes.ApiResponse(
            status="error",
            code=500,
            message=f"Failed to submit validation request: {str(e)}",
            data={},
        )
        return [response]

    database_client.set_task_id(
        dtypes.SetTaskIdRequest(
            task_id=task_id,
            value=response,
            task=VALIDATION_TASK,
        )
    )
    return [response]


@router.post("/insert")
async def insert(
    current_user: CurrentUser,
    publisher: PublisherDep,
    database_client: DatabaseClientDep,
    project_service: ProjectServiceDep,
    spreadsheet_file: UploadFile,
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

    # Read the file content
    file_content = await spreadsheet_file.read()

    assert file_content, "File content is empty."
    assert spreadsheet_file.filename, "Filename is missing."
    assert spreadsheet_file.content_type, "Content type is missing."

    # Create Metadata object obtained from the uploaded file
    metadata = Metadata(
        filename=spreadsheet_file.filename,
        content_type=spreadsheet_file.content_type,
        size=len(file_content),
    )

    # Fetch db credentials of the project
    db_uri = project_service.get_project_db_uri(project_id)
    try:
        # Publish in RabbitMQ
        task_id = publisher.publish_insertion_request(
            routing_key=mq_settings.RABBITMQ_PUBLISHERS_ROUTING_KEY_INSERTION,
            file_data=file_content,
            project_id=project_id,
            table_name=table_name,
            metadata=metadata,
            task="sample_insertion",
            overwrite=overwrite,
            db_uri=db_uri,
        )

        response = dtypes.ApiResponse(
            status="accepted",
            code=202,
            message="Validation request submitted successfully",
            data={"task_id": task_id, "project_id": project_id},
        )

    except Exception as e:
        response = dtypes.ApiResponse(
            status="error",
            code=500,
            message=f"Failed to submit validation request: {str(e)}",
            data={},
        )
        return response

    database_client.set_task_id(
        dtypes.SetTaskIdRequest(
            task_id=task_id,
            value=response,
            task=INSERTION_TASK,
        )
    )
    return response


@router.post("/process")
async def process(
    current_user: CurrentUser,
    publisher: PublisherDep,
    database_client: DatabaseClientDep,
    project_service: ProjectServiceDep,
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

    # Read the file content
    file_content = await spreadsheet_file.read()

    assert file_content, "File content is empty."
    assert spreadsheet_file.filename, "Filename is missing."
    assert spreadsheet_file.content_type, "Content type is missing."

    # Create Metadata object obtained from the uploaded file
    metadata = Metadata(
        filename=spreadsheet_file.filename,
        content_type=spreadsheet_file.content_type,
        size=len(file_content),
    )

    # Fetch db credentials of the project
    db_uri = project_service.get_project_db_uri(project_id)

    # Publish in RabbitMQ
    try:
        task_id = publisher.publish_validation_request(
            routing_key=mq_settings.RABBITMQ_PUBLISHERS_ROUTING_KEY_VALIDATIONS,
            file_data=file_content,
            project_id=project_id,
            table_name=table_name,
            metadata=metadata,
            task="sample_validation",
            insert=True,
            insert_overwrite=overwrite,
            insert_db_uri=db_uri,
        )

        response = dtypes.ApiResponse(
            status="accepted",
            code=202,
            message="Validation request submitted successfully",
            data={"task_id": task_id, "project_id": project_id},
        )

    except Exception as e:
        response = dtypes.ApiResponse(
            status="error",
            code=500,
            message=f"Failed to submit validation request: {str(e)}",
            data={},
        )
        return response

    database_client.set_task_id(
        dtypes.SetTaskIdRequest(
            task_id=task_id,
            value=response,
            task=VALIDATION_TASK,
        )
    )
    return response


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
