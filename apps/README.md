# Applications Directory

This directory contains the runtime services for ETL Design. The application layer is split into a small number of focused services rather than a monolithic backend.

## Runtime Map

```text
apps/
├── backend/
│   ├── api/            # Core API and orchestration
│   ├── parsers/        # Excel parsing pipeline
│   └── typechecking/   # RabbitMQ consumers for validation
├── connections/
│   └── database/       # gRPC proxy for MongoDB and Redis
└── web/                # Nuxt frontend
```

## Service Index

### Backend

- [API Service](./backend/api/README.md) - authentication, orchestration, uploads, tasks, and events.
- [Typechecking Service](./backend/typechecking/README.md) - Polars-based validation and schema workers.
- [Parsing Services](./backend/parsers/README.md) - Excel Reader, Formula Parser, DDL Generator, and SQL Builder.

### Infrastructure-facing Runtime

- [Database Service](./connections/database/README.md) - MongoDB and Redis proxy over gRPC.

### Frontend

- [Web App](./web) - Nuxt client for the platform.

## How to Navigate

1. Start with the root [README](../README.md) for the full system overview.
2. Use [backend/README.md](./backend/README.md) for runtime architecture and workflows.
3. Use the service README files when working on a specific component.

## Runtime Flows

Validation flow: API -> RabbitMQ -> Typechecking -> Database Service -> PostgreSQL/MongoDB/Redis

Parsing flow: Excel Reader -> Formula Parser -> DDL Generator -> SQL Builder

## Deployment Notes

- Infrastructure provisioning lives in `iac/`.
- Swarm deployment definitions live in `iac/swarm/`.
- GitHub Actions workflows live in `.github/workflows/`.

## Status Summary

| Service | State | Notes |
| ------- | ----- | ----- |
| API | Active | Core orchestration service |
| Typechecking | Active | RabbitMQ consumer pipeline |
| Database Service | Active | gRPC proxy for Redis and MongoDB |
| Excel Reader | Active | REST orchestrator for parsing |
| Formula Parser | Active | Node.js gRPC service |
| DDL Generator | Active | Python gRPC service |
| SQL Builder | Active | Python gRPC service |

## Related Documentation

- [Backend Architecture](./backend/README.md)
- [Database Service](./connections/database/README.md)
- [Parsing Services](./backend/parsers/README.md)
