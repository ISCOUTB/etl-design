from src.exceptions.base import AppException


class UserProjectNotFoundException(AppException):
    status_code = 404
    error_code = "error:user-project-not-found"
    message = "User-Project association not found."
