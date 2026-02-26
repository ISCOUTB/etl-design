from datetime import datetime
from typing import Optional

from messaging_utils.schemas import Metadata
from pydantic import BaseModel

from src.models import TaskStatus


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
