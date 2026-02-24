from src.exceptions.base import AppException


class UserNotFoundException(AppException):
    status_code = 404
    error_code = "error:user-not-found"
    message = "User not found"


class EmailInUseException(AppException):
    status_code = 409
    error_code = "error:email-in-use"
    message = "Email is already in use"


class UserHasActiveProjectsException(AppException):
    status_code = 400
    error_code = "error:user-has-active-projects"
    message = "Cannot delete user with active projects"


class InvalidUserDataException(AppException):
    status_code = 400
    error_code = "error:invalid-user-data"
    message = "Invalid user data provided"


class EmailFormatException(AppException):
    status_code = 400
    error_code = "error:invalid-email-format"
    message = "Email format is invalid"


class UserInactiveException(AppException):
    status_code = 403
    error_code = "error:user-inactive"
    message = "User account is inactive"
