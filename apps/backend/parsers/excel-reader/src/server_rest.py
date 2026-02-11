# TODO: Migrate this REST server to gRPC
import json
from typing import Annotated, Dict

from fastapi import Depends, FastAPI, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from proto_utils.generated.parsers import (
    ddl_generator_pb2_grpc,
    formula_parser_pb2_grpc,
    sql_builder_pb2_grpc,
)

from src.core.config import settings
from src.services.insert import create_sql_for_insertion
from src.services.parse_formulas import generate_sql, parse_formulas_with_ddl
from src.utils import LOGGING_CONFIG, logger
from src.utils.deps import (
    get_ddl_generator_stub,
    get_formula_parser_stub,
    get_sql_builder_stub,
)
from src.utils.monitor_performance import monitor_performance

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

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/excel-parser")
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
        dtypes = json.loads(dtypes_str)
    except json.JSONDecodeError as e:
        raise HTTPException(
            status_code=400, detail=f"Invalid dtypes JSON: {str(e)}"
        )

    if not table_name:
        table_name = ""

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

    return {
        sheet: generate_sql(
            sql_builder_stub,
            ddls[sheet],
            dtypes[sheet],
            f"{table_name}_{sheet}",
        )
        for sheet in ddls.keys()
    }


@app.post("/insert-sql")
@monitor_performance("insert_sql")
async def insert_sql(
    spreadsheet: UploadFile,
    table_name: str = Form(...),
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
    sql_statements = create_sql_for_insertion(table_name, file_content, filename)
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
