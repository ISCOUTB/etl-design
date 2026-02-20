from src.exceptions.base import AppException


class SchemaNotProvidedException(AppException):
    error_code = "error:schema:not-provided"
    status_code = 400
    default_message = "Schema data must be provided."


class InvalidJsonSchemaException(AppException):
    error_code = "error:schema:invalid-json"
    status_code = 400
    default_message = "Invalid JSON schema provided."


class SchemaNotFoundException(AppException):
    error_code = "error:schema:not-found"
    status_code = 404
    default_message = "Schema not found for the given import name."
