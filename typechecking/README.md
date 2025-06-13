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

### Current Version

- Multi-format file support (CSV, XLSX, XLS)
- Parallel validation processing
- RabbitMQ message queuing
- MongoDB schema storage
- Redis caching
- Performance benchmarking tools
- Docker deployment support
