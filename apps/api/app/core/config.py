from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "gxRag API"
    app_version: str = "0.1.0"
    api_prefix: str = "/v1"
    redis_url: str = "redis://localhost:6379/0"
    processing_queue: str = "asset-processing"
    processing_state_path: str = ".gxrag/processing-state.json"
    artifact_root: str = ".gxrag/artifacts"
    vector_database_url: str = "postgresql://gxrag:gxrag@localhost:5432/gxrag"
    opensearch_url: str = "http://localhost:9200"
    arangodb_url: str = "http://localhost:8529"
    arangodb_database: str = "gxrag"
    arangodb_username: str = "root"
    arangodb_password: str = "gxrag"
    openai_api_key: str | None = None
    webhook_secret: str | None = None
    stripe_secret_key: str | None = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="GXRAG_",
        extra="ignore",
    )


settings = Settings()
