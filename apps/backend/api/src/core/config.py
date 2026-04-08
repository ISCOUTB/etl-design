from typing import Annotated, Any

from dotenv import load_dotenv
from pydantic import (
    AmqpDsn,
    BeforeValidator,
    PostgresDsn,
    computed_field,
)
from pydantic_core import MultiHostUrl
from pydantic_settings import BaseSettings, SettingsConfigDict

load_dotenv(override=True)


def split_list(v: Any) -> list[str] | str:
    """
    Function to split strings into a list in text format.

    Args:
        v (Any): Value that can be a string or list.

    Returns:
        list[str] | str: List or the original string if it's already a list or string respectively.

    Raises:
        ValueError: If the value is not of a valid type.
    """
    if isinstance(v, str) and not v.startswith("["):
        return [i.strip() for i in v.split(",")]
    elif isinstance(v, list | str):
        return v
    raise ValueError(v)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_ignore_empty=True,
        extra="ignore",
    )
    # API Configuration
    API_V1_STR: str
    CORS_ORIGINS: Annotated[list[str] | str, BeforeValidator(split_list)]
    SERVER_HOST: str
    SERVER_PORT: int
    SERVER_DEBUG: bool

    AUTH_INFO: str
    SECRET_KEY: str

    # Encryption configuration for database credentials in projects
    CREDENTIALS_SECRET_KEY: str
    CREDENTIALS_SIGN: str

    # OTel Configuration
    OTEL_SERVICE_NAME: str = "api-server"
    OTEL_SERVICE_VERSION: str = "1.0.0"

    # For pending status
    IDEMPOTENCY_TTL_DEFAULT_SECONDS: int = 60 * 10  # 10 minutes
    IDEMPOTENCY_TTL_RETRY_DELAY_SECONDS: int = 60 * 1  # 1 minute
    IDEMPOTENCY_TTL_PUBLISHED_SECONDS: int = 60 * 30  # 30 minutes

    FIRST_SUPERUSER_NAME: str
    FIRST_SUPERUSER_EMAIL: str
    FIRST_SUPERUSER_PASSWORD: str

    # RabbitMQ Configuration
    RABBITMQ_HOST: str
    RABBITMQ_PORT: int
    RABBITMQ_VHOST: str
    RABBITMQ_USER: str
    RABBITMQ_PASSWORD: str
    RABBITMQ_MAX_RETRIES: int = 5
    RABBITMQ_RETRY_DELAY_SECONDS: float = 1.0
    RABBITMQ_BACKOFF_MULTIPLIER: float = 2.0

    @computed_field
    @property
    def RABBITMQ_URI(self) -> AmqpDsn:
        return MultiHostUrl.build(  # type: ignore
            scheme="amqp",
            username=self.RABBITMQ_USER,
            password=self.RABBITMQ_PASSWORD,
            host=self.RABBITMQ_HOST,
            port=self.RABBITMQ_PORT,
            path=self.RABBITMQ_VHOST,
        )

    # PostgreSQL Configuration
    POSTGRES_HOST: str
    POSTGRES_PORT: int
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str

    @computed_field
    @property
    def POSTGRES_URI(self) -> PostgresDsn:
        return MultiHostUrl.build(  # type: ignore
            scheme="postgresql+psycopg2",
            username=self.POSTGRES_USER,
            password=self.POSTGRES_PASSWORD,
            host=self.POSTGRES_HOST,
            port=self.POSTGRES_PORT,
            path=self.POSTGRES_DB,
        )

    # Database Connection Configuration
    DATABASE_CONNECTION_HOST: str
    DATABASE_CONNECTION_PORT: int
    DATABASE_MAX_RETRIES: int = 5
    DATABASE_RETRY_DELAY_SECONDS: float = 1.0
    DATABASE_BACKOFF_MULTIPLIER: float = 2.0
    DATABASE_TRACE_CONTEXT_ENABLED: bool = True

    @computed_field
    @property
    def DATABASE_CONNECTION_CHANNEL(self) -> str:
        return f"{self.DATABASE_CONNECTION_HOST}:{self.DATABASE_CONNECTION_PORT}"

    # Excel-Reader configuration
    EXCEL_READER_HOST: str = "localhost"
    EXCEL_READER_PORT: int = 8001
    EXCEL_READER_TIMEOUT_SECONDS: int = 30

    @computed_field
    @property
    def EXCEL_READER_URL(self) -> str:
        return f"http://{self.EXCEL_READER_HOST}:{self.EXCEL_READER_PORT}"


settings = Settings()  # type: ignore
