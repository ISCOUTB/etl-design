from typing import Annotated, AsyncGenerator, Dict

from fastapi import Depends, FastAPI, HTTPException
from prometheus_fastapi_instrumentator import Instrumentator

from src.core.config import settings
from src.core.database_client import DatabaseClient, get_database_client
from src.schemas.healthcheck import OverallHealthCheckResult
from src.services.healthcheck import check_databases_connection
from src.utils.logger import create_component_logger
from src.utils.uvicorn_logger import LOGGING_CONFIG

# Create logger with [http-server] prefix
logger = create_component_logger("http-server")

app = FastAPI()

Instrumentator().instrument(app).expose(app, endpoint="/metrics")


async def generate_db_client() -> AsyncGenerator[DatabaseClient, None]:
    db_client = get_database_client()
    try:
        yield db_client
    finally:
        await db_client.aclose()


DatabaseClientDep = Annotated[DatabaseClient, Depends(generate_db_client)]


@app.get("/")
async def root() -> Dict[str, str]:
    """Root endpoint for minimal server."""
    logger.debug("Root endpoint accessed")
    return {"message": "Minimal Typechecking Server is running."}


@app.get("/health")
async def health_check(
    database_client: DatabaseClientDep,
) -> OverallHealthCheckResult:
    """Health check endpoint for service monitoring."""
    logger.debug("Health check endpoint accessed")
    health_status = await check_databases_connection(database_client, awaitable=True)

    # Log health check results
    if health_status.status == "healthy":
        logger.debug("Health check passed: all systems healthy")
    else:
        logger.warning(f"Health check failed: {health_status.model_dump_json()}")
        raise HTTPException(status_code=503, detail="Service is unhealthy")

    return health_status


if __name__ == "__main__":
    import uvicorn

    logger.info(
        f"Starting minimal HTTP server on "
        f"{settings.MINIMAL_SERVER_HOST}:{settings.MINIMAL_SERVER_PORT}"
    )

    uvicorn.run(
        "src.minimal_server:app",
        host=settings.MINIMAL_SERVER_HOST,
        port=settings.MINIMAL_SERVER_PORT,
        reload=settings.MINIMAL_SERVER_DEBUG,
        reload_dirs=["src/"] if settings.MINIMAL_SERVER_DEBUG else None,
        reload_includes=["*.py"] if settings.MINIMAL_SERVER_DEBUG else None,
        log_config=LOGGING_CONFIG,
        log_level="info",
        use_colors=True,
        access_log=True,
    )
