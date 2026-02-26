from src.exceptions.base import AppException


class UploadTaskNotFoundException(AppException):
    status_code = 404
    error_code = "error:upload-task-not-found"
    message = "Upload task not found"
