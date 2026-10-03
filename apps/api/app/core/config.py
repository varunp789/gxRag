from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "gxRag API"
    app_version: str = "0.1.0"
    api_prefix: str = "/v1"
    environment: str = "development"
    redis_url: str = "redis://localhost:6379/0"
    processing_queue: str = "asset-processing"
    processing_state_path: str = ".gxrag/processing-state.json"
    artifact_root: str = ".gxrag/artifacts"
    # When set, operational state (assets, jobs, artifacts, indexes, usage,
    # audit, API keys) lives in PostgreSQL; otherwise the JSON dev store is used.
    database_url: str | None = None
    vector_database_url: str = "postgresql://gxrag:gxrag@localhost:5432/gxrag"
    opensearch_url: str = "http://localhost:9200"
    arangodb_url: str = "http://localhost:8529"
    arangodb_database: str = "gxrag"
    arangodb_username: str = "root"
    arangodb_password: str = "gxrag"
    openai_api_key: str | None = None
    webhook_secret: str | None = None
    stripe_secret_key: str | None = None
    # "dev" trusts X-Actor-Email headers (local only); "jwt" requires bearer
    # tokens or workspace API keys and is mandatory outside development.
    auth_mode: str = "dev"
    jwt_secret: str | None = None
    jwt_issuer: str = "gxrag"
    jwt_leeway_seconds: int = 30
    rate_limit_per_minute: int = 120

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="GXRAG_",
        extra="ignore",
    )

    def validate_for_runtime(self) -> None:
        """Refuse insecure combinations before the API starts serving traffic."""
        if self.environment != "development":
            if self.auth_mode != "jwt":
                raise RuntimeError("GXRAG_AUTH_MODE must be 'jwt' outside development.")
            if not self.jwt_secret or len(self.jwt_secret) < 32:
                raise RuntimeError("GXRAG_JWT_SECRET must be set to at least 32 characters.")
            if not self.database_url:
                raise RuntimeError("GXRAG_DATABASE_URL is required outside development.")
        if self.auth_mode == "jwt" and not self.jwt_secret:
            raise RuntimeError("GXRAG_JWT_SECRET is required when GXRAG_AUTH_MODE=jwt.")


settings = Settings()
