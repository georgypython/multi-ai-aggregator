import logging
from pathlib import Path

from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_PATH = Path(__file__).resolve().parent.parent.parent


class RunConfig(BaseModel):
    host: str = "0.0.0.0"
    port: int = 8000


class LoggerConfig(BaseModel):
    lvl: int = logging.INFO
    logs_path: Path = BASE_PATH / "logs" / "app_logs.log"
    log_format: str = (
        "%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s"
    )
    max_bytes: int = 5 * 1024 * 1024
    backup_count: int = 3


class ApiV1Prefix(BaseModel):
    prefix: str = "/v1"


class ApiConfig(BaseModel):
    api_key: str = "YOUR_API_KEY"
    prefix: str = "/api"
    v1: ApiV1Prefix = ApiV1Prefix()


class DbConfig(BaseModel):
    host: str = "localhost"
    passwd: str | None = None
    user: str = "postgres"
    name: str = "postgres"
    port: int = 5432

    convention: dict = {
        "ix": "ix_%(column_0_label)s",
        "uq": "uq_%(table_name)s_%(column_0_name)s",
        "ck": "ck_%(table_name)s_%(constraint_name)s",
        "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
        "pk": "pk_%(table_name)s",
    }

    @property
    def url_async(self):
        return f"postgresql+asyncpg://{self.user}:{self.passwd}@{self.host}:{self.port}/{self.name}"


class OpenRouterConfig(BaseModel):
    base_url: str = "https://openrouter.ai/api/v1"
    api_key: str = "API_KEY_HERE"


class RedisConfig(BaseModel):
    host: str = "localhost"
    port: int = 6379
    db: int = 0
    password: str | None = None
    chat_history_ttl_seconds: int = 7 * 24 * 60 * 60
    chat_history_limit: int = 15

    @property
    def url(self) -> str:
        auth = f":{self.password}@" if self.password else ""
        return f"redis://{auth}{self.host}:{self.port}/{self.db}"


class AILogicConfig(BaseModel):
    new_user_free_tokens: float = 10


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BASE_PATH / ".env",
        case_sensitive=False,
        env_nested_delimiter="__",
        env_prefix="APP_CONFIG__",
    )

    logger: LoggerConfig = LoggerConfig()
    api: ApiConfig = ApiConfig()
    run: RunConfig = RunConfig()
    db: DbConfig
    openrouter: OpenRouterConfig
    redis: RedisConfig = RedisConfig()
    ai_logic: AILogicConfig = AILogicConfig()
    

settings = Settings()
