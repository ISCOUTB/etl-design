# Idempotency is now handled by IdempotencyService which ensures atomicity
# across database, Redis cache, and RabbitMQ operations.
# All upload operations (validate, insert, process) use idempotency keys
# to prevent duplicate requests within a configurable time window.

import json
from typing import Annotated, Dict

import httpx
import psycopg2
from fastapi import APIRouter, Form, HTTPException, Query, Request, UploadFile
from proto_utils.database import dtypes
from pydantic import ValidationError

from src.api.deps import (
    CurrentUser,
    DatabaseClientDep,
    IdempotencyServiceDep,
    ProjectServiceDep,
    PublisherDep,
)
from src.core.config import settings
from src.exceptions import (
    DtypesInvalidContentException,
    DtypesInvalidJsonObjectException,
    DtypesInvalidJsonStringException,
    ExcelReaderErrorException,
    ForbiddenException,
    InvalidDBCredentialsException,
    Psycopg2ErrorException,
)
from src.models import Project
from src.schemas import (
    CreateTableFromJsonSchemaRequest,
    CreateTableResponse,
    SpreadsheetDtypesSchema,
)
from src.services import SchemaService
from src.services.permissions import Action, ModelKeys, PermissionService

router = APIRouter()

HTTPX_CLIENT = httpx.AsyncClient(timeout=settings.EXCEL_READER_TIMEOUT_SECONDS)


def _execute_sql_per_sheet(
    *,
    uri: str,
    sql_per_sheet: Dict[str, str],
) -> None:
    with psycopg2.connect(uri) as conn:
        cur = conn.cursor()
        for _, sql in sql_per_sheet.items():
            cur.execute(sql)
        conn.commit()


@router.post("/validate")
async def validate(
    request: Request,
    current_user: CurrentUser,
    publisher: PublisherDep,
    database_client: DatabaseClientDep,
    idempotency_service: IdempotencyServiceDep,
    spreadsheet_file: Annotated[UploadFile, Form()],
    project_id: Annotated[str, Form()],
    table_name: Annotated[str, Form()],
) -> dtypes.ApiResponse:
    """
    Upload a spreadsheet file in order to be validated.
    """
    has_permission = PermissionService.has_permission(
        user=current_user,
        action=Action.validate,
        model_key=ModelKeys.upload,
        model=Project(id=project_id),
    )
    if not has_permission:
        raise ForbiddenException()

    try:
        trace_headers = {}
        if hasattr(request, "state") and hasattr(request.state, "trace_headers"):
            trace_headers = request.state.trace_headers

        response = await idempotency_service.validate_task(
            db_client=database_client,
            publisher=publisher,
            spreadsheet_file=spreadsheet_file,
            user_id=current_user.id,
            project_id=project_id,
            table_name=table_name,
            trace_headers=trace_headers,
        )
        return response
    except Exception:
        # Exception handlers will manage this
        raise


@router.post("/insert")
async def insert(
    request: Request,
    current_user: CurrentUser,
    publisher: PublisherDep,
    database_client: DatabaseClientDep,
    project_service: ProjectServiceDep,
    idempotency_service: IdempotencyServiceDep,
    spreadsheet_file: Annotated[UploadFile, Form()],
    project_id: Annotated[str, Form()],
    table_name: Annotated[str, Form()],
    overwrite: bool = False,
):
    """Insert data from a validated spreadsheet file into the database.
    this is not intented to be used always, just in specific cases, where all the
    pipeline (validation + insert) cannot be used.
    """
    has_permission = PermissionService.has_permission(
        user=current_user,
        action=Action.insert,
        model_key=ModelKeys.upload,
        model=Project(id=project_id),
    )
    if not has_permission:
        raise ForbiddenException()

    # Fetch db credentials of the project
    db_uri = project_service.get_project_db_uri(project_id)

    try:
        trace_headers = {}
        if hasattr(request, "state") and hasattr(request.state, "trace_headers"):
            trace_headers = request.state.trace_headers

        response = await idempotency_service.insert_task(
            db_client=database_client,
            publisher=publisher,
            spreadsheet_file=spreadsheet_file,
            user_id=current_user.id,
            project_id=project_id,
            table_name=table_name,
            db_uri=db_uri,
            overwrite=overwrite,
            trace_headers=trace_headers,
        )
        return response
    except Exception:
        # Exception handlers will manage this
        raise


@router.post("/process")
async def process(
    request: Request,
    current_user: CurrentUser,
    publisher: PublisherDep,
    database_client: DatabaseClientDep,
    project_service: ProjectServiceDep,
    idempotency_service: IdempotencyServiceDep,
    spreadsheet_file: Annotated[UploadFile, Form()],
    project_id: Annotated[str, Form()],
    table_name: Annotated[str, Form()],
    overwrite: bool = False,
):
    """Validates and inserts data from a spreadsheet file into the database.
    Actually, it just publish the task to the mq, the worker will do the rest.
    """
    has_permission = PermissionService.has_permission(
        user=current_user,
        action=Action.process,
        model_key=ModelKeys.upload,
        model=Project(id=project_id),
    )
    if not has_permission:
        raise ForbiddenException()

    # Fetch db credentials of the project
    db_uri = project_service.get_project_db_uri(project_id)

    try:
        trace_headers = {}
        if hasattr(request, "state") and hasattr(request.state, "trace_headers"):
            trace_headers = request.state.trace_headers

        response = await idempotency_service.process_task(
            db_client=database_client,
            publisher=publisher,
            spreadsheet_file=spreadsheet_file,
            user_id=current_user.id,
            project_id=project_id,
            table_name=table_name,
            db_uri=db_uri,
            overwrite=overwrite,
            trace_headers=trace_headers,
        )
        return response
    except Exception:
        # Exception handlers will manage this
        raise


# To be completely fair, one spreadsheet may contain multiple sheets,
# but we're only taking one. In the future, we will support
# multiple sheets, and even the dependency between them
@router.post("/table-excel")
async def create_table(
    request: Request,
    current_user: CurrentUser,
    project_service: ProjectServiceDep,
    db_client: DatabaseClientDep,
    spreadsheet: UploadFile,
    project_id: Annotated[str, Form()],
    table_name: Annotated[str, Form()],
    dtypes_str: Annotated[str, Form()],
    execute_sql: bool = True,
) -> CreateTableResponse:
    has_permission = PermissionService.has_permission(
        user=current_user,
        action=Action.table,
        model_key=ModelKeys.upload,
        model=Project(id=project_id),
    )
    if not has_permission:
        raise ForbiddenException()

    db_uri = project_service.get_project_db_uri(project_id, ping=execute_sql)

    try:
        dtypes_json = json.loads(dtypes_str)
        if not isinstance(dtypes_json, dict):
            raise DtypesInvalidJsonObjectException()

        # Validate the content of dtypes_json and convert it to the expected format
        dtypes = {
            str(sheet_name): dict(
                map(
                    lambda item: (str(item[0]), SpreadsheetDtypesSchema(**item[1])),
                    sheet_json.items(),
                )
            )
            for sheet_name, sheet_json in dtypes_json.items()
        }
    except json.JSONDecodeError:
        raise DtypesInvalidJsonStringException()
    except ValidationError:
        raise DtypesInvalidContentException()

    fill_spaces = "_"

    # Extract trace headers from request state (set by LogsMiddleware)
    headers = {}
    if hasattr(request, "state") and hasattr(request.state, "trace_headers"):
        trace_headers = request.state.trace_headers
        # Only include headers that have values
        if trace_headers.get("traceparent"):
            headers["traceparent"] = trace_headers["traceparent"]
        if trace_headers.get("tracestate"):
            headers["tracestate"] = trace_headers["tracestate"]
        if trace_headers.get("baggage"):
            headers["baggage"] = trace_headers["baggage"]

    response = await HTTPX_CLIENT.post(
        f"{settings.EXCEL_READER_URL}/parser/excel",
        files={
            "spreadsheet": (
                spreadsheet.filename,
                await spreadsheet.read(),
                spreadsheet.content_type,
            )
        },
        data={
            "table_name": table_name,
            "dtypes_str": dtypes_str,
        },
        params={"fill_spaces": fill_spaces, "limit": 5},
        headers=headers,
    )

    if response.is_error:
        try:
            detail = response.json().get("detail", response.text)
        except Exception:
            detail = response.text

        raise ExcelReaderErrorException(
            status_code=response.status_code,
            message=f"Excel Reader error: {detail}",
        )

    sql_per_sheet = response.json()

    # Once the file is parsed and the SQL statements are generated, we can execute them if requested.
    # But, first, is neccesary create the jsonschema instance and save it in the db, because the worker
    # will need it to validate the data before insert it.

    # Create the JSON Schema for the table and save it in the database
    save_schema_responses = {}
    for sheet_name, sheet_data in dtypes.items():
        required_fields = [
            field_name for field_name, dtype in sheet_data.items() if not dtype.optional
        ]

        properties = dict(
            map(
                lambda item: (item[0], item[1].to_jsonschema_property()),
                sheet_data.items(),
            )
        )
        jsonschema = {
            "$schema": "https://json-schema.org/draft-07/schema",
            "type": "object",
            "required": required_fields,
            "properties": properties,
        }

        save_schema_response = await SchemaService.save_schema(
            import_name=f"{project_id}__{sheet_name}",
            orig_schema=jsonschema,
            database_client=db_client,
        )

        save_schema_responses[sheet_name] = save_schema_response

    # Execute the generated SQL statements to create the table in the database if requested
    if execute_sql:
        try:
            _execute_sql_per_sheet(uri=db_uri, sql_per_sheet=sql_per_sheet)
        except InvalidDBCredentialsException:
            raise
        except psycopg2.OperationalError as e:
            raise Psycopg2ErrorException(
                message="An error occurred while processing the database operation.\n"
                f"Error details: {str(e)}\nSQL attempted: {json.dumps(sql_per_sheet)}"
            )

        return CreateTableResponse(
            message="Table created successfully",
            sql_per_sheet=sql_per_sheet,
            schema_saved=save_schema_responses,
        )

    return CreateTableResponse(
        message="SQL generated successfully (execution skipped)",
        sql_per_sheet=sql_per_sheet,
        schema_saved=save_schema_responses,
    )


@router.post("/table-json")
async def create_table_from_json_schema(
    current_user: CurrentUser,
    db_client: DatabaseClientDep,
    project_service: ProjectServiceDep,
    payload: CreateTableFromJsonSchemaRequest,
    execute_sql: Annotated[bool, Query()] = True,
) -> CreateTableResponse:
    """Create a table from a JSON Schema.

    Accepts a JSON request body with:
    - table_name: Name of the table to create
    - jsonschema: JSON Schema object describing the table structure
    - primary_keys: List of column names that form the primary key (optional)
    - execute_sql: Query parameter to execute the generated SQL (default: true)
    """
    project_id = payload.project_id
    table_name = payload.table_name

    has_permission = PermissionService.has_permission(
        user=current_user,
        action=Action.table,
        model_key=ModelKeys.upload,
        model=Project(id=project_id),
    )
    if not has_permission:
        raise ForbiddenException()

    db_uri = project_service.get_project_db_uri(project_id, ping=execute_sql)

    try:
        response = await HTTPX_CLIENT.post(
            f"{settings.EXCEL_READER_URL}/parser/json",
            json={
                "table_name": payload.table_name,
                "jsonschema": payload.jsonschema,
                "primary_keys": payload.primary_keys,
            },
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to communicate with Excel Reader service: {str(e)}",
        )

    if response.is_error:
        try:
            detail = response.json().get("detail", response.text)
        except Exception:
            detail = response.text

        raise HTTPException(
            status_code=response.status_code,
            detail=f"Excel Reader error: {detail}",
        )

    sql_per_sheet = response.json()

    # Create the JSON Schema for the table and save it in the database
    save_schema_response = await SchemaService.save_schema(
        import_name=f"{project_id}__{table_name}",
        orig_schema=payload.jsonschema,
        database_client=db_client,
    )

    if execute_sql:
        try:
            _execute_sql_per_sheet(uri=db_uri, sql_per_sheet=sql_per_sheet)
        except InvalidDBCredentialsException:
            raise
        except Exception as e:
            raise Psycopg2ErrorException(
                message="An error occurred while processing the database operation.\n"
                f"Error details: {str(e)}\nSQL attempted: {sql_per_sheet}"
            )

        return CreateTableResponse(
            message="Table created successfully",
            sql_per_sheet=sql_per_sheet,
            schema_saved={"Sheet1": save_schema_response},
        )

    return CreateTableResponse(
        message="SQL generated successfully (execution skipped)",
        sql_per_sheet=sql_per_sheet,
        schema_saved={"Sheet1": save_schema_response},
    )
