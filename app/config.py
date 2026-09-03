from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "global-invoice-metrics"
    port: int = 5000
    cors_origins: str = "*"

    database_url: str = (
        "postgresql://postgres:postgres_password@postgres-db:5432/global_invoice"
    )
    invoice_table: str = "invoices"
    invoice_type_column: str = "invoice_type"
    invoice_total_column: str = "total"

    jwt_secret: str = "change-me-shared-with-java"
    jwt_algorithm: str = "HS256"
    jwt_role_claim: str = "role"

    internal_api_key: str = "change-me-internal-key"

    @property
    def cors_origin_list(self) -> list[str]:
        if self.cors_origins.strip() == "*":
            return ["*"]
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
