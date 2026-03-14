from fastapi import APIRouter

from src.api.deps import DatabaseClientDep, PublisherDep
from src.schemas.healthcheck import HealthCheckResponse

router = APIRouter()


@router.get("/")
async def healthcheck(
    database_client: DatabaseClientDep, publisher: PublisherDep
) -> HealthCheckResponse:
    """
    Healthcheck endpoint to verify that the API is running.
    This endpoint can be used by monitoring tools to check the health of the API.
    """
    mongo_status = (await database_client.mongo_ping_async())["pong"]
    redis_status = (await database_client.redis_ping_async())["pong"]

    return HealthCheckResponse(
        mongo_status=mongo_status,
        redis_status=redis_status,
        message_queue=publisher._channel.is_open,
    )
