import asyncio

import aio_pika
from messaging_utils.core.config import settings as mq_settings

from src.core.database_client import DatabaseClient
from src.schemas.healthcheck import (
    DatabaseHealthCheckResult,
    OverallHealthCheckResult,
    RabbitMQHealthCheckResult,
)


async def check_rabbitmq_connection() -> RabbitMQHealthCheckResult:
    """Check RabbitMQ connection health."""
    try:
        rabbitmq_url = str(mq_settings.RABBITMQ_URI)

        # Connect with timeout
        connection = await asyncio.wait_for(
            aio_pika.connect_robust(rabbitmq_url), timeout=5.0
        )

        # Create a channel to test the connection
        channel = await connection.channel()
        await channel.close()
        await connection.close()

        return RabbitMQHealthCheckResult(
            status="healthy", response_time_ms="< 5000", error=None
        )
    except asyncio.TimeoutError:
        return RabbitMQHealthCheckResult(
            status="unhealthy", response_time_ms="> 5000", error="Connection timeout"
        )
    except Exception as e:
        return RabbitMQHealthCheckResult(
            status="unhealthy", response_time_ms="N/A", error=str(e)
        )


def check_database_client_connection(
    db_client: DatabaseClient,
) -> DatabaseHealthCheckResult:
    """Check overall database client connection health."""
    try:
        redis_health = db_client.redis_ping()["pong"]
    except Exception:
        redis_health = False

    try:
        mongo_health = db_client.mongo_ping()["pong"]
    except Exception:
        mongo_health = False

    overall_status = "healthy" if mongo_health and redis_health else "unhealthy"
    return DatabaseHealthCheckResult(
        status=overall_status, mongodb=mongo_health, redis=redis_health
    )


async def check_database_client_connection_async(
    db_client: DatabaseClient,
) -> DatabaseHealthCheckResult:
    """Check overall database client connection health."""
    try:
        redis_health = (await db_client.redis_ping_async())["pong"]
    except Exception:
        redis_health = False

    try:
        mongo_health = (await db_client.mongo_ping_async())["pong"]
    except Exception:
        mongo_health = False

    overall_status = "healthy" if mongo_health and redis_health else "unhealthy"
    return DatabaseHealthCheckResult(
        status=overall_status, mongodb=mongo_health, redis=redis_health
    )


async def check_databases_connection(
    db_client: DatabaseClient, awaitable: bool = False
) -> OverallHealthCheckResult:
    """Check overall database connection health."""
    rabbitmq_health = await check_rabbitmq_connection()

    if awaitable:
        database_health = await check_database_client_connection_async(db_client)
    else:
        database_health = check_database_client_connection(db_client)

    overall_status = (
        "healthy"
        if database_health.status == "healthy" and rabbitmq_health.status == "healthy"
        else "unhealthy"
    )
    return OverallHealthCheckResult(
        status=overall_status, database=database_health, rabbitmq=rabbitmq_health
    )
