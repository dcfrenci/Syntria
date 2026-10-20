from urllib.parse import quote_plus

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    POSTGRES_HOST: str
    POSTGRES_PORT: int = 5432

    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 2

    # Identifier of the system admin account (the password is never stored in config)
    ADMIN_EMAIL: str
    ENABLE_DOCS: bool = False
    LOG_LEVEL: str = "INFO"

    @field_validator("SECRET_KEY")
    @classmethod
    def _strong_secret(cls, v: str) -> str:
        weak = ("change_me", "supersecret", "changeme")
        if len(v) < 32 or any(w in v.lower() for w in weak):
            raise ValueError("SECRET_KEY must be >= 32 chars and not a placeholder")
        return v

    @property
    def database_url(self) -> str:
        user = quote_plus(self.POSTGRES_USER)
        password = quote_plus(self.POSTGRES_PASSWORD)
        return (
            f"postgresql+asyncpg://{user}:{password}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )
    
    @field_validator("POSTGRES_PASSWORD")
    @classmethod
    def _strong_db_password(cls, v: str) -> str:
        if len(v) < 16 or v.lower() in ("admin", "password", "postgres"):
            raise ValueError("POSTGRES_PASSWORD must be >= 16 chars and not a default")
        return v
    

settings = Settings()
