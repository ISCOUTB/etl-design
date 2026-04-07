# SQL Builder Service

A Python gRPC service that constructs SQL DDL statements from individual DDL expressions and column metadata. This service assembles `CREATE TABLE` plus dependency-ordered `ALTER TABLE ... GENERATED ALWAYS AS (...) STORED` statements.

## Overview

The SQL Builder service provides:

- **SQL Statement Assembly**: Combines individual SQL expressions into complete statements
- **Dependency Resolution**: Manages execution order of interdependent SQL expressions
- **Schema Generation**: Creates `CREATE TABLE IF NOT EXISTS` statements for level-0 columns
- **Generated Columns**: Creates dependency-based `ALTER TABLE ... ADD COLUMN ... GENERATED ALWAYS AS` statements
- **Error Management**: Detects cyclic dependencies and reports construction errors

## Architecture

```text
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  DDL Generator  │───►│   SQL Builder   │───►│  Final SQL      │
│                 │    │   (Python)      │    │  Statements     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌─────────────────┐
                       │ Dependencies:   │
                       │ • Graph Analysis│
                       │ • Level Ordering│
                       │ • SQL Assembly  │
                       └─────────────────┘
```

## Features

- **Dependency Graph Construction**: Builds dependency graphs for SQL expressions
- **Level-Based Ordering**: Orders SQL statements based on dependency depth
- **SQL Statement Generation**: Creates valid `CREATE TABLE` and `ALTER TABLE` DDL statements
- **Column Type Management**: Handles different SQL data types and constraints
- **Constraint Handling**: Handles PRIMARY KEY cleanup on generated columns
- **Error Reporting**: Cyclic dependency detection and structured response errors

## gRPC Service Definition

The service implements the `SQLBuilder` service defined in `sql_builder.proto`:

```proto
service SQLBuilder {
    rpc BuildSQL(BuildSQLRequest) returns (BuildSQLResponse);
}

message BuildSQLRequest {
    message ColumnInfo {
        string type = 1; // Data type of the column (e.g., "INTEGER", "TEXT")
        string extra = 2; // Additional SQL constraints (e.g., "NOT NULL", "PRIMARY KEY")
    }

    map<string, ddl_generator.DDLResponse> cols = 1;
    map<string, ColumnInfo> dtypes = 2;
    string table_name = 3;
}

message BuildSQLResponse {
  message SQLContent {
    string sql = 1;
    repeated string columns = 2;
    }

  message Content {
    repeated SQLContent sql_content = 1;
  }

  map<int32, Content> content = 1;
    optional string error = 2;
}
```

## Key Capabilities

### Dependency Resolution

The service analyzes SQL expressions to identify dependencies and creates a proper execution order:

```text
Example Dependencies:
column_c = column_a + column_b  # Depends on column_a and column_b
column_d = column_c * 2         # Depends on column_c
```

**Execution Order**:

1. `column_a` and `column_b` (independent)
2. `column_c` (depends on a and b)
3. `column_d` (depends on c)

### SQL Statement Types

#### CREATE TABLE Statements

Generates complete table creation statements with:

- Column definitions
- Data types
- Constraints (PRIMARY KEY, NOT NULL, etc.)
- Generated columns (calculated fields)

#### ALTER TABLE Statements for Dependent Columns

Creates additional statements for columns with dependencies:

- `ALTER TABLE ... ADD COLUMN IF NOT EXISTS ...`
- `GENERATED ALWAYS AS (<expression>) STORED`
- One statement per dependent column, grouped by dependency level

### Column Type Support

| SQL Type | Description | Example |
| ---------- | ------------- | --------- |
| `INTEGER` | Whole numbers | `42`, `-10` |
| `NUMERIC` | Decimal numbers | `3.14`, `99.99` |
| `TEXT` | String values | `'John Doe'`, `'Sample Text'` |
| `BOOLEAN` | True/false values | `TRUE`, `FALSE` |
| `DATE` | Date values | `'2023-01-01'` |
| `TIMESTAMP` | Date and time | `'2023-01-01 12:00:00'` |

### Expression Types

#### Simple Columns

```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    age INTEGER
);
```

#### Calculated Columns

```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    birth_year INTEGER,
    current_year INTEGER,
    age INTEGER GENERATED ALWAYS AS (current_year - birth_year) STORED
);
```

#### Complex Expressions

```sql
CREATE TABLE users (
    salary NUMERIC,
    bonus NUMERIC,
    is_eligible BOOLEAN GENERATED ALWAYS AS (salary > 50000) STORED,
    total_compensation NUMERIC GENERATED ALWAYS AS (salary + bonus) STORED
);
```

## Installation

### Prerequisites

- Python 3.12.10
- uv (package manager)

### Setup

1. Install dependencies:

   ```bash
   uv sync
   ```

2. Configure environment:

   ```bash
   cp ../.env.example .env
   # Edit .env with your configuration
   ```

3. Start the service:

   ```bash
   uv run python src/server.py
   ```

## Configuration

Environment variables (see `.env.example`):

```env
# SQL Builder Configuration
SQL_BUILDER_HOST="localhost"
SQL_BUILDER_PORT="50054"
SQL_BUILDER_DEBUG=True
```

## Development

### Project Structure

```text
sql-builder/
├── src/
│   ├── server.py                    # gRPC server setup
│   ├── client.py                    # Test client
│   ├── core/
│   │   └── config.py                # Configuration management
│   ├── handlers/
│   │   └── sql_builder.py           # Request handling logic
│   ├── services/
│   │   ├── sql_builder.py           # Main service logic
│   │   ├── create_graph.py          # Dependency analysis
│   │   ├── builder.py               # SQL statement construction
│   │   └── utils.py                 # Graph utility functions
│   └── utils/
│       ├── logger.py                # Logger configuration
│       └── watch_files.py           # Debug file watcher
├── tests/                           # Test files
│   ├── services/
│   ├── test_server.py
│   └── conftest.py
├── scripts/                         # Utility scripts
├── pyproject.toml                   # Project configuration
├── Dockerfile                       # Container configuration
└── README.md                        # This file
```

### Key Components

#### Main Service (`services/sql_builder.py`)

The entry point that orchestrates the SQL building process:

```python
def build_sql(request_data):
    # 1. Parse input data
    # 2. Analyze dependencies
    # 3. Build dependency graph
    # 4. Detect cyclic dependencies
    # 5. Generate SQL statements by dependency level
    # 6. Return structured response
```

#### Dependency Graph Builder (`services/create_graph.py`)

Analyzes SQL expressions to identify column dependencies:

- **Graph Construction**: Builds dependency graphs using igraph
- **AST Reference Extraction**: Resolves dependencies from `cell`, `function`, `binary-expression`, etc.
- **Edge Creation**: Adds directed edges from a column to referenced columns

#### Statement Builder (`services/builder.py`)

Constructs final SQL statements:

- **Level 0**: Assembles `CREATE TABLE IF NOT EXISTS`
- **Dependent Levels**: Builds `ALTER TABLE ... GENERATED ALWAYS AS (...) STORED`
- **Constraint Handling**: Preserves extras and removes `PRIMARY KEY` from generated columns

#### Graph Utilities (`services/utils.py`)

Utility helpers for dependency processing:

- **Cycle Detection**: Checks if graph is DAG
- **Priority Level Calculation**: Computes dependency depth per column
- **Connection Counters**: Incoming and outgoing edge helpers

### Error Handling

The service provides comprehensive error handling:

- **Circular Dependencies**: Detects and reports dependency cycles
- **Request Processing Errors**: Logs and propagates handler/server exceptions

## API Examples

### Simple Table Creation

**Input**:

```json
{
  "cols": {
    "id": {
      "type": "number",
      "sql": "1",
      "number_value": 1
    },
    "name": {
      "type": "text",
      "sql": "'John Doe'",
      "text_value": "John Doe"
    }
  },
  "dtypes": {
    "id": {"type": "INTEGER", "extra": "PRIMARY KEY"},
    "name": {"type": "TEXT", "extra": "NOT NULL"}
  },
  "table_name": "users"
}
```

**Output**:

```json
{
  "content": {
    "0": {
      "sql_content": [
        {
          "sql": "CREATE TABLE IF NOT EXISTS users (id INTEGER, name TEXT NOT NULL, CONSTRAINT users_pk PRIMARY KEY (id));",
          "columns": ["id", "name"]
        }
      ]
    }
  }
}
```

### Complex Dependencies

**Input**: Multiple interconnected calculated columns

**Output**: Properly ordered SQL statements ensuring dependencies are resolved in correct sequence.

## Testing

### Running Tests

Run all tests:

```bash
uv run pytest tests/ -v
```

Run specific test module:

```bash
uv run pytest tests/services/test_builder.py -v
uv run pytest tests/services/test_utils.py -v
uv run pytest tests/services/test_create_graph.py -v
```

Run with coverage report:

```bash
uv run pytest tests/ --cov=src --cov-report=term-missing --cov-report=html
```

### Test Structure

```text
tests/
├── services/
│   ├── test_builder.py           # SQL generation tests
│   ├── test_utils.py             # Graph utilities tests
│   ├── test_create_graph.py      # Dependency graph tests
│   └── test_sql_builder.py       # Orchestrator tests
├── test_server.py                # gRPC servicer tests
└── conftest.py                   # pytest configuration
```

### Key Test Patterns

#### Graph Dependency Tests

Tests validate:

- Single and multiple independent columns
- Linear dependency chains
- Diamond pattern dependencies (multiple paths)
- Cyclic dependency detection
- Complex nested expressions

#### SQL Generation Tests

Tests validate:

- **Level 0**: CREATE TABLE statements
- **Level N**: ALTER TABLE ADD COLUMN for dependent columns
- **PRIMARY KEY**: Only allowed in level 0
- **GENERATED ALWAYS AS STORED**: Syntax for calculated columns
- **Constraints**: UNIQUE, NOT NULL preservation

#### Priority Level Tests

Tests validate:

- Recursive depth calculation
- Cumulative priority over multiple dependency paths
- Level gap handling in SQL generation
- Order independence check

### Example Test

```python
# Excel input: col1, col2=col1, col3=col2 (linear chain)
def test_linear_chain_three_columns():
    cols = {
        "col1": {"type": "number", "value": 10, "sql": "10"},
        "col2": {"type": "cell", "column": "col1", "sql": "col1"},
        "col3": {"type": "cell", "column": "col2", "sql": "col2"},
    }
    
    response = sql_builder(cols, dtypes, "test_table")
    
    # Should have 3 levels (0, 1, 2)
    assert 0 in response["content"]
    assert 1 in response["content"]
    assert 2 in response["content"]
    assert response["error"] is None
```

## Dependencies

### Core Dependencies

- **proto-utils**: Shared proto types and serializers
- **asyncio**: Async server runtime
- **igraph**: Graph analysis for dependency resolution
- **pydantic-settings**: Configuration management
- **watchfiles**: Debug auto-reload support
- **py-async-grpc-prometheus**: Prometheus gRPC interceptor

### Dependency Analysis

The service uses igraph for:

- **Graph Construction**: Building dependency relationships
- **Cycle Detection**: Identifying circular dependencies
- **Priority/Level Calculation**: Ordering statements by dependency depth

## Monitoring and Logging

- **Debug Mode**: Detailed logging when `SQL_BUILDER_DEBUG=True`
- **Request Logging**: Logs incoming requests and generated SQL
- **Dependency Analysis**: Logs dependency resolution process
- **Error Tracking**: Comprehensive error reporting with context
- **Metrics Support**: Optional Prometheus interceptor and metrics HTTP endpoint
