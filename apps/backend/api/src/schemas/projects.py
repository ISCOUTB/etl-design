from datetime import datetime

from pydantic import BaseModel, field_validator, model_validator

from src.exceptions import InvalidUserDataException


class BaseProjectSchema(BaseModel):
    """Base schema for project data."""

    name: str
    description: str | None = None
    provider: str | None = None
    db_host: str | None = None
    db_port: int | None = None
    db_user: str | None = None
    db_password: str | None = None
    db_name: str | None = None
    db_params: str | None = None


class CreateProjectSchema(BaseProjectSchema):
    """Schema for creating a new project."""

    @field_validator("name")
    def validate_name(cls, value):
        if len(value.strip()) == 0:
            raise InvalidUserDataException("Project name cannot be empty")
        return value


class UpdateProjectSchema(BaseModel):
    """Schema for updating project information."""

    name: str | None = None
    description: str | None = None
    provider: str | None = None
    db_host: str | None = None
    db_port: int | None = None
    db_user: str | None = None
    db_password: str | None = None
    db_name: str | None = None
    db_params: str | None = None

    @field_validator("name")
    def validate_name(cls, value):
        if value is not None and len(value.strip()) == 0:
            raise InvalidUserDataException("Project name cannot be empty")
        return value


class ResponseProjectSchema(BaseProjectSchema):
    """Schema for project data in API responses."""

    id: str
    created_at: datetime
    updated_at: datetime
