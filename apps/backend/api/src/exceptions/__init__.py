from src.exceptions.auth import (
    ForbiddenException,
    IncorrectModel,
    InvalidCredentialsException,
    TokenExpiredException,
    UnauthenticatedException,
)
from src.exceptions.base import AppException
from src.exceptions.projects import (
    DatabaseConnectionException,
    InvalidProjectDataException,
    ProjectAlreadyExistsException,
    ProjectHasActiveUsersException,
    ProjectNotFoundException,
)
from src.exceptions.user_project import UserProjectNotFoundException
from src.exceptions.users import (
    EmailFormatException,
    EmailInUseException,
    InvalidUserDataException,
    UserAlreadyExistsException,
    UserHasActiveProjectsException,
    UserInactiveException,
    UserNotFoundException,
)

__all__ = [
    # Auth exceptions
    "ForbiddenException",
    "UnauthenticatedException",
    "IncorrectModel",
    "InvalidCredentialsException",
    "TokenExpiredException",
    # User exceptions
    "UserNotFoundException",
    "UserAlreadyExistsException",
    "InvalidUserDataException",
    "EmailFormatException",
    "EmailInUseException",
    "UserInactiveException",
    "UserHasActiveProjectsException",
    # Project exceptions
    "ProjectNotFoundException",
    "ProjectHasActiveUsersException",
    "ProjectAlreadyExistsException",
    "InvalidProjectDataException",
    "DatabaseConnectionException",
    # User-Project exceptions
    "UserProjectNotFoundException",
    # Base exception
    "AppException",
]
