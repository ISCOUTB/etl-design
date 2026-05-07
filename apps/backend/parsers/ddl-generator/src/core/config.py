from pydantic import computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict

from src.utils.rootdir import ROOTDIR


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(ROOTDIR / ".env").absolute(),
        env_ignore_empty=True,
        extra="ignore",
    )

    DDL_GENERATOR_HOST: str = "localhost"
    DDL_GENERATOR_PORT: str = "50053"
    DDL_GENERATOR_DEBUG: bool = False

    @computed_field
    @property
    def DDL_GENERATOR_CHANNEL(self) -> str:
        return f"{self.DDL_GENERATOR_HOST}:{self.DDL_GENERATOR_PORT}"

    ENABLE_PROMETHEUS_METRICS: bool = False
    PROMETHEUS_METRICS_PORT: str = "9090"

    DDL_TRACE_CONTEXT_ENABLED: bool = True
    DDL_TRACE_CONTEXT_LOG_HEADERS: bool = False
    OTEL_SERVICE_NAME: str = "ddl-generator"
    OTEL_SERVICE_VERSION: str = "1.0.0"


settings = Settings()
