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

Background processing components with enhanced capabilities:

#### Schema Workers (`workers/schema_workers.py`)

Handles schema management operations:

```python
# Schema upload processing
def _update_schema(message: SchemaMessage) -> SchemaUpdated:
    """
    Processes schema upload requests:
    - Creates schemas from raw or processed format
    - Performs schema validation using Draft7Validator
    - Updates active schemas with versioning
    - Handles rollback operations for schema removal
    - Updates Redis task status throughout processing
    """
```

**Key Features:**

- **Schema Creation**: Support for both raw and processed schema formats
- **Validation**: JSON Schema Draft 7 validation before storage
- **Versioning**: Maintains schema history with rollback capabilities
- **Status Updates**: Real-time progress updates via Redis
- **Error Handling**: Comprehensive error catching with detailed logging
- **Message ACK**: Proper message acknowledgment for reliable processing

#### Validation Workers (`workers/validation_workers.py`)

Processes file validation requests:

```python
# File validation processing
async def _validate_file(message: ValidationMessage) -> DataValidated:
    """
    Processes file validation requests:
    - Converts hex-encoded file data to binary format
    - Creates UploadFile objects for processing
    - Validates against specified schemas
    - Returns detailed validation summaries
    - Updates task progress in Redis
    """
```

**Key Features:**

- **File Format Support**: CSV, XLSX, XLS file processing
- **Data Conversion**: Hex-to-binary conversion for safe transmission
- **Async Processing**: Non-blocking validation operations
- **Progress Tracking**: Real-time validation progress updates
- **Result Publishing**: Structured validation results with error details
- **Resource Management**: Efficient memory usage for large files

#### Worker Manager (`workers/worker_manager.py`)

Manages worker lifecycle and scaling:

- **Worker Pools**: Manages multiple worker instances
- **Health Monitoring**: Tracks worker health and performance
- **Auto Scaling**: Dynamic worker scaling based on queue depth
- **Graceful Shutdown**: Proper worker termination handling

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
# RabbitMQ configuration
RABBITMQ_HOST="localhost"
RABBITMQ_PORT="5672"
RABBITMQ_VHOST="/"
RABBITMQ_USER="guest"
RABBITMQ_PASSWORD="guest"

# Worker configuration
MAX_WORKERS=8
WORKER_CONCURRENCY=4
WORKER_PREFETCH_COUNT=1

# API configuration
API_V1_STR="/api/v1"
CORS_ORIGINS="*"

# MongoDB configuration
MONGO_PORT="27017"
MONGO_HOST="localhost"
MONGO_INITDB_ROOT_USERNAME="admin"
MONGO_INITDB_ROOT_PASSWORD="admin"
MONGO_DB="json_schemas"
MONGO_COLLECTION="schemas"

# Redis configuration
REDIS_PASSWORD="root"
REDIS_PORT="6379"
REDIS_HOST="localhost"
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

## Recent Updates

### API Layer Enhancements

#### Schema Management Routes (`api/routes/schemas.py`)

- **Upload Schema Endpoint**: New `POST /upload/{import_name}` endpoint with advanced features:
  - Support for both raw and processed schema formats
  - Cache-first strategy with `new` parameter to bypass caching
  - Asynchronous processing with task ID tracking
  - Automatic schema comparison to prevent duplicate uploads
  
- **Schema Status Tracking**: Enhanced `GET /status` endpoint:
  - Query by task_id or import_name
  - Returns detailed task information and progress
  - Support for multiple task tracking per import_name
  
- **Schema Removal**: New `DELETE /remove/{import_name}` endpoint:
  - Safe schema removal with version rollback
  - Asynchronous processing with result tracking
  - Maintains schema history for rollback operations

#### Validation Routes (`api/routes/validation.py`)

- **File Upload Processing**: Enhanced `POST /upload/{import_name}` endpoint:
  - Multi-format file support (CSV, XLSX, XLS)
  - Rich metadata extraction (filename, content_type, size)
  - Hex-encoded file data for reliable transmission
  - Asynchronous validation with progress tracking
  
- **Validation Status**: Improved `GET /status` endpoint:
  - Real-time validation progress monitoring
  - Task lookup by task_id or import_name
  - Comprehensive error handling and reporting

### Controller Layer Improvements

#### Schema Controller (`controllers/schemas.py`)

- **Schema Comparison Logic**: Enhanced `compare_schemas()` function for accurate equality checking
- **Data Validation**: Improved `validate_data_chunk()` with comprehensive error reporting
- **Active Schema Management**: Robust `get_active_schema()` and `save_schema()` functions
- **Schema Versioning**: New `remove_schema()` function with rollback capabilities
- **Raw Schema Processing**: Enhanced `create_schema()` with support for raw and processed formats

### Infrastructure Layer Updates

#### Redis Integration (`core/database_redis.py`)

- **Advanced Task Management**: Comprehensive task tracking system:
  - Task status updates with field-level granularity
  - Import name indexing for efficient task lookup
  - Multi-task support per import name
  - Cache expiration and cleanup mechanisms
  
- **Enhanced Data Structures**: Optimized Redis operations:
  - Hash-based task storage for atomic updates
  - Set-based import name indexing
  - JSON serialization for complex data types
  - Connection pooling and error handling

#### Messaging System (`messaging/publishers.py`)

- **ValidationPublisher Enhancements**:
  - Detailed message documentation and schemas
  - Priority-based message queuing
  - Hex-encoded file data transmission
  - Comprehensive metadata support
  - UUID-based task identification
  
- **Message Formatting**: Standardized message structure:
  - ISO timestamp formatting
  - Persistent delivery mode
  - Priority-based routing
  - Structured error handling

### Schema Layer Updates

#### Messaging Schemas (`schemas/messaging.py`)

- **TypedDict Implementation**: Strongly typed message contracts:
  - `ValidationMessage` schema for file validation requests
  - `SchemaMessage` schema for schema update operations
  - Literal types for task classification
  - Comprehensive field documentation
  
- **Message Standards**: Defined message structure standards:
  - Unique task identification
  - Timestamp consistency
  - Priority system implementation
  - Metadata standardization

### Worker Layer Enhancements

#### Schema Workers (`workers/schema_workers.py`)

- **Enhanced Processing Pipeline**:
  - Improved schema creation and validation logic
  - Real-time Redis status updates
  - Comprehensive error handling and logging
  - Proper message acknowledgment patterns
  
- **Connection Management**: Thread-safe RabbitMQ operations:
  - Connection factory integration
  - Graceful shutdown handling
  - QoS configuration for optimal throughput
  - Error recovery mechanisms

#### Validation Workers (`workers/validation_workers.py`)

- **File Processing Improvements**:
  - Enhanced hex-to-binary conversion
  - UploadFile object creation from binary data
  - Asynchronous validation processing
  - Structured result publishing
  
- **Progress Tracking**: Real-time validation monitoring:
  - Step-by-step progress updates
  - Detailed error reporting
  - Result summarization
  - Cache integration for status persistence

### Performance Optimizations

- **Caching Strategy**: Multi-level caching with Redis
- **Async Processing**: Non-blocking operations throughout the pipeline
- **Connection Pooling**: Efficient resource utilization
- **Message Queuing**: Priority-based task distribution
- **Memory Management**: Optimized data structures and garbage collection

### API Consistency

- **Standardized Responses**: Consistent ApiResponse format across all endpoints
- **Error Handling**: Uniform error response structure
- **Status Codes**: HTTP status code standardization
- **Documentation**: Comprehensive endpoint documentation with examples

### Message Queue System

#### Enhanced Message Schemas (`schemas/messaging.py`)

The system now uses strongly typed message contracts for reliable communication:

##### ValidationMessage Schema

```python
class ValidationMessage(TypedDict):
    """Message format for file validation requests"""
    id: str                    # Unique task identifier (UUID)
    task: ValidationTasks      # Task type: "sample_validation"
    timestamp: str             # ISO format timestamp
    file_data: str            # Hex-encoded binary file content
    import_name: str          # Schema identifier for validation
    metadata: dict            # File metadata (filename, content_type, size)
    priority: int             # Message priority (1-10)
```

**Usage Example:**

```python
# Publishing a validation request
task_id = publisher.publish_validation_request(
    file_data=file_content,
    import_name="user_schema",
    metadata={
        "filename": "users.csv",
        "content_type": "text/csv",
        "size": 1024,
        "priority": 5
    },
    task="sample_validation"
)
```

##### SchemaMessage Schema

```python
class SchemaMessage(TypedDict):
    """Message format for schema update requests"""
    id: str                    # Unique task identifier (UUID)
    task: SchemasTasks        # Task type: "upload_schema" | "remove_schema"
    timestamp: str             # ISO format timestamp
    schema: dict              # JSON schema definition
    import_name: str          # Schema identifier
    raw: bool                 # Raw format flag
```

**Usage Example:**

```python
# Publishing a schema update
task_id = publisher.publish_schema_update(
    schema={
        "type": "object",
        "properties": {"name": {"type": "string"}},
        "required": ["name"]
    },
    import_name="person_schema",
    raw=False,
    task="upload_schema"
)
```

#### Enhanced Publishers (`messaging/publishers.py`)

##### ValidationPublisher

- **Hex Encoding**: File data converted to hexadecimal for safe JSON transmission
- **Priority Queuing**: Message priority system for processing order optimization
- **Persistent Delivery**: Messages marked as persistent for reliability
- **UUID Generation**: Unique task identifiers for tracking
- **Routing Keys**: Optimized message routing (`validation.request`)

##### Message Publishing Flow

```python
# Internal message creation and publishing
message: ValidationMessage = {
    "id": str(uuid.uuid4()),
    "task": task,
    "timestamp": datetime.now().isoformat(),
    "file_data": file_data.hex(),  # Hex encoding for safe transmission
    "import_name": import_name,
    "metadata": metadata,
    "priority": metadata.get("priority", 5),
}

# Publish with properties
channel.basic_publish(
    exchange="typechecking.exchange",
    routing_key="validation.request",
    body=json.dumps(message),
    properties=pika.BasicProperties(
        message_id=task_id,
        timestamp=int(datetime.now().timestamp()),
        delivery_mode=pika.DeliveryMode.Persistent,
        priority=message["priority"],
    ),
)
```

#### Queue Infrastructure

- **Validation Queue**: `typechecking.validation.queue` for file validation requests
- **Schema Queue**: `typechecking.schema.queue` for schema management operations
- **Exchange**: `typechecking.exchange` with topic routing
- **Dead Letter Queues**: Automatic failure handling and message requeuing
- **Priority Support**: Message priority levels for processing optimization

#### Connection Management (`messaging/connection_factory.py`)

- **Thread Safety**: Separate connections per worker thread
- **Connection Pooling**: Efficient resource utilization
- **Automatic Reconnection**: Robust connection recovery
- **Graceful Shutdown**: Proper connection cleanup
