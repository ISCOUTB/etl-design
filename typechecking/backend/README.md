# Typechecking ETL System

A high-performance data validation system designed for ETL processes that validates spreadsheet files (CSV, XLSX, XLS) against JSON schemas using parallel processing and message queuing.

## Overview

This system provides a robust, scalable solution for validating large datasets in spreadsheet formats. It uses a microservices architecture with RabbitMQ for asynchronous processing, MongoDB for schema storage, Redis for caching, and FastAPI for the REST API interface.

## Key Features

- **Multi-format Support**: Validates CSV, XLSX, and XLS files
- **Parallel Processing**: Uses multi-threading for high-performance validation
- **Asynchronous Processing**: RabbitMQ-based message queuing for scalable operations
- **Schema Management**: Dynamic JSON schema validation and version control
- **Caching**: Redis-based caching for improved performance
- **RESTful API**: FastAPI-based endpoints for easy integration
- **Docker Support**: Containerized deployment with Docker Compose
- **Performance Testing**: Built-in benchmarking and performance analysis tools

## Architecture

```text
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   FastAPI       │────▶│   RabbitMQ      │────▶│   Workers       │
│   Web Server    │     │   Message Queue │     │   (Validation)  │
└─────────────────┘     └─────────────────┘     └─────────────────┘
         │                                                │
         ▼                                                ▼
┌─────────────────┐                              ┌─────────────────┐
│   Redis         │                              │   MongoDB       │
│   (Caching)     │                              │   (Schemas)     │
└─────────────────┘                              └─────────────────┘
```

## Prerequisites

- Python 3.12+
- Docker and Docker Compose
- MongoDB
- Redis
- RabbitMQ

## Quick Start

### Using Docker Compose (Recommended)

1. Clone the repository:

```bash
git clone https://github.com/ISCOUTB/etl-design.git
cd typechecking
```

2. Edit environment file.

```bash
cp .env.example .env
```

3. Start the services:

```bash
cd docker
docker-compose up -d
```

### Manual Installation

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Start the API server:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

3. Start workers:

```bash
python -m app.workers.worker_manager
```

## API Endpoints

### Validation

- `POST /api/v1/validation/upload/{import_name}` - Upload and validate a file
- `GET /api/v1/validation/status/{task_id}` - Check validation status

### Schema Management

- `POST /api/v1/schemas/upload/{import_name}` - Upload a JSON schema
- `GET /api/v1/schemas/status` - Get active schema

### System Health

- `GET /api/v1/healthcheck` - Health check of all connections
- `GET /api/v1/healthcheck/simple` - Checks if api is running

### Cache Monitoring

- `GET /api/v1/cache` - Get all cache keys and values
- `DELETE /api/v1/cache/clear` - Clear all cache

## Usage Examples

### Validate a CSV file

```bash
curl -X POST "http://localhost:8000/api/v1/validation/upload/users_data" \
     -H "Content-Type: multipart/form-data" \
     -F "spreadsheet_file=@users.csv"
```

### Upload a JSON schema

```bash
curl -X POST "http://localhost:8000/api/v1/schemas/upload/users_data" \
     -H "Content-Type: application/json" \
     -d @schema.json
```

## Configuration

The system uses environment variables for configuration. Key settings include:

- `API_V1_STR`: API version prefix
- `MAX_WORKERS`: Number of parallel validation workers
- `RABBITMQ_*`: RabbitMQ connection settings
- `MONGO_*`: MongoDB connection settings
- `REDIS_*`: Redis connection settings
- `CORS_ORIGINS`: Allowed CORS origins

## Performance

The system is optimized for high-performance validation:

- **Parallel Processing**: Multi-threaded validation with configurable worker counts
- **Chunked Processing**: Large files are processed in chunks for memory efficiency
- **Asynchronous Architecture**: Non-blocking operations through message queuing
- **Caching**: Redis caching reduces redundant operations

### Performance Benchmarks

Based on testing with various file sizes:

- **Small files** (1K rows, 100 columns): ~4.5 seconds
- **Medium files** (5K rows, 100 columns): ~23 seconds
- **Large files** (10K rows, 100 columns): ~45 seconds

Performance scales linearly with data size and can be improved by increasing worker counts.

## Development

### Project Structure

```console
typechecking/
├── app/                    # Main application code
├── docker/                 # Docker configuration
├── scripts/                # Deployment scripts
├── static/                 # Sample data files
├── tests/                  # Test files and performance benchmarks
├── requirements.txt        # Python dependencies
└── README.md               # This file
```

### Running Tests

```bash
# Run validation tests
python tests/example_validation_usage.py

# Run performance benchmarks
jupyter notebook tests/testing_typechecking.ipynb
```

### Performance Testing

The `tests/` directory contains comprehensive performance testing tools:

```bash
# Generate test data and run benchmarks
python tests/testing_typechecking.py
```

## Deployment

### Production Deployment

1. Use the provided Docker Compose configuration
2. Configure environment variables for production
3. Set up monitoring and logging
4. Configure load balancing if needed

### Scaling

- **Horizontal Scaling**: Add more worker instances
- **Vertical Scaling**: Increase worker thread counts
- **Database Scaling**: Use MongoDB replica sets
- **Cache Scaling**: Use Redis clustering

## Recent Updates

### API Endpoints Enhancements

#### Schema Management API (`api/v1/schemas`)

- **New Upload Endpoint**: `POST /schemas/upload/{import_name}` - Upload and manage JSON schemas with versioning support
  - Parameters: `raw` (boolean) for raw schema processing, `new` (boolean) to force new task creation
  - Returns task ID for asynchronous processing
  - Implements schema comparison to avoid duplicate uploads
- **Status Tracking**: `GET /schemas/status` - Track schema upload tasks by task_id or import_name
- **Schema Removal**: `DELETE /schemas/remove/{import_name}` - Remove schemas with rollback to previous versions
- **Caching Integration**: Redis-based task caching with import_name indexing

#### Validation API (`api/v1/validation`)

- **File Upload Endpoint**: `POST /validation/upload/{import_name}` - Validate spreadsheet files against schemas
  - Support for CSV, XLSX, and XLS file formats
  - Asynchronous processing with task tracking
  - File metadata extraction (filename, content_type, size)
- **Status Monitoring**: `GET /validation/status` - Monitor validation progress by task_id or import_name
- **Cache Optimization**: Improved response caching with import_name grouping

### Worker System Improvements

#### Schema Workers

- **Enhanced Task Processing**: Improved schema creation and validation logic
- **Better Error Handling**: Comprehensive error catching with detailed logging
- **Redis Integration**: Real-time task status updates throughout processing pipeline
- **Version Control**: Support for schema versioning with rollback capabilities
- **Message Acknowledgment**: Reliable message processing with proper ACK/NACK handling

#### Validation Workers

- **File Processing Pipeline**: Enhanced file data conversion from hex to binary format
- **Async Processing**: Improved asynchronous file validation with better resource management
- **Progress Tracking**: Real-time validation progress updates via Redis
- **Result Publishing**: Structured validation results with detailed summaries

### Messaging System Updates

#### Message Schemas

- **Typed Message Contracts**: New TypedDict schemas for ValidationMessage and SchemaMessage
- **Task Classification**: Defined ValidationTasks and SchemasTasks literal types
- **Priority Support**: Message priority system for queue processing optimization
- **Metadata Enhancement**: Rich metadata support for better processing context

#### Publishers

- **Validation Publisher**: Enhanced with detailed message documentation and error handling
- **Schema Publisher**: Improved schema update publishing with task type support
- **Message Formatting**: Standardized message structure with UUID generation and timestamps
- **Routing Keys**: Optimized routing for better message distribution

### Infrastructure Enhancements

#### Redis Integration

- **Task Management**: Comprehensive task ID tracking and status management
- **Import Name Indexing**: Efficient task lookup by import_name
- **Cache Operations**: Advanced caching with TTL and key pattern management
- **Data Structures**: Optimized use of Redis hashes and sets for task relationships

#### Database Operations

- **Schema Storage**: Enhanced MongoDB operations for schema versioning
- **Comparison Logic**: Improved schema comparison for duplicate detection
- **Rollback Support**: Schema removal with automatic rollback to previous versions
- **Result Tracking**: Better database result handling and status reporting

## Summary of Recent Changes

The Typechecking ETL System has undergone significant enhancements across all layers of the architecture. These improvements focus on robustness, scalability, and developer experience.

### 🚀 Key Improvements

**API Layer:**

- Enhanced schema management with versioning and rollback capabilities
- Improved file validation endpoints with multi-format support
- Redis-based caching for task tracking and performance optimization
- Comprehensive error handling with standardized response formats

**Worker System:**

- Strengthened message processing with proper ACK/NACK handling
- Real-time progress tracking via Redis integration
- Enhanced file processing pipeline with hex encoding for safe transmission
- Improved connection management with thread-safe operations

**Messaging Infrastructure:**

- Strongly typed message contracts using TypedDict schemas
- Priority-based message queuing for optimal processing order
- Enhanced publishers with comprehensive documentation and error handling
- Robust connection factory with automatic recovery mechanisms

**Data Management:**

- Advanced Redis operations for task management and caching
- MongoDB schema versioning with comparison logic and rollback support
- Optimized database operations with atomic updates and error handling
- Enhanced query patterns for efficient data retrieval

### 📊 Technical Metrics

- **Endpoint Coverage**: 6 API endpoints with comprehensive functionality
- **Message Types**: 2 strongly typed message schemas (Validation, Schema)
- **Task Types**: 3 distinct task types (sample_validation, upload_schema, remove_schema, meanwhile)
- **File Formats**: 3 supported formats (CSV, XLSX, XLS)
- **Database Integration**: 3 storage systems (MongoDB, Redis, RabbitMQ)

### 🔧 Developer Experience

- **Type Safety**: TypedDict schemas for compile-time validation
- **Documentation**: Comprehensive README files for each module
- **Error Handling**: Detailed error messages with context
- **Monitoring**: Real-time task tracking and progress updates
- **Testing**: Enhanced error scenarios and edge case handling
