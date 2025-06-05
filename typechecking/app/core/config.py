from pydantic_core import MultiHostUrl
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import MongoDsn, computed_field, BeforeValidator

from typing import Any, Annotated

from dotenv import load_dotenv

load_dotenv()


def split_list(v: Any) -> list[str] | str:
    """
    Función para dividir cadenas en una lista en formato de texto.

    Args:
        v (Any): Valor que puede ser una cadena o lista.

    Returns:
        list[str] | str: Lista o la cadena original si ya es una lista o cadena respectivamente.

    Raises:
        ValueError: Si el valor no es de tipo válido.
    """
    if isinstance(v, str) and not v.startswith("["):
        return [i.strip() for i in v.split(",")]
    elif isinstance(v, list | str):
        return v
    raise ValueError(v)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    API_V1_STR: str
    CORS_ORIGINS: Annotated[list[str] | str, BeforeValidator(split_list)]

    # MongoDB Configuration
    MONGO_HOST: str
    MONGO_PORT: int
    MONGO_INITDB_ROOT_USERNAME: str
    MONGO_INITDB_ROOT_PASSWORD: str
    MONGO_DB: str
    MONGO_COLLECTION: str

    @computed_field
    @property
    def MONGO_URI(self) -> MongoDsn:
        return MultiHostUrl.build(
            scheme="mongodb",
            username=self.MONGO_INITDB_ROOT_USERNAME,
            password=self.MONGO_INITDB_ROOT_PASSWORD,
            host=self.MONGO_HOST,
            port=self.MONGO_PORT,
        )


settings = Settings()
