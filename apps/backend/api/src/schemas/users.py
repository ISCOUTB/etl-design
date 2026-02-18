import re
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, field_validator

from src.exceptions import EmailFormatException, InvalidUserDataException
from src.models.dtypes import UserRole, UserStatus


class BaseUserSchema(BaseModel):
    """Base schema for user data."""

    name: str
    email: str
    role: UserRole


class CreateUserSchema(BaseUserSchema):
    """Schema for creating a new user."""

    password: str

    @field_validator("email")
    def validate_email(cls, value):
        """Validate email format."""
        if bool(re.match(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$", value)):
            raise EmailFormatException("Invalid email format")
        return value

    @field_validator("password")
    def validate_password(cls, value):
        n_chars = len(value.strip())
        if n_chars < 8 or n_chars > 50:
            raise InvalidUserDataException(
                "Password must be between 8 and 50 characters"
            )
        return value

    @field_validator("name")
    def validate_name(cls, value):
        n_chars = len(value.strip())
        if n_chars == 0:
            raise InvalidUserDataException("Name cannot be empty")
        return value


class UpdateUserSchema(BaseModel):
    """Schema for updating user information."""

    name: Optional[str] = None
    email: Optional[str] = None
    role: Optional[UserRole] = None
    status: Optional[UserStatus] = None

    @field_validator("email")
    def validate_email(cls, value):
        """Validate email format."""
        if value is not None and bool(
            re.match(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$", value)
        ):
            raise EmailFormatException("Invalid email format")
        return value

    @field_validator("name")
    def validate_name(cls, value):
        """Validate that name is not empty if provided."""
        if value is not None and len(value.strip()) == 0:
            raise InvalidUserDataException("Name cannot be empty")
        return value


class ResponseUserSchema(BaseUserSchema):
    """Schema for user data in API responses."""

    id: str
    status: UserStatus
    created_at: datetime
    updated_at: datetime
