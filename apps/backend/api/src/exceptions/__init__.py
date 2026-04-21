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
    CouldNotConnectToDatabaseException,
    DatabaseConnectionException,
    InvalidDBCredentialsException,
    InvalidProjectDataException,
    ProjectHasActiveUsersException,
    ProjectNotFoundException,
    UserAlreadyInProjectException,
)
from src.exceptions.schemas import (
    InvalidJsonSchemaDraftException,
    InvalidJsonSchemaException,
    InvalidJsonSchemaTypeException,
    MissingJsonSchemaDraftException,
    SchemaNotFoundException,
    SchemaNotProvidedException,
)
from src.exceptions.tasks import TaskNotFoundException
from src.exceptions.uploads import (
    DtypesInvalidContentException,
    DtypesInvalidJsonObjectException,
    DtypesInvalidJsonStringException,
    ExcelReaderErrorException,
    Psycopg2CouldNotConnectToDatabaseException,
    Psycopg2ErrorException,
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
    "CouldNotConnectToDatabaseException",
    "ProjectNotFoundException",
    "ProjectHasActiveUsersException",
    "InvalidProjectDataException",
    "InvalidDBCredentialsException",
    "DatabaseConnectionException",
    "UserAlreadyInProjectException",
    # Schema exceptions
    "InvalidJsonSchemaDraftException",
    "InvalidJsonSchemaException",
    "InvalidJsonSchemaTypeException",
    "MissingJsonSchemaDraftException",
    "SchemaNotFoundException",
    "SchemaNotProvidedException",
    # Task exceptions
    "TaskNotFoundException",
    # User-Project exceptions
    "UserProjectNotFoundException",
    # Base exception
    "AppException",
    # Upload exceptions
    "DtypesInvalidJsonStringException",
    "DtypesInvalidJsonObjectException",
    "DtypesInvalidContentException",
    "ExcelReaderErrorException",
    "Psycopg2CouldNotConnectToDatabaseException",
    "Psycopg2ErrorException",
    "UploadTaskNotFoundException",
]
