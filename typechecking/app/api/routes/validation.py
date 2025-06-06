from fastapi import APIRouter, UploadFile
from app.messaging.publishers import ValidationPublisher
from app.schemas.api import ApiResponse

router = APIRouter()
publisher = ValidationPublisher()


@router.post("/validate")
async def validate(spreadsheet_file: UploadFile, import_name: str) -> ApiResponse:
    """
    Endpoint asíncrono para validación usando RabbitMQ
    """
    try:
        # Leer archivo
        file_content = await spreadsheet_file.read()

        # Metadatos
        metadata = {
            "filename": spreadsheet_file.filename,
            "content_type": spreadsheet_file.content_type,
            "size": len(file_content),
        }

        # Publish in RabbitMQ
        task_id = publisher.publish_validation_request(
            file_data=file_content, import_name=import_name, metadata=metadata
        )

        return ApiResponse(
            status="accepted",
            code=202,
            message="Validation request submitted successfully",
            data={"task_id": task_id},
        )

    except Exception as e:
        return ApiResponse(
            status="error",
            code=500,
            message=f"Failed to submit validation request: {str(e)}",
        )
