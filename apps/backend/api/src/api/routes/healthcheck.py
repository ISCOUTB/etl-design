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
    mongo_response = database_client.mongo_ping_async()
    redis_response = database_client.redis_ping_async()
    mongo_status, redis_status = await mongo_response, await redis_response

    return HealthCheckResponse(
        mongo_status=mongo_status["pong"],
        redis_status=redis_status["pong"],
        message_queue=publisher._channel.is_open,
    )
