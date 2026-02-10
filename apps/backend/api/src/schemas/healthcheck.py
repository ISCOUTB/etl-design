from pydantic import BaseModel


class HealthCheckResponse(BaseModel):
    mongo_status: bool
    redis_status: bool
    message_queue: bool
