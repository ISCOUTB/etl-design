# Application Core

This directory contains the core application code for the Typechecking ETL System. The application follows a modular architecture with clear separation of concerns across different layers.

## Architecture Overview

The application is structured using a layered architecture pattern:

```text
┌─────────────────────────────────────────────────────────────┐
│                        API Layer                            │
│  (FastAPI routes, request/response handling)                │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                    Controllers Layer                        │
│  (Business logic, validation orchestration)                 │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                     Services Layer                          │
│  (File processing, data transformation)                     │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                   Data Access Layer                         │
│  (Database connections, caching, messaging)                 │
└─────────────────────────────────────────────────────────────┘
```

## Directory Structure

```text
app/
├── api/                    # API layer - HTTP endpoints and routing
│   ├── main.py            # Main API router configuration
│   └── routes/            # API route definitions
│       ├── validation.py  # File validation endpoints
│       ├── schemas.py     # Schema management endpoints
│       ├── healthcheck.py # Health check endpoints
│       └── cache.py       # Cache management endpoints
├── controllers/           # Business logic layer
│   ├── validation.py      # Core validation logic
│   └── schemas.py         # Schema management logic
├── core/                  # Infrastructure and configuration
│   ├── config.py          # Application configuration
│   ├── database_mongo.py  # MongoDB connection and operations
│   ├── database_redis.py  # Redis connection and caching
│   └── database_sql.py    # SQL database operations (if used)
├── messaging/             # Message queue system
│   ├── connection.py      # RabbitMQ connection management
│   ├── connection_factory.py # Connection factory pattern
│   └── publishers.py      # Message publishers
├── schemas/               # Data models and type definitions
│   ├── api.py            # API request/response models
│   ├── controllers.py    # Controller data models
│   ├── messaging.py      # Message format definitions
│   ├── services.py       # Service layer models
│   └── workers.py        # Worker process models
├── services/              # Service layer - core business services
│   ├── file_processor.py # File reading and processing
│   └── healthcheck.py    # System health checks
├── workers/               # Background processing
│   ├── validation_workers.py # File validation workers
│   ├── schema_workers.py     # Schema processing workers
│   └── worker_manager.py     # Worker lifecycle management
└── main.py               # Application entry point
```

## Core Components

### API Layer (`api/`)

The API layer handles HTTP requests and responses using FastAPI:

- **Routes**: RESTful endpoints for validation, schema management, and system monitoring
- **Request/Response Models**: Pydantic models for data validation and serialization
- **Middleware**: CORS, authentication, and request logging
- **Error Handling**: Standardized error responses and exception handling

Key endpoints:

- `/validation/upload/{import_name}` - File validation
- `/schemas/upload/{import_name}` - Schema management
- `/healthcheck` - System health checks
- `/cache` - Cache statistics

### Controllers Layer (`controllers/`)

Contains the business logic and orchestrates operations across services:

- **Validation Controller**: Manages file validation workflows
- **Schema Controller**: Handles schema CRUD operations and versioning
- **Parallel Processing**: Implements multi-threaded validation logic
- **Error Handling**: Business-level error processing and recovery

### Services Layer (`services/`)

Provides reusable business services:

- **File Processor**: Handles CSV, XLSX, and XLS file reading using Polars
- **Health Check Service**: Monitors system component health

### Core Infrastructure (`core/`)

Manages system configuration and database connections:

- **Configuration**: Environment-based settings using Pydantic
- **Database Connections**: MongoDB, Redis, and SQL database clients
- **Connection Pooling**: Efficient database connection management
- **Settings Validation**: Type-safe configuration management

### Messaging System (`messaging/`)

Implements asynchronous message processing with RabbitMQ:

- **Connection Management**: Robust connection handling with reconnection logic
- **Publishers**: Message publishing for validation and schema operations
- **Message Serialization**: JSON-based message formatting
- **Queue Management**: Dynamic queue creation and management

### Data Models (`schemas/`)

Type-safe data models using Pydantic:

- **API Models**: Request/response schemas for HTTP endpoints
- **Domain Models**: Core business object definitions
- **Message Models**: Queue message format specifications
- **Validation Models**: Data validation result structures

### Workers (`workers/`)

Background processing components:

- **Validation Workers**: Process file validation requests asynchronously
- **Schema Workers**: Handle schema updates and migrations
- **Worker Manager**: Manages worker lifecycle and scaling

## Key Features

### File Processing

The system supports multiple spreadsheet formats:

```python
# Example: Processing different file types
from app.services.file_processor import FileProcessor

# Supports CSV, XLSX, XLS files
success, data, error = await FileProcessor.process_file(upload_file)
```

### Parallel Validation

Multi-threaded validation for performance:

```python
# Example: Parallel validation configuration
from app.controllers.validation import validate_file_against_schema

result = await validate_file_against_schema(
    file=upload_file,
    import_name="user_data",
    n_workers=4  # Configurable worker count
)
```

### Schema Management

Dynamic schema validation and versioning:

```python
# Example: Schema operations
from app.controllers.schemas import get_active_schema

schema = await get_active_schema("user_data")
```

### Caching Strategy

Redis-based caching for improved performance:

- **Result Caching**: Validation results cached by task ID
- **Schema Caching**: Active schemas cached for quick access
- **TTL Management**: Configurable cache expiration times

### Message Queue Integration

Asynchronous processing with RabbitMQ:

- **Validation Queue**: File validation requests
- **Schema Queue**: Schema update operations  
- **Result Publishing**: Validation results broadcast
- **Dead Letter Queues**: Failed message handling

## Configuration

### Environment Variables

Key configuration options:

```bash
# API Configuration
API_V1_STR="/api/v1"
CORS_ORIGINS="http://localhost:3000,http://localhost:8080"

# Performance Settings
MAX_WORKERS=4
CHUNK_SIZE=1000

# Database Connections
MONGO_HOST="localhost"
MONGO_PORT=27017
REDIS_HOST="localhost" 
REDIS_PORT=6379

# Message Queue
RABBITMQ_HOST="localhost"
RABBITMQ_PORT=5672
RABBITMQ_USER="guest"
RABBITMQ_PASSWORD="guest"
```

### Database Schema

MongoDB collections:

- `schemas`: Active JSON schemas
- `schema_releases`: Schema version history
- `validation_results`: Validation result cache

Redis keys:

- `task:{task_id}`: Validation task results
- `schema:{import_name}`: Cached schemas
- `import:{import_name}`: Import metadata

## Development Guidelines

### Adding New Endpoints

1. Define Pydantic models in `schemas/api.py`
2. Create route handler in `api/routes/`
3. Implement business logic in `controllers/`
4. Add services in `services/` if needed
5. Update tests

### Error Handling

Use standardized error responses:

```python
from fastapi import HTTPException
from app.schemas.api import ApiResponse

# Standard error response
raise HTTPException(400, "Validation failed")

# Structured API response
return ApiResponse(
    status="error",
    code=400,
    message="Validation failed",
    data={"errors": validation_errors}
)
```

### Logging

Use structured logging throughout:

```python
import logging

logger = logging.getLogger(__name__)
logger.info("Processing validation request", extra={
    "task_id": task_id,
    "import_name": import_name,
    "file_size": file_size
})
```

### Testing

- Unit tests for individual components
- Integration tests for API endpoints
- Performance benchmarks in `tests/`
- Mock external dependencies

## Performance Considerations

### Optimization Strategies

1. **Parallel Processing**: Configurable worker threads
2. **Chunked Processing**: Memory-efficient large file handling
3. **Caching**: Redis-based result and schema caching
4. **Connection Pooling**: Efficient database connections
5. **Async Operations**: Non-blocking I/O operations

### Memory Management

- Stream processing for large files
- Garbage collection optimization
- Connection pooling limits
- Cache size management

### Monitoring

- Health check endpoints
- Performance metrics collection
- Error rate monitoring
- Queue depth monitoring

## Extension Points

The architecture supports easy extension:

1. **New File Formats**: Add processors in `services/file_processor.py`
2. **Custom Validation Rules**: Extend validation logic in `controllers/`
3. **Additional Databases**: Add connections in `core/`
4. **New Message Types**: Define in `schemas/messaging.py`
5. **Worker Types**: Add new workers in `workers/`

## Troubleshooting

Common issues and solutions:

1. **Connection Issues**: Check database/queue connectivity
2. **Memory Issues**: Reduce worker count or chunk size
3. **Validation Errors**: Check schema format and data compatibility
4. **Performance Issues**: Monitor worker utilization and queue depth
