from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_ignore_empty=True,
        extra="ignore",
    )

    FORMULA_PARSER_HOST: str = "localhost"
    FORMULA_PARSER_PORT: str = "50052"


settings = Settings()


if __name__ == "__main__":
    print(settings.model_dump())
