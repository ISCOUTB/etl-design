from src.exceptions.base import AppException


class ForbiddenException(AppException):
    status_code = 403
    error_code = "error:unauthorized"
    message = "Unauthorized access"


class UnauthenticatedException(AppException):
    status_code = 401
    error_code = "error:unauthenticated"
    message = "Authentication required"


class InvalidCredentialsException(AppException):
    status_code = 401
    error_code = "error:invalid-credentials"
    message = "Invalid email or password"


class TokenExpiredException(AppException):
    status_code = 401
    error_code = "error:token-expired"
    message = "Authentication token has expired"
