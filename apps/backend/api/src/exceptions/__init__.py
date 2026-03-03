from src.exceptions.api import (
    ContentTypeEmptyException,
    FileContentEmptyException,
    FilenameEmptyException,
)
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
    InvalidDBCredentialsException,
    InvalidProjectDataException,
    ProjectAlreadyExistsException,
    ProjectHasActiveUsersException,
    ProjectNotFoundException,
    UserAlreadyInProjectException,
)
from src.exceptions.schemas import (
    InvalidJsonSchemaException,
    SchemaNotFoundException,
    SchemaNotProvidedException,
)
from src.exceptions.tasks import TaskNotFoundException
from src.exceptions.uploads import (
    UploadTaskNotFoundException,
)
from src.exceptions.user_project import UserProjectNotFoundException
from src.exceptions.users import (
    EmailFormatException,
    EmailInUseException,
    InvalidUserDataException,
    UserHasActiveProjectsException,
    UserInactiveException,
    UserNotFoundException,
)

__all__ = [
    # API exceptions
    "ContentTypeEmptyException",
    "FileContentEmptyException",
    "FilenameEmptyException",
    # Auth exceptions
    "ForbiddenException",
    "UnauthenticatedException",
    "IncorrectModel",
    "InvalidCredentialsException",
    "TokenExpiredException",
    # User exceptions
    "UserNotFoundException",
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
    "InvalidDBCredentialsException",
    "DatabaseConnectionException",
    "UserAlreadyInProjectException",
    # Schema exceptions
    "InvalidJsonSchemaException",
    "SchemaNotFoundException",
    "SchemaNotProvidedException",
    # Task exceptions
    "TaskNotFoundException",
    # User-Project exceptions
    "UserProjectNotFoundException",
    # Base exception
    "AppException",
    # Upload exceptions
    "UploadTaskNotFoundException",
]
