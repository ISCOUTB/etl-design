# Typechecking Service

The Typechecking service is the asynchronous worker subsystem of ETL Design. It validates spreadsheet data against JSON schemas, coordinates insertion work when validation succeeds, and reports task completion back to the API.

## Architecture

```text
API Service
    ├── publishes validation jobs to RabbitMQ
    ├── receives completion callbacks from ResultWorker
    └── stores task state in PostgreSQL

RabbitMQ
    ├── typechecking.validations.queue
    ├── typechecking.insertion.queue
    └── typechecking.results.queue

Typechecking Service
    ├── ValidationWorker
    ├── InsertionWorker
    ├── ResultWorker
    ├── Database gRPC client
    └── optional minimal health server

Database Service
    ├── Redis for task state cache
    └── MongoDB for schema persistence
```

The worker layer treats the database proxy as the source of truth for task state. Redis is used as a cache, MongoDB stores schemas and persistent metadata, and RabbitMQ carries the work queue.

## Responsibilities

- Consume validation jobs from RabbitMQ.
- Validate spreadsheet files against the active JSON schema.
- Publish insertion jobs when validation succeeds and insertion is requested.
- Execute insertion work by calling the Excel Reader to generate SQL.
- Notify the API when a task is completed or failed.
- Keep task state idempotent and recoverable through the DB proxy.
- Expose an optional minimal HTTP health server.

## Worker Model

### ValidationWorker

- Consumes messages from `RABBITMQ_QUEUE_VALIDATIONS`.
- Reads the uploaded file, normalizes the schema, and validates rows in parallel.
- Updates task status through the DB proxy.
- Publishes validation results to `RABBITMQ_QUEUE_RESULTS`.
- Publishes insertion work to `RABBITMQ_QUEUE_INSERTION` when the task requires insertion.

### InsertionWorker

- Consumes messages from `RABBITMQ_QUEUE_INSERTION`.
- Calls the Excel Reader insertion endpoint through `EXCEL_READER_INSERT_URL`.
- Executes SQL against the target database using the project credentials carried in the task.
- Updates task status and publishes the final result message.

### ResultWorker

- Consumes messages from `RABBITMQ_QUEUE_RESULTS`.
- Checks the task state in the DB proxy before acting.
- Posts completion payloads to `API_REQUEST_URL`.
- Marks the task as completed once the API acknowledges the callback.

## Data Flow

### Validation Path

```text
API -> RabbitMQ validation queue -> ValidationWorker -> DB Proxy -> RabbitMQ results queue -> ResultWorker -> API
```

### Validation + Insertion Path

```text
API -> RabbitMQ validation queue -> ValidationWorker -> RabbitMQ insertion queue -> InsertionWorker -> Excel Reader / target DB -> RabbitMQ results queue -> ResultWorker -> API
```

### Idempotency Rules

- `set_task_id()` creates the first task record in the database.
- Later state transitions depend on that record existing.
- If the DB proxy is unavailable, the worker fails fast and the orchestrator restarts the process.
- If the task already finished, workers skip duplicate work.

## Configuration

The service reads its configuration from `apps/backend/typechecking/.env.example`.

### Database Proxy

- `DATABASE_CONNECTION_HOST`
- `DATABASE_CONNECTION_PORT`
- `DATABASE_MAX_RETRIES`
- `DATABASE_RETRY_DELAY_SECONDS`
- `DATABASE_BACKOFF_MULTIPLIER`

### RabbitMQ

- `RABBITMQ_HOST`
- `RABBITMQ_PORT`
- `RABBITMQ_VHOST`
- `RABBITMQ_USER`
- `RABBITMQ_PASSWORD`
- `RABBITMQ_MAX_RETRIES`
- `RABBITMQ_RETRY_DELAY_SECONDS`
- `RABBITMQ_BACKOFF_MULTIPLIER`
- `RABBITMQ_THRESHOLD_SECONDS`
- `RABBITMQ_EXCHANGE`
- `RABBITMQ_QUEUE_INSERTION`
- `RABBITMQ_QUEUE_VALIDATIONS`
- `RABBITMQ_QUEUE_RESULTS`
- `RABBITMQ_ROUTING_KEY_INSERTION`
- `RABBITMQ_ROUTING_KEY_VALIDATIONS`
- `RABBITMQ_ROUTING_KEY_RESULTS`
- `RABBITMQ_PUBLISHERS_ROUTING_KEY_INSERTION`
- `RABBITMQ_PUBLISHERS_ROUTING_KEY_VALIDATIONS`
- `RABBITMQ_PUBLISHERS_ROUTING_KEY_RESULTS`
- `RABBITMQ_QUEUE_TYPE_INSERTION`
- `RABBITMQ_QUEUE_TYPE_VALIDATIONS`
- `RABBITMQ_QUEUE_TYPE_RESULTS`

### Worker Runtime

- `MAX_WORKERS`
- `WORKER_PREFETCH_COUNT`

### API and Excel Reader

- `API_REQUEST_URL`
- `API_TIMEOUT_SECONDS`
- `EXCEL_READER_HOST`
- `EXCEL_READER_PORT`
- `EXCEL_READER_TIMEOUT_SECONDS`

### Minimal Health Server

- `MINIMAL_SERVER_HOST`
- `MINIMAL_SERVER_PORT`
- `MINIMAL_SERVER_DEBUG`

### OpenTelemetry

- `OTEL_SERVICE_NAME`
- `OTEL_SERVICE_VERSION`
- `OTEL_TRACING_ENABLED`
- `OTEL_EXPORTER_OTLP_ENDPOINT`
- `OTEL_EXPORTER_OTLP_TRACES_ENDPOINT`

## Development

### Prerequisites

- Python 3.12.10
- RabbitMQ 4.0+
- Database Service running
- API Service running
- Excel Reader available for insertion jobs

### Install

```bash
uv sync
```

### Run the worker manager

```bash
uv run python -m src.main
```

### Run the minimal health server

```bash
uv run python -m src.minimal_server
```

### Tests

```bash
uv run pytest
uv run pytest --cov=src --cov-report=html
uv run pytest -n auto
```

## Project Structure

```text
typechecking/
├── src/
│   ├── core/
│   │   ├── config.py
│   │   ├── database_client.py
│   │   └── events.py
│   ├── handlers/
│   │   ├── schemas.py
│   │   └── validation.py
│   ├── schemas/
│   │   ├── healthcheck.py
│   │   ├── handlers.py
│   │   └── workers.py
│   ├── services/
│   │   ├── file_processor.py
│   │   └── healthcheck.py
│   ├── utils/
│   ├── workers/
│   │   ├── insertion.py
│   │   ├── results.py
│   │   ├── utils.py
│   │   └── validation.py
│   ├── main.py
│   └── minimal_server.py
├── tests/
├── logs/
├── Dockerfile
├── moon.yml
├── pyproject.toml
├── README.md
└── supervisord.conf
```

## Notes

- `src.main` starts the worker manager with validation, insertion, and result workers.
- `src.minimal_server` exposes `/`, `/health`, and `/metrics` for lightweight monitoring.
- The service does not use a separate schema worker anymore.
- Validation is schema-driven, but schema persistence is handled by the DB proxy rather than by a dedicated worker.

## Related Documentation

- [Backend Overview](../README.md)
- [API Service](../api/README.md)
- [Parsing Services](../parsers/README.md)
- [Database Service](../../connections/database/README.md)
