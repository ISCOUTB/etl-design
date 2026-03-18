from dotenv import load_dotenv
from pydantic import RedisDsn, computed_field
from pydantic_core import MultiHostUrl
from pydantic_settings import BaseSettings, SettingsConfigDict

load_dotenv()


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_ignore_empty=True,
        extra="ignore",
    )

    # MongoDB Configuration
    MONGO_HOST: str
    MONGO_PORT: int
    MONGO_INITDB_ROOT_USERNAME: str | None = None
    MONGO_INITDB_ROOT_PASSWORD: str | None = None
    MONGO_AUTH_SOURCE: str = "admin"
    MONGO_DB: str
    MONGO_SCHEMAS_COLLECTION: str
    MONGO_TASKS_COLLECTION: str
    MONGO_MAX_RETRIES: int = 5
    MONGO_RETRY_DELAY_SECONDS: float = 0.5
    MONGO_RETRY_BACKOFF_FACTOR: float = 2.0

    @computed_field
    @property
    def MONGO_URI(self) -> str:
        credentials = ""
        if self.MONGO_INITDB_ROOT_USERNAME and self.MONGO_INITDB_ROOT_PASSWORD:
            credentials = (
                f"{self.MONGO_INITDB_ROOT_USERNAME}:{self.MONGO_INITDB_ROOT_PASSWORD}@"
            )

        return (
            f"mongodb://{credentials}{self.MONGO_HOST}:{self.MONGO_PORT}/"
            f"?authSource={self.MONGO_AUTH_SOURCE}"
        )

    # Redis Configuration
    REDIS_HOST: str
    REDIS_PORT: int
    REDIS_DB: int = 0
    REDIS_PASSWORD: str
    REDIS_EXPIRE_SECONDS: int = 60 * 5  # 5 minutes by default
    REDIS_MAX_RETRIES: int = 5
    REDIS_RETRY_DELAY_SECONDS: float = 0.5
    REDIS_RETRY_BACKOFF_FACTOR: float = 2.0

    @computed_field
    @property
    def REDIS_URI(self) -> RedisDsn:
        return MultiHostUrl.build(  # type: ignore
            scheme="redis",
            password=self.REDIS_PASSWORD,
            host=self.REDIS_HOST,
            port=self.REDIS_PORT,
        )

    # Database Connection Configuration
    DATABASE_CONNECTION_HOST: str
    DATABASE_CONNECTION_PORT: int
    DATABASE_CONNECTION_DEBUG: bool = False

    @computed_field
    @property
    def DATABASE_CONNECTION_CHANNEL(self) -> str:
        return f"{self.DATABASE_CONNECTION_HOST}:{self.DATABASE_CONNECTION_PORT}"

    # Task-specific TTL configurations
    TASK_TTL_PENDING_SECONDS: int = 60 * 30  # 30 minutes
    TASK_TTL_PROCESSING_SECONDS: int = 60 * 60  # 1 hour
    TASK_TTL_COMPLETED_SECONDS: int = 60 * 60 * 24  # 24 hours
    TASK_TTL_PUBLISHED_SECONDS: int = 60 * 60 * 12  # 12 hours
    TASK_TTL_FAILED_SECONDS: int = 60 * 60 * 12  # 12 hours

    # Cache TTL configurations
    USER_CACHE_TTL_SECONDS: int = 60 * 15  # 15 minutes
    USER_LIST_CACHE_TTL_SECONDS: int = 60 * 5  # 5 minutes
    SCHEMA_CACHE_TTL_SECONDS: int = 60 * 60 * 6  # 6 minutes

    # Default TTL configuration
    DEFAULT_TTL_SECONDS: int = 60 * 30  # 30 minutes

    # Prometheus Metrics Configuration
    ENABLE_PROMETHEUS_METRICS: bool = False
    PROMETHEUS_METRICS_PORT: str = "9090"


settings = Settings()


if __name__ == "__main__":
    print(settings.model_dump_json(indent=4))
