# Excel Parsing Microservices

This subsystem converts Excel workbooks into SQL-oriented outputs through a modular pipeline.

## Architecture

```text
Excel Reader (REST)
    ├── Formula Parser (gRPC, Node.js)
    ├── DDL Generator (gRPC, Python)
    └── SQL Builder (gRPC, Python)
```

The Excel Reader is the orchestration layer. It receives workbook uploads, extracts sheet data, and coordinates the gRPC services that produce SQL output.

## Services

### Excel Reader

- Entry point for spreadsheet processing.
- Accepts `.xlsx`, `.xls`, and `.csv` uploads.
- Exposes REST endpoints for workbook-to-SQL and JSON-schema-to-SQL flows.
- Coordinates formula parsing, DDL generation, and SQL assembly.

### Formula Parser

- Parses Excel formulas into tokens and ASTs.
- Runs as a Node.js gRPC service.
- Supplies structured formula data to downstream generators.

### DDL Generator

- Converts ASTs into SQL-friendly expressions.
- Maps Excel references to SQL column names.
- Runs as a Python gRPC service.

### SQL Builder

- Combines expressions into final SQL statements.
- Resolves dependency ordering.
- Runs as a Python gRPC service.

## Protocol Buffers

The service contracts live in `packages/proto/parsers/` and are consumed through the generated client packages in `packages/proto-utils/`.

## Current Flow

### Workbook to SQL

1. The client uploads a workbook to the Excel Reader.
2. The Excel Reader extracts sheet data and formulas.
3. The Formula Parser converts formulas to ASTs.
4. The DDL Generator converts ASTs to SQL expressions.
5. The SQL Builder assembles the final SQL statements.

### JSON Schema to SQL

1. The client submits a JSON schema payload.
2. The Excel Reader normalizes the request.
3. The DDL Generator and SQL Builder produce SQL without formula parsing.

## Configuration

Each service has its own `.env.example` file.

- Excel Reader: `EXCEL_READER_HOST`, `EXCEL_READER_PORT`
- Formula Parser: `FORMULA_PARSER_HOST`, `FORMULA_PARSER_PORT`
- DDL Generator: `DDL_GENERATOR_HOST`, `DDL_GENERATOR_PORT`
- SQL Builder: `SQL_BUILDER_HOST`, `SQL_BUILDER_PORT`

## Development

### Run the services

```bash
cd excel-reader && uv sync && uv run python src/server_rest.py
cd ../formula-parser && pnpm install && moon run formula-parser:run
cd ../ddl-generator && uv sync && uv run python src/server.py
cd ../sql-builder && uv sync && uv run python src/server.py
```

### Testing

- Excel Reader: endpoint and service tests under `excel-reader/tests/`
- Formula Parser: Node.js tests under `formula-parser/tests/`
- DDL Generator: Python tests under `ddl-generator/tests/`
- SQL Builder: Python tests under `sql-builder/tests/`

## Related Documentation

- [Backend Overview](../README.md)
- [Excel Reader](./excel-reader/README.md)
- [Formula Parser](./formula-parser/README.md)
- [DDL Generator](./ddl-generator/README.md)
- [SQL Builder](./sql-builder/README.md)
