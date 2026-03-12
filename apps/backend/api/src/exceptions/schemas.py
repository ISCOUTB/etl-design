from src.exceptions.base import AppException


class SchemaNotProvidedException(AppException):
    error_code = "error:schema:not-provided"
    status_code = 400
    default_message = "Schema data must be provided."


class InvalidJsonSchemaException(AppException):
    error_code = "error:schema:invalid-json"
    status_code = 400
    default_message = "Invalid JSON schema provided."


class InvalidJsonSchemaTypeException(AppException):
    error_code = "error:schema:invalid-type"
    status_code = 400
    default_message = "Invalid JSON schema type. Root schema type must be 'object'."


class MissingJsonSchemaDraftException(AppException):
    error_code = "error:schema:missing-draft"
    status_code = 400
    default_message = "Missing '$schema' field in JSON schema."


class InvalidJsonSchemaDraftException(AppException):
    error_code = "error:schema:invalid-draft"
    status_code = 400
    default_message = (
        "Unsupported JSON schema draft version specified in '$schema' field."
    )


class SchemaNotFoundException(AppException):
    error_code = "error:schema:not-found"
    status_code = 404
    default_message = "Schema not found for the given import name."
