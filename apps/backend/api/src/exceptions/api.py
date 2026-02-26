from src.exceptions.base import AppException


class FileContentEmptyException(AppException):
    status_code = 400
    error_code = "error:file-content-empty"
    message = "Uploaded file is empty. Please provide a valid file with content."


class FilenameEmptyException(AppException):
    status_code = 400
    error_code = "error:filename-empty"
    message = (
        "Uploaded file must have a filename. Please provide a valid file with a name."
    )


class ContentTypeEmptyException(AppException):
    status_code = 400
    error_code = "error:content-type-empty"
    message = "Uploaded file must have a content type. Please provide a valid file with a content type."
