# TODO: Ideally, the import_name must not be requested here,
# it, actually, is obtained from the user's table from the DB,
# but for simplicity, we are requesting it here.

from typing import Annotated, Literal

from fastapi import APIRouter, Form, HTTPException, UploadFile
from messaging_utils.core.config import settings as mq_settings
from proto_utils.database import dtypes

from src.api.deps import DatabaseClientDep, PublisherDep
from src.core.constants import VALIDATION_TASK

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

        # Metadata
        metadata = {
            "filename": spreadsheet_file.filename,
            "content_type": spreadsheet_file.content_type,
            "size": len(file_content),
        }

        # Publish in RabbitMQ
        # file_content = UploadFile(file_content)
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
    mode: Annotated[Literal["append", "replace"], Form()],
):
    """Insert data from a validated spreadsheet file into the database.
    this is not intented to be used always, just in specific cases, where all the 
    pipeline (validation + insert) cannot be used.
    """
    # TODO: implement the function for inserting the data
    pass


@router.post("/process")
async def process(
    publisher: PublisherDep,
    database_client: DatabaseClientDep,
    import_name: Annotated[str, Form()],
):
    """Validates and inserts data from a spreadsheet file into the database.
    Actually, it just publish the task to the mq, the worker will do the rest.
    """
    # TODO: implement the function for processing (validating + inserting) the data
    pass


@router.get("/status")
async def get_validation_status(
    database_client: DatabaseClientDep,
    task: str,
    task_id: str = "",
    import_name: str = "",
) -> dtypes.ApiResponse | list[dtypes.ApiResponse]:
    """
    Get the status of the file being validated.
    """
    if not task_id and not import_name:
        raise HTTPException(400, "Either `task_id` or `import_name` must be provided.")

    if import_name:
        cached_response = database_client.get_tasks_by_import_name(
            dtypes.GetTasksByImportNameRequest(import_name=import_name, task=task)
        )
        return cached_response["tasks"]

    cached_response = database_client.get_task_id(
        dtypes.GetTaskIdRequest(task_id=task_id, task=task)
    )
    if not cached_response["found"]:
        HTTPException(404, f"Task with ID {task_id} not found.")

    return cached_response["value"]
