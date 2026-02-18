from datetime import datetime

from pydantic import BaseModel

from src.models import UserProjectType


class BaseUserProjectSchema(BaseModel):
    """Schema for user-project association."""

    user_id: str
    project_id: str
    role: UserProjectType


class CreateUserProjectSchema(BaseUserProjectSchema):
    """Schema for creating a user-project association."""

    pass


class UpdateUserProjectSchema(BaseModel):
    """Schema for updating user-project association."""

    role: UserProjectType | None = None


class ResponseUserProjectSchema(BaseUserProjectSchema):
    """Schema for project data in API responses."""

    created_at: datetime
    updated_at: datetime
