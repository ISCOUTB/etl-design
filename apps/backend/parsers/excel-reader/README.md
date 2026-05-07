# Excel Reader Service

Excel Reader is a FastAPI REST service that orchestrates spreadsheet processing and coordinates three parser microservices:

- Formula Parser
- DDL Generator
- SQL Builder

It also exposes an insertion endpoint that generates `INSERT INTO` statements directly from spreadsheet data.

## Overview

This service is responsible for:

- Receiving spreadsheet uploads (`.xlsx`, `.xls`, `.csv`)
- Extracting spreadsheet data and formulas
- Calling Formula Parser to build ASTs
- Calling DDL Generator to transform ASTs into SQL expressions
- Calling SQL Builder to build final table-level SQL
- Generating insertion SQL for non-formula columns
- Running as the current REST implementation while the gRPC migration remains pending

## Current Architecture

```text
Client (HTTP)
   |
   v
Excel Reader (FastAPI REST)
   |-- gRPC -> Formula Parser
   |-- gRPC -> DDL Generator
   |-- gRPC -> SQL Builder
```

## API Endpoints

### `POST /parser/excel`

Orchestrates Formula Parser + DDL Generator + SQL Builder from an uploaded spreadsheet.

Request:

- `spreadsheet` (file, required)
- `dtypes_str` (form stringified JSON, required; must match `SpreadsheetDtypesSchema`)
- `table_name` (form string, required)
- `limit` (query int, optional, default `50`)
- `fill_spaces` (query string, optional, default `" "`)
- Each sheet in `dtypes_str` maps column letters to objects with `dtype` plus optional `unique`, `optional`, `primary_key`, and `constraints` fields.
- `constraints` can use numeric fields such as `minimum`, `maximum`, `exclusive_minimum`, `exclusive_maximum`, and `multiple_of`, or string fields such as `min_length`, `max_length`, and `pattern`.

Response:

- `Dict[str, str]` where each key is a table/sheet name and each value is generated SQL.
- If one sheet is returned, key is normalized to the provided `table_name`.
- The exact SQL string depends on the workbook contents, column metadata, and constraint flags such as `primary_key`, `unique`, `optional`, and `constraints`.

Example:

```bash
curl -X POST "http://localhost:8001/parser/excel" \
  -H "Content-Type: multipart/form-data" \
  -F "spreadsheet=@sample.xlsx" \
  -F "table_name=users" \
   -F 'dtypes_str={"Sheet1": {"A": {"dtype": "integer", "optional": false, "primary_key": true}, "B": {"dtype": "string", "optional": true, "unique": true, "constraints": {"max_length": 120}}}}'
```

Example response:

```json
{
   "users": "CREATE TABLE IF NOT EXISTS users (... PRIMARY KEY ..., UNIQUE ..., CHECK (...));"
}
```

### `POST /parser/json`

Builds SQL directly from a JSON Schema payload and primary keys.

Request body:

- `jsonschema` (object with root type `object` and a non-empty `properties` map)
- `table_name` (string)
- `primary_keys` (list of strings, optional)

Response:

- `Dict[str, str]` with one key (`table_name`) and generated SQL as value.
- The exact SQL string depends on schema properties, required fields, primary keys, and constraints.

Example request:

```json
{
  "table_name": "users",
  "jsonschema": {
    "type": "object",
    "required": ["id", "email"],
    "properties": {
      "id": {"type": "integer"},
      "email": {"type": "string", "maxLength": 255, "unique": true},
      "age": {"type": "integer", "minimum": 0}
    }
  },
  "primary_keys": ["id"]
}
```

Example response:

```json
{
  "users": "CREATE TABLE IF NOT EXISTS users (... PRIMARY KEY ..., UNIQUE ..., CHECK (...));"
}
```

### `POST /insert-sql`

Generates `INSERT INTO` statements from spreadsheet data.

Request:

- `spreadsheet` (file, required)
- `table_name` (form string, required)
- `overwrite` (form bool, optional, default `false`)

Behavior:

- Uses only non-formula columns for inserts.
- If `overwrite=true`, the output string also includes a temp-table block, a `BEGIN`/`COMMIT` section, and table rename/drop statements.

Example response:

```json
{
   "users": "INSERT INTO users (id, name) VALUES (1, 'Alice'), (2, NULL);"
}
```

### `GET /metrics`

Prometheus metrics endpoint provided by `prometheus-fastapi-instrumentator`.

## Configuration

Environment variables (`src/core/config.py`):

```env
EXCEL_READER_HOST=localhost
EXCEL_READER_PORT=8001
EXCEL_READER_DEBUG=False

FORMULA_PARSER_HOST=localhost
FORMULA_PARSER_PORT=50052

DDL_GENERATOR_HOST=localhost
DDL_GENERATOR_PORT=50053

SQL_BUILDER_HOST=localhost
SQL_BUILDER_PORT=50054
```

Derived channels:

- `FORMULA_PARSER_CHANNEL=<host>:<port>`
- `DDL_GENERATOR_CHANNEL=<host>:<port>`
- `SQL_BUILDER_CHANNEL=<host>:<port>`

## Installation

Prerequisites:

- Python `3.12.10`
- `uv`

Setup:

```bash
uv sync
```

Run server:

```bash
uv run python src/server_rest.py
```

## Project Structure

```text
excel-reader
├── src
│   ├── core
│   │   ├── config.py
│   │   └── __init__.py
│   ├── services
│   │   ├── get_data.py
│   │   ├── __init__.py
│   │   ├── insert.py
│   │   ├── json_schema.py
│   │   ├── parse_formulas.py
│   │   └── utils.py
│   ├── utils
│   │   ├── deps.py
│   │   ├── __init__.py
│   │   ├── logger.py
│   │   ├── monitor_performance.py
│   │   └── sql.py
│   ├── schemas.py
│   └── server_rest.py
├── tests
│   ├── conftest.py
│   ├── test_get_data.py
│   ├── test_insert.py
│   ├── test_json_schema.py
│   ├── test_parse_formulas.py
│   ├── test_server_rest.py
│   ├── test_services_utils.py
│   └── test_utils_sql.py
├── Dockerfile
├── moon.yml
├── pyproject.toml
├── README.md
└── uv.lock
```

## Key Internal Flows

### Spreadsheet Flow (`/parser/excel`)

1. Parse and validate `dtypes_str`.
2. Extract spreadsheet cells/columns from file bytes.
3. Parse formulas with Formula Parser.
4. Convert ASTs to DDL fragments with DDL Generator.
5. Build final SQL per sheet with SQL Builder.

### JSON Schema Flow (`/parser/json`)

1. Validate `table_name` and schema.
2. Convert JSON Schema into SQL Builder payload (`cols`, `dtypes`).
3. Build final SQL with SQL Builder.

### Insertion Flow (`/insert-sql`)

1. Extract sheet data.
2. Keep only non-formula columns.
3. Emit `INSERT INTO ... VALUES ...` statements.
4. Optionally wrap with overwrite strategy SQL.

## Error Handling

Common validation errors:

- Empty uploaded file -> HTTP `400`
- Missing filename -> HTTP `400`
- Invalid `dtypes_str` JSON -> HTTP `400`
- `dtypes_str` schema mismatch -> HTTP `400`
- DDL sheet keys not matching dtypes sheet keys -> HTTP `400`
- Blank `table_name` in `/parser/json` -> HTTP `400`

## Testing

Run all tests:

```bash
uv run -m pytest tests/ -v
```

Run with coverage:

```bash
uv run -m pytest tests/ -v --cov=src --cov-report=term-missing
```

Current suite includes endpoint, service, and utility level tests.

## Dependencies

Core runtime dependencies (from `pyproject.toml`):

- `fastapi[standard]`
- `openpyxl`
- `pydantic`
- `pydantic-settings`
- `prometheus-fastapi-instrumentator`
- `proto-utils`

## Notes

- The service interface is REST.
- Internal communication to Formula Parser, DDL Generator, and SQL Builder is gRPC via stubs in `src/utils/deps.py`.
