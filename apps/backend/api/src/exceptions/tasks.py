from src.exceptions.base import AppException


class TaskNotFoundException(AppException):
    error_code = "error:task:not-found"
    status_code = 404
    message = "Task not found for the given ID."
