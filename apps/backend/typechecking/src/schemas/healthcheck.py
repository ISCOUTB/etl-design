from pydantic import BaseModel


class RabbitMQHealthCheckResult(BaseModel):
    status: str
    response_time_ms: str
    error: str | None = None


class DatabaseHealthCheckResult(BaseModel):
    status: str
    mongodb: bool
    redis: bool


class OverallHealthCheckResult(BaseModel):
    status: str
    database: DatabaseHealthCheckResult
    rabbitmq: RabbitMQHealthCheckResult
