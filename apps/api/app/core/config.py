from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "gxRag API"
    app_version: str = "0.1.0"
    api_prefix: str = "/v1"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="GXRAG_",
        extra="ignore",
    )


settings = Settings()

