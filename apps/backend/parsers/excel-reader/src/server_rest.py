# TODO: Migrate this REST server to gRPC
import json
from typing import Annotated, Dict

from fastapi import Depends, FastAPI, Form, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from opentelemetry import context as otel_context
from opentelemetry.propagate import extract
from prometheus_fastapi_instrumentator import Instrumentator
from proto_utils.generated.parsers import (
    ddl_generator_pb2_grpc,
    formula_parser_pb2_grpc,
    sql_builder_pb2_grpc,
)
from pydantic import ValidationError

from src.core.config import settings
from src.schemas import (
    ColumnDtypesSchema,
    JSONSchemaRequest,
    SpreadsheetDtypesSchema,
)
from src.services.insert import create_sql_for_insertion
from src.services.json_schema import json_schema_to_sql_builder_payload
from src.services.parse_formulas import generate_sql, parse_formulas_with_ddl
from src.utils import LOGGING_CONFIG, logger
from src.utils.deps import (
    get_ddl_generator_stub,
    get_formula_parser_stub,
    get_sql_builder_stub,
)
from src.utils.formatting import standardize_string
from src.utils.monitor_performance import monitor_performance
from src.utils.sql import generate_extra_statements_sql, get_column_type_sql

# ======== Dependency Injection ========

FormulaParserDep = Annotated[
    formula_parser_pb2_grpc.FormulaParserStub,
    Depends(get_formula_parser_stub),
]

DDLGeneratorDep = Annotated[
    ddl_generator_pb2_grpc.DDLGeneratorStub,
    Depends(get_ddl_generator_stub),
]

SQLBuilderDep = Annotated[
    sql_builder_pb2_grpc.SQLBuilderStub,
    Depends(get_sql_builder_stub),
]

# ======== Server ========

app = FastAPI()


@app.middleware("http")
async def propagate_trace_context(request: Request, call_next):
    extracted_context = extract(dict(request.headers))
    token = otel_context.attach(extracted_context)
    try:
        return await call_next(request)
    finally:
        otel_context.detach(token)


Instrumentator().instrument(app).expose(app, endpoint="/metrics")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/parser/json")
@monitor_performance("read_json")
async def read_json(
    sql_builder_stub: SQLBuilderDep,
    payload: JSONSchemaRequest,
    fill_spaces: str = " ",
) -> Dict[str, str]:
    if settings.EXCEL_READER_DEBUG:
        logger.debug(f"Received JSON schema for table: {payload.table_name}")

    table_name = payload.table_name.strip()
    if not table_name:
        raise HTTPException(status_code=400, detail="'table_name' is required")

    try:
        cols, dtypes = json_schema_to_sql_builder_payload(
            payload.jsonschema,
            payload.primary_keys,
            fill_spaces=fill_spaces,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    sql_statement = generate_sql(
        sql_builder_stub,
        cols,
        dtypes,
        table_name,
    )
    return {table_name: sql_statement}


@app.post("/parser/excel")
@monitor_performance("read_excel")
async def read_excel(
    spreadsheet: UploadFile,
    formula_parser_stub: FormulaParserDep,
    ddl_generator_stub: DDLGeneratorDep,
    sql_builder_stub: SQLBuilderDep,
    dtypes_str: str = Form(...),
    table_name: str = Form(...),
    limit: int = 50,
    fill_spaces: str = " ",
) -> Dict[str, str]:
    if settings.EXCEL_READER_DEBUG:
        logger.debug(f"Received file: {spreadsheet.filename}")

    file_content = await spreadsheet.read()
    if not file_content:
        raise HTTPException(status_code=400, detail="File content is empty")

    filename = spreadsheet.filename
    if not filename:
        raise HTTPException(status_code=400, detail="Filename is required")

    try:
        dtypes_json = json.loads(dtypes_str)
        if not isinstance(dtypes_json, dict):
            raise HTTPException(
                status_code=400,
                detail="Dtypes JSON must be an object/dictionary",
            )

        # Validate the content of dtypes_json and convert it to the expected format
        dtypes_validated: Dict[str, ColumnDtypesSchema] = {
            sheet_name: dict(
                map(
                    lambda item: (
                        standardize_string(
                            str(item[0]), fill_spaces=fill_spaces
                        ),
                        SpreadsheetDtypesSchema(**item[1]),
                    ),
                    sheet_data.items(),
                )
            )
            for sheet_name, sheet_data in dtypes_json.items()
        }
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=400, detail="Invalid JSON format for dtypes"
        )
    except ValidationError as e:
        print(repr(e))
        raise HTTPException(
            status_code=400,
            detail="Dtypes JSON does not match the expected schema",
        )

    if not table_name:
        table_name = ""

    # Parse dtypes to use OPTIONAL, PRIMARY KEY, etc. in SQL generation
    dtypes = {
        sheet_name: dict(
            map(
                lambda col_info: (
                    col_info[0],
                    {
                        "type": get_column_type_sql(col_info[1]),
                        "extra": generate_extra_statements_sql(
                            col_info[0], col_info[1]
                        ),
                    },
                ),
                dtypes_col.items(),
            )
        )
        for sheet_name, dtypes_col in dtypes_validated.items()
    }

    logger.info(f"Processing file: {filename}")
    content = parse_formulas_with_ddl(
        formula_parser_stub=formula_parser_stub,
        ddl_generator_stub=ddl_generator_stub,
        filename=filename,
        file_bytes=file_content,
        limit=limit,
        fill_spaces=fill_spaces,
    )
    result = content["result"]
    columns = content["columns"]

    ddls = {
        sheet: dict(
            map(
                lambda x: (x[1]["name"], result[sheet][x[0]][0]["sql"]),
                columns[sheet].items(),
            )
        )
        for sheet in columns.keys()
    }

    ddl_keys = set(ddls.keys())
    dtype_keys = set(dtypes.keys())
    if not ddl_keys.issubset(dtype_keys):
        raise HTTPException(
            status_code=400,
            detail=(
                "Mismatch between sheets in DDLs and dtypes. "
                "DDL keys is not subset of dtypes keys."
            ),
        )

    sql_statements = {
        sheet: generate_sql(
            sql_builder_stub,
            ddls[sheet],  # type: ignore
            dtypes[sheet],
            (f"{table_name}_{sheet}" if len(ddls) > 1 else table_name),
        )
        for sheet in ddls.keys()
    }

    keys = list(sql_statements.keys())
    if len(keys) == 1:
        sql_statements = {table_name: sql_statements[keys[0]]}

    return sql_statements


@app.post("/insert-sql")
@monitor_performance("insert_sql")
async def insert_sql(
    spreadsheet: UploadFile,
    table_name: str = Form(...),
    overwrite: bool = False,
) -> Dict[str, str]:
    if settings.EXCEL_READER_DEBUG:
        logger.debug(f"Received file for SQL insertion: {spreadsheet.filename}")

    file_content = await spreadsheet.read()
    if not file_content:
        raise HTTPException(status_code=400, detail="File content is empty")

    filename = spreadsheet.filename
    if not filename:
        raise HTTPException(status_code=400, detail="Filename is required")

    logger.info(f"Processing SQL insertion for file: {filename}")
    sql_statements = create_sql_for_insertion(
        table_name, file_content, filename, truncate=overwrite
    )

    keys = list(sql_statements.keys())
    if len(keys) == 1:
        sql_statements = {table_name: sql_statements[keys[0]]}

    return sql_statements


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "src.server_rest:app",
        host=settings.EXCEL_READER_HOST,
        port=settings.EXCEL_READER_PORT,
        reload=settings.EXCEL_READER_DEBUG,
        log_config=LOGGING_CONFIG,
        reload_dirs=["src"] if settings.EXCEL_READER_DEBUG else None,
        reload_includes=["*.py"] if settings.EXCEL_READER_DEBUG else None,
    )
