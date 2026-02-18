from src.exceptions.base import AppException


class UserNotFoundException(AppException):
    status_code = 404
    error_code = "error:user-not-found"
    message = "User not found"


class UserAlreadyExistsException(AppException):
    status_code = 409
    error_code = "error:user-already-exists"
    message = "User with the given email already exists"


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
