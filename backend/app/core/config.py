import json
from typing import List, Union
from pydantic import AnyHttpUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application Settings loaded from environment variables and .env file.
    Production-safe defaults with strict typing.
    """
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )

    APP_NAME: str = "Enermax CRM"
    APP_ENV: str = "development"  # development | staging | production
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"
    API_V1_PREFIX: str = "/api/v1"

    # Security
    SECRET_KEY: str = "insecure-development-secret-key-change-in-production-minimum-64-characters"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # CORS
    CORS_ORIGINS: Union[List[str], str] = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
    ]

    @field_validator("CORS_ORIGINS", mode="before")
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str):
            try:
                parsed = json.loads(v)
                if isinstance(parsed, list):
                    return parsed
            except Exception:
                return [i.strip() for i in v.split(",") if i.strip()]
        elif isinstance(v, list):
            return v
        return ["http://localhost:5173"]

    # Database
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = "enermax_user"
    POSTGRES_PASSWORD: str = "enermax_secure_password"
    POSTGRES_DB: str = "enermax_crm"
    DATABASE_URL: str = ""

    # Database connection pool configuration
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20
    DB_POOL_TIMEOUT: int = 30
    DB_POOL_RECYCLE: int = 1800
    DB_STATEMENT_TIMEOUT: int = 15000  # 15s in ms
    DB_IDLE_TIMEOUT: int = 30000       # 30s in ms

    # Redis
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: str = ""
    REDIS_DB: int = 0
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_SOCKET_TIMEOUT: float = 2.0
    REDIS_MAX_CONNECTIONS: int = 50

    # Rate Limiting
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_LOGIN_PER_MINUTE: int = 10
    RATE_LIMIT_API_PER_MINUTE: int = 300

    # Token Security
    TOKEN_BLACKLIST_ENABLED: bool = True

    # Document & File Storage
    STORAGE_BACKEND: str = "local"  # local | s3
    STORAGE_LOCAL_DIR: str = "storage"
    STORAGE_MAX_FILE_SIZE_BYTES: int = 26214400  # 25 MB
    S3_BUCKET_NAME: str = "enermax-documents"
    S3_ENDPOINT_URL: str = ""
    S3_ACCESS_KEY: str = ""
    S3_SECRET_KEY: str = ""
    S3_REGION: str = "us-east-1"

    def get_database_url(self) -> str:
        if self.DATABASE_URL:
            # Normalize postgres:// to postgresql+asyncpg:// if needed
            url = self.DATABASE_URL
            if url.startswith("postgres://"):
                url = url.replace("postgres://", "postgresql+asyncpg://", 1)
            elif url.startswith("postgresql://") and not url.startswith("postgresql+asyncpg://"):
                url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
            return url
        # Default async PostgreSQL URL
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@"
            f"{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    @property
    def is_production(self) -> bool:
        return self.APP_ENV.lower() == "production"

    def validate_production_settings(self) -> None:
        """Validate critical security requirements when running in production mode."""
        if self.is_production:
            if self.DEBUG:
                raise ValueError("DEBUG mode must be FALSE in production environment.")
            if "insecure" in self.SECRET_KEY.lower() or len(self.SECRET_KEY) < 32:
                raise ValueError("Production SECRET_KEY must be a secure, random string with at least 32 characters.")
            if not self.DATABASE_URL and self.POSTGRES_PASSWORD == "enermax_secure_password":
                raise ValueError("Production PostgreSQL password must not use default credentials.")


settings = Settings()
settings.validate_production_settings()

