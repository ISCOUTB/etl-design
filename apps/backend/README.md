# ETL Design Backend

This directory contains the backend runtime for ETL Design: the core API, the validation workers, the parsing pipeline, and the database proxy service.

## Backend Layout

```text
backend/
├── api/            # Core API and orchestration
├── typechecking/   # RabbitMQ consumers for validation and insertion
└── parsers/        # Excel Reader + formula/DDL/SQL microservices
```

## Architecture Overview

The backend is a distributed system built around three communication styles:

```text
Browser / Client
   │
   ▼
API Service
   ├── PostgreSQL
   ├── RabbitMQ
   ├── Database Service (gRPC)
   └── Parsing Services (REST + gRPC)

RabbitMQ
   └── Typechecking workers

Database Service
   ├── MongoDB
   └── Redis
```

The backend supports two core workflows:

1. **Validation pipeline**: file upload, schema lookup, RabbitMQ publish, async validation, and status updates.
2. **Parsing pipeline**: spreadsheet ingestion, formula parsing, SQL expression generation, and final SQL assembly.

## Service Groups

### API Service

See [api/README.md](./api/README.md).

Current responsibilities:

- Authentication and user management.
- Project and schema management.
- Upload and task orchestration.
- Event callbacks for completed work.
- Health and metrics endpoints.

### Typechecking Service

See [typechecking/README.md](./typechecking/README.md).

Current responsibilities:

- Consume validation and insertion jobs from RabbitMQ.
- Validate spreadsheet data against JSON Schema.
- Update task state through the database proxy.
- Publish result messages for downstream processing.

### Parsing Services

See [parsers/README.md](./parsers/README.md).

Current responsibilities:

- Parse Excel formulas into ASTs.
- Convert ASTs into SQL expressions.
- Assemble complete DDL and SQL statements.

### Database Service

See [../connections/database/README.md](../connections/database/README.md).

Current responsibilities:

- Provide a unified gRPC proxy for MongoDB and Redis.
- Persist schema metadata and task state.
- Offer cache and task management operations to backend services.

## Data Flow

### Validation Flow

```text
Client -> API -> RabbitMQ -> Typechecking -> Database Service -> PostgreSQL/MongoDB/Redis
```

### Parsing Flow

```text
Client -> Excel Reader -> Formula Parser -> DDL Generator -> SQL Builder
```

The two flows are independent but can be used together by the API when a request requires both validation and SQL generation.

## Technology Stack

- **Python 3.12** for API, database proxy, and worker services.
- **Node.js 18+** for the Formula Parser.
- **FastAPI** for the API service.
- **gRPC** and **Protocol Buffers** for internal service contracts.
- **RabbitMQ** for asynchronous work distribution.
- **PostgreSQL**, **MongoDB**, and **Redis** for persisted application state.
- **Polars** for validation throughput in the worker layer.

## Configuration

Each service has its own `.env.example` file. Copy it to `.env` before running the service.

Key service ports are:

- API: `8000`
- Excel Reader: `8001`
- Formula Parser: `50052`
- DDL Generator: `50053`
- SQL Builder: `50054`
- Database Service: `50050`

## Quick Start

1. Start infrastructure services first: PostgreSQL, MongoDB, Redis, and RabbitMQ.
2. Start the Database Service.
3. Start the API Service.
4. Start the Typechecking Service.
5. Start the parsing services if you are working on the Excel-to-SQL pipeline.

See each service README for exact commands and environment variables.

## Monitoring

- API exposes health and metrics endpoints.
- Typechecking can expose an optional health endpoint.
- Parsing services expose service-specific health checks.
- Logs are stored per service under each service directory.

## Testing

- API: run the test suite from `api/`.
- Typechecking: run the test suite from `typechecking/`.
- Parsers: run the service-specific tests in `parsers/`.

## Documentation

- [API Service](./api/README.md)
- [Typechecking Service](./typechecking/README.md)
- [Parsing Services](./parsers/README.md)
- [Database Service](../connections/database/README.md)

## Development Notes

- Keep workflow diagrams in `docs/diagrams/` aligned with service behavior.
- Keep deployment references aligned with `iac/` and `.github/workflows/`.
