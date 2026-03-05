from datetime import datetime
from typing import Any, Dict, List, Optional

from messaging_utils.schemas import Metadata
from pydantic import BaseModel, Field

from src.models import TaskStatus


class CreateTableFromJsonSchemaRequest(BaseModel):
    """Request model for creating a table from a JSON Schema."""

    table_name: str
    project_id: str
    jsonschema: Dict[str, Any]
    primary_keys: List[str] = Field(default_factory=list)


class UploadTaskBaseSchema(BaseModel):
    task_id: str
    idempotency_key: str
    status: TaskStatus
    user_id: str
    project_id: str
    file_hash: Optional[str] = None
    task_metadata: Optional[Metadata] = None


class UploadTaskCreateSchema(UploadTaskBaseSchema):
    pass


class UploadTaskUpdateSchema(BaseModel):
    status: TaskStatus


class UploadTaskResponseSchema(UploadTaskBaseSchema):
    created_at: datetime
    updated_at: datetime
