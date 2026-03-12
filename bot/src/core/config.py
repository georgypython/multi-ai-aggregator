from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import BaseModel


BASE_PATH = Path(__file__).resolve().parent.parent.parent.parent


class LoggerConfig(BaseModel):
    log_lvl: int = 20
    logger_path: Path = BASE_PATH / "logs" / "bot_logs.log"


class TgConfig(BaseModel):
    bot_token: str = "YOUR_BOT_TOKEN"


class AIConfig(BaseModel):
    ai_api_url: str = "http://localhost:8000"
    api_key: str = "YOUR_API_KEY"
    request_timeout_seconds: float = 120.0


class RedisConfig(BaseModel):
    host: str = "localhost"
    port: int = 6379
    db: int = 0
    password: str | None = None

    @property
    def url(self) -> str:
        auth = f":{self.password}@" if self.password else ""
        return f"redis://{auth}{self.host}:{self.port}/{self.db}"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BASE_PATH / ".env",
        extra="ignore",
        case_sensitive=False,
        env_nested_delimiter="__",
        env_prefix="BOT__CONFIG__",
    )

    ai: AIConfig
    redis: RedisConfig = RedisConfig()
    logger: LoggerConfig = LoggerConfig()
    tg: TgConfig


settings = Settings()