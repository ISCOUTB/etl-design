# TODO: Ideally, the import_name must not be requested here,
# it, actually, is obtained from the user's table from the DB,
# but for simplicity, we are requesting it here.

# TODO: Ensure idempotency of the endpoints, especially the /validate endpoint,
# since it can be called multiple times with the same file.

from typing import Annotated

import httpx
from fastapi import APIRouter, Form, HTTPException, UploadFile
from messaging_utils.core.config import settings as mq_settings
from messaging_utils.schemas import Metadata
from proto_utils.database import dtypes

from src.api.deps import DatabaseClientDep, PublisherDep
from src.core.config import settings
from src.core.constants import INSERTION_TASK, VALIDATION_TASK

router = APIRouter()


# TODO: Fix return-type xddd
@router.post("/validate")
async def validate(
    publisher: PublisherDep,
    database_client: DatabaseClientDep,
    spreadsheet_file: Annotated[UploadFile, Form()],
    import_name: Annotated[str, Form()],
    new: bool = False,
) -> dtypes.ApiResponse | list[dtypes.ApiResponse]:
    """
    Upload a spreadsheet file in order to be validated.
    """
    if not import_name:
        raise HTTPException(400, "import_name must be provided.")

    if not new and (
        cached_response := database_client.get_tasks_by_import_name(
            dtypes.GetTasksByImportNameRequest(
                import_name=import_name, task=VALIDATION_TASK
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
            import_name=import_name,
            metadata=metadata,
            task="sample_validation",
        )

        response = dtypes.ApiResponse(
            status="accepted",
            code=202,
            message="Validation request submitted successfully",
            data={"task_id": task_id, "import_name": import_name},
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


@router.post("/insert")
async def insert(
    publisher: PublisherDep,
    database_client: DatabaseClientDep,
    spreadsheet_file: UploadFile,
    import_name: Annotated[str, Form()],
    overwrite: bool = False,
):
    """Insert data from a validated spreadsheet file into the database.
    this is not intented to be used always, just in specific cases, where all the
    pipeline (validation + insert) cannot be used.
    """
    if not import_name:
        raise HTTPException(400, "import_name must be provided.")

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
        task_id = publisher.publish_insertion_request(
            routing_key=mq_settings.RABBITMQ_PUBLISHERS_ROUTING_KEY_INSERTION,
            file_data=file_content,
            import_name=import_name,
            metadata=metadata,
            task="sample_insertion",
            overwrite=overwrite,
        )

        response = dtypes.ApiResponse(
            status="accepted",
            code=202,
            message="Validation request submitted successfully",
            data={"task_id": task_id, "import_name": import_name},
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
    publisher: PublisherDep,
    database_client: DatabaseClientDep,
    spreadsheet_file: Annotated[UploadFile, Form()],
    import_name: Annotated[str, Form()],
    overwrite: bool = False,
):
    """Validates and inserts data from a spreadsheet file into the database.
    Actually, it just publish the task to the mq, the worker will do the rest.
    """
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
            import_name=import_name,
            metadata=metadata,
            task="sample_validation",
            insert=True,
            insert_overwrite=overwrite,
        )

        response = dtypes.ApiResponse(
            status="accepted",
            code=202,
            message="Validation request submitted successfully",
            data={"task_id": task_id, "import_name": import_name},
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
    spreadsheet: UploadFile,
    import_name: Annotated[str, Form()],
    dtypes: Annotated[str, Form()],
):
    # Example of `dtypes`:
    # {"Sheet1": {"name": {"type": "TEXT", "extra": "NOT NULL"},
    # "age": {"type": "INTEGER", "extra": "NOT NULL"}, "is_adult": {"type": "TEXT"}}}
    fill_spaces = "_"

    try:
        async with httpx.AsyncClient(
            timeout=settings.EXCEL_READER_TIMEOUT_SECONDS
        ) as client:
            response = await client.post(
                f"{settings.EXCEL_READER_URL}/excel-parser",
                files={
                    "spreadsheet": (
                        spreadsheet.filename,
                        await spreadsheet.read(),
                        spreadsheet.content_type,
                    )
                },
                data={"import_name": import_name, "dtypes_str": dtypes},
                params={"fill_spaces": fill_spaces, "limit": 5},
            )

        response.raise_for_status()
        return response.json()

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to communicate with Excel Reader service: {str(e)}",
        )
