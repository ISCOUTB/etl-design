from src.exceptions.base import AppException


class UploadTaskNotFoundException(AppException):
    status_code = 404
    error_code = "error:upload-task-not-found"
    message = "Upload task not found"


class DtypesInvalidJsonStringException(AppException):
    status_code = 400
    error_code = "error:dtypes-invalid-json-string"
    message = "Invalid dtypes_str format. Must be a valid JSON string."


class DtypesInvalidJsonObjectException(AppException):
    status_code = 400
    error_code = "error:dtypes-invalid-json-object"
    message = "Invalid dtypes_str format. Must be a JSON object."


class DtypesInvalidContentException(AppException):
    status_code = 422
    error_code = "error:dtypes-invalid-content"
    message = "Invalid dtypes_str content."


class Psycopg2ErrorException(AppException):
    status_code = 500
    error_code = "error:psycopg2-error"
    message = "An error occurred while processing the database operation."


class ExcelReaderErrorException(AppException):
    status_code = 500  # Depending on the context, this could also be a 400 if it's due to client input
    error_code = "error:excel-reader-error"
    message = "An error occurred while reading the Excel file."
