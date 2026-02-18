from src.exceptions.auth import (
    ForbiddenException,
    InvalidCredentialsException,
    TokenExpiredException,
    UnauthenticatedException,
)
from src.exceptions.base import AppException
from src.exceptions.projects import (
    DatabaseConnectionException,
    InvalidProjectDataException,
    ProjectAlreadyExistsException,
    ProjectNotFoundException,
)
from src.exceptions.users import (
    EmailFormatException,
    InvalidUserDataException,
    UserAlreadyExistsException,
    UserInactiveException,
    UserNotFoundException,
)

__all__ = [
    # Auth exceptions
    "ForbiddenException",
    "UnauthenticatedException",
    "InvalidCredentialsException",
    "TokenExpiredException",
    # User exceptions
    "UserNotFoundException",
    "UserAlreadyExistsException",
    "InvalidUserDataException",
    "EmailFormatException",
    "UserInactiveException",
    # Project exceptions
    "ProjectNotFoundException",
    "ProjectAlreadyExistsException",
    "InvalidProjectDataException",
    "DatabaseConnectionException",
    # Base exception
    "AppException",
]
