from pydantic_settings import BaseSettings, SettingsConfigDict


class WorkerSettings(BaseSettings):
    service_name: str = "gxRag Worker"
    service_version: str = "0.1.0"
    queue_name: str = "asset-processing"
    redis_url: str = "redis://localhost:6379/0"
    poll_timeout_seconds: int = 5

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="GXRAG_WORKER_",
        extra="ignore",
    )


settings = WorkerSettings()
