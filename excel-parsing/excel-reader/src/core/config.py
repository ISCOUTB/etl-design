from pydantic import computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_ignore_empty=True,
        extra="ignore",
    )

    FORMULA_PARSER_HOST: str = "localhost"
    FORMULA_PARSER_PORT: str = "50052"

    @computed_field
    @property
    def FORMULA_PARSER_CHANNEL(self) -> str:
        return f"{self.FORMULA_PARSER_HOST}:{self.FORMULA_PARSER_PORT}"


settings = Settings()


if __name__ == "__main__":
    print(settings.model_dump())
