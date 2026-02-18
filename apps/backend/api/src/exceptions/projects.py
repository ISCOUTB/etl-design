from src.exceptions.base import AppException


class ProjectNotFoundException(AppException):
    status_code = 404
    error_code = "error:project-not-found"
    message = "Project not found"


class ProjectAlreadyExistsException(AppException):
    status_code = 409
    error_code = "error:project-already-exists"
    message = "Project with the given name already exists"


class InvalidProjectDataException(AppException):
    status_code = 400
    error_code = "error:invalid-project-data"
    message = "Invalid project data provided"


class DatabaseConnectionException(AppException):
    status_code = 503
    error_code = "error:database-connection"
    message = "Failed to connect to the database"
