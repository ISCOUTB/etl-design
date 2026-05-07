# ETL Design API Service

The API service is the core orchestrator of the backend. It exposes the REST interface used by the frontend and coordinates authentication, user management, projects, schemas, uploads, task tracking, cache access, and event callbacks.

## Architecture

```text
Client / Web App
    │
    ▼
API Service (FastAPI)
    ├── PostgreSQL for users, projects, and uploads
    ├── RabbitMQ for async validation and insertion jobs
    ├── Database Service (gRPC) for Redis and MongoDB
    └── Parsing Services for Excel-to-SQL workflows
```

The API is the entry point for the current validation pipeline and the main bridge between the frontend and backend services.

## Responsibilities

- Authenticate users and issue JWT tokens.
- Manage users, projects, and schema metadata.
- Register upload tasks and track their lifecycle.
- Publish validation and insertion jobs to RabbitMQ.
- Persist workflow state through PostgreSQL and the database proxy.
- Receive completion callbacks from background workers through the events route.
- Expose health and metrics endpoints.

## Registered Routes

### OpenAPI and Docs

- `GET /api/v1/openapi.json`
- `GET /docs`
- `GET /docs/oauth2-redirect`
- `GET /redoc`

### Health and Metrics

- `GET /api/v1/metrics`
- `GET /api/v1/healthcheck/`

### Authentication

- `POST /api/v1/auth/sign-in`
- `POST /api/v1/auth/sign-up`
- `GET /api/v1/auth/test-token`

### Cache

- `GET /api/v1/cache/`
- `DELETE /api/v1/cache/clear`

### Tasks

- `GET /api/v1/tasks/task/{task_id}`
- `GET /api/v1/tasks/project/{project_id}`

### Users

- `GET /api/v1/users/me`
- `GET /api/v1/users/search`
- `GET /api/v1/users/id/{user_id}`
- `GET /api/v1/users/search/{email}`
- `POST /api/v1/users/`
- `PATCH /api/v1/users/{user_id}`
- `DELETE /api/v1/users/{user_id}`
- `GET /api/v1/users/{user_id}/projects`
- `GET /api/v1/users/{user_id}/projects/{project_id}`

### Events

- `POST /api/v1/events/task-completed`

### Schemas

- `POST /api/v1/schemas/{project_id}`
- `GET /api/v1/schemas/{project_id}`
- `GET /api/v1/schemas/{project_id}/raw`
- `GET /api/v1/schemas/search/{project_id}`
- `DELETE /api/v1/schemas/{project_id}`

### Uploads

- `POST /api/v1/uploads/validate`
- `POST /api/v1/uploads/insert`
- `POST /api/v1/uploads/process`
- `POST /api/v1/uploads/table-excel`
- `POST /api/v1/uploads/table-json`

### Projects

- `GET /api/v1/projects/search`
- `GET /api/v1/projects/id/{project_id}`
- `POST /api/v1/projects/`
- `PATCH /api/v1/projects/{project_id}`
- `DELETE /api/v1/projects/{project_id}`
- `POST /api/v1/projects/{project_id}/users/invite`
- `POST /api/v1/projects/{project_id}/users`
- `DELETE /api/v1/projects/{project_id}/flush`
- `DELETE /api/v1/projects/{project_id}/users/{user_id}`
- `GET /api/v1/projects/{project_id}/users`
- `GET /api/v1/projects/{project_id}/users/{user_id}`

## Data Flow

### Validation Flow

```text
Client -> API -> PostgreSQL -> RabbitMQ -> Typechecking -> Database Service -> API -> Client
```

### Parsing Flow

```text
Client -> API -> Parsing Services -> SQL output
```

The validation flow is the most mature workflow in the repository. The parsing flow is available through the parser subsystem and can be composed with upload workflows when needed.

## Configuration

The service uses environment variables defined in `apps/backend/api/.env.example`.

Key values include:

- `SERVER_HOST`
- `SERVER_PORT`
- `API_V1_STR`
- `CORS_ORIGINS`
- `SERVER_DEBUG`
- `AUTH_INFO`
- `SECRET_KEY`
- `CREDENTIALS_SECRET_KEY`
- `CREDENTIALS_SIGN`
- `IDEMPOTENCY_TTL_DEFAULT_SECONDS`
- `IDEMPOTENCY_TTL_RETRY_DELAY_SECONDS`
- `IDEMPOTENCY_TTL_PUBLISHED_SECONDS`
- `FIRST_SUPERUSER_NAME`
- `FIRST_SUPERUSER_EMAIL`
- `FIRST_SUPERUSER_PASSWORD`
- `POSTGRES_HOST`
- `POSTGRES_PORT`
- `DATABASE_CONNECTION_HOST`
- `DATABASE_CONNECTION_PORT`
- `RABBITMQ_HOST`
- `RABBITMQ_PORT`
- `RABBITMQ_VHOST`
- `RABBITMQ_USER`
- `RABBITMQ_PASSWORD`
- `RABBITMQ_EXCHANGE`
- `RABBITMQ_QUEUE_INSERTION`
- `RABBITMQ_QUEUE_VALIDATIONS`
- `RABBITMQ_QUEUE_RESULTS`
- `RABBITMQ_ROUTING_KEY_INSERTION`
- `RABBITMQ_ROUTING_KEY_VALIDATIONS`
- `RABBITMQ_ROUTING_KEY_RESULTS`
- `WORKER_CONCURRENCY`
- `WORKER_PREFETCH_COUNT`
- `RABBITMQ_MAX_RETRIES`
- `RABBITMQ_RETRY_DELAY_SECONDS`
- `RABBITMQ_BACKOFF_MULTIPLIER`
- `DATABASE_MAX_RETRIES`
- `DATABASE_RETRY_DELAY_SECONDS`
- `DATABASE_BACKOFF_MULTIPLIER`
- `DATABASE_TRACE_CONTEXT_ENABLED`
- `EXCEL_READER_HOST`
- `EXCEL_READER_PORT`
- `EXCEL_READER_TIMEOUT_SECONDS`
- `OTEL_SERVICE_NAME`
- `OTEL_SERVICE_VERSION`
- `OTEL_TRACING_ENABLED`
- `OTEL_EXPORTER_OTLP_ENDPOINT`

## Development

### Prerequisites

- Python 3.12+
- PostgreSQL 18+
- RabbitMQ 4.0+
- Database Service running

### Run Locally

```bash
uv sync
uv run bash scripts/prestart.sh
uv run alembic upgrade head
uv run python -m src.initial_data
uv run python -m src.main
```

### Tests

```bash
pytest
pytest --cov=src --cov-report=html
```

## Project Structure

```text
api/
├── scripts/
│   └── prestart.sh   # Local bootstrap script
├── src/
│   ├── alembic/        # Database migrations
│   ├── api/            # FastAPI routes and dependencies
│   ├── core/           # Configuration and database setup
│   ├── exceptions/     # Domain and HTTP exceptions
│   ├── models/         # SQLAlchemy models
│   ├── repositories/   # Persistence abstractions
│   ├── schemas/        # Pydantic schemas
│   ├── services/       # Business logic layer
│   ├── utils/          # Shared helpers
│   ├── initial_data.py  # Initial data bootstrap
│   ├── main.py         # Application entry point
│   └── sql_prestart.py # Prestart SQL/bootstrap helpers
├── tests/
│   ├── models/
│   ├── repositories/
│   ├── routes/
│   ├── schemas/
│   ├── services/
│   └── utils/
├── alembic.ini
├── Dockerfile
├── get_token.py
├── moon.yml
├── pyproject.toml
├── README.md
└── uv.lock
```

## Related Documentation

- [Backend Overview](../README.md)
- [Typechecking Service](../typechecking/README.md)
- [Parsing Services](../parsers/README.md)
- [Database Service](../../connections/database/README.md)
