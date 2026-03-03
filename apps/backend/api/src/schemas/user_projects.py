from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from src.models import Status, UserProjectType


class BaseUserProjectSchema(BaseModel):
    """Schema for user-project association."""

    user_id: str
    project_id: str
    role: UserProjectType


class CreateUserProjectSchema(BaseUserProjectSchema):
    """Schema for creating a user-project association."""

    pass


class InviteUserProjectSchema(BaseModel):
    """Schema for inviting a user to a project."""

    email: str
    role: UserProjectType


class AddUserProjectSchema(BaseModel):
    """Schema for adding an existing user to a project."""

    user_id: str
    role: UserProjectType


class UpdateUserProjectSchema(BaseModel):
    """Schema for updating user-project association."""

    role: Optional[UserProjectType] = None
    status: Optional[Status] = None


class ResponseUserProjectSchema(BaseUserProjectSchema):
    """Schema for project data in API responses."""

    status: Status
    created_at: datetime
    updated_at: datetime
