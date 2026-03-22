from src.exceptions.base import AppException


class ProjectNotFoundException(AppException):
    status_code = 404
    error_code = "error:project-not-found"
    message = "Project not found"


class ProjectAlreadyExistsException(AppException):
    status_code = 409
    error_code = "error:project-already-exists"
    message = "Project with the given name already exists"


class ProjectHasActiveUsersException(AppException):
    status_code = 400
    error_code = "error:project-has-active-users"
    message = "Cannot delete project with active users"


class InvalidProjectDataException(AppException):
    status_code = 400
    error_code = "error:invalid-project-data"
    message = "Invalid project data provided"


class DatabaseConnectionException(AppException):
    status_code = 503
    error_code = "error:database-connection"
    message = "Failed to connect to the database"


class InvalidDBCredentialsException(AppException):
    status_code = 400
    error_code = "error:invalid-db-credentials"
    message = "Invalid database credentials provided"


class CouldNotConnectToDatabaseException(AppException):
    status_code = 503
    error_code = "error:could-not-connect-to-database"
    message = "Could not connect to the database with the provided credentials"


class UserAlreadyInProjectException(AppException):
    status_code = 400
    error_code = "error:user-already-in-project"
    message = "User is already associated with the project"
