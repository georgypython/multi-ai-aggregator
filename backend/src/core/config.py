import logging
from pathlib import Path
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_PATH = Path(__file__).resolve().parent.parent.parent.parent


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


class WaveSpeedConfig(BaseModel):
    base_url: str = "https://api.wavespeed.ai"
    api_key: str = "API_KEY_HERE"
    webhook_secret: str = "whsec_YOUR_WEBHOOK_SECRET"
    wavespeed_webhook_url: str = "https://your-webhook-url"
    poll_interval_seconds: int = 3
    poll_max_attempts: int = 30


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


class RabbitMQConfig(BaseModel):
    host: str = "localhost"
    port: int = 5672
    user: str = "guest"
    password: str = "guest"
    vhost: str = "/"

    @property
    def url(self) -> str:
        return (
            f"amqp://{self.user}:{self.password}"
            f"@{self.host}:{self.port}{self.vhost}"
        )


class StorageConfig(BaseModel):
    endpoint_url: str = "http://localhost:9000"
    region: str = "us-east-1"
    access_key: str = "minioadmin"
    secret_key: str = "minioadmin"
    connect_timeout_seconds: float = 3.0
    read_timeout_seconds: float = 15.0
    max_retry_attempts: int = 2
    operation_timeout_seconds: float = 20.0
    bucket: str = "ai-media"
    presigned_ttl_seconds: int = 900
    input_retention_hours: int = 24
    input_prefix: str = "inputs"
    max_upload_bytes: int = 10 * 1024 * 1024
    allowed_image_content_types: tuple[str, ...] = (
        "image/jpeg",
        "image/png",
        "image/webp",
    )
    image_extensions: dict[str, str] = {
        "image/jpeg": "jpg",
        "image/png": "png",
        "image/webp": "webp",
    }


class AILogicConfig(BaseModel):
    new_user_free_tokens: int = 300


class BillingConfig(BaseModel):
    token_scale: str = "0.000001"

    @property
    def token_scale_decimal(self) -> Decimal:
        return Decimal(self.token_scale)


class PaymentConfig(BaseModel):
    base_url: str = "https://gate.lava.top"
    api_key: str = "LAVATOP_API_KEY_HERE"
    webhook_api_key: str | None = None
    order_expire_minutes: int = 30


class TgConfig(BaseModel):
    bot_token: str = "YOUR_BOT_TOKEN"


class AuthConfig(BaseModel):
    access_secret: str = "change-me-access-secret"
    refresh_secret: str = "change-me-refresh-secret"
    algorithm: str = "HS256"
    access_ttl_minutes: int = 60
    refresh_ttl_days: int = 7
    cookie_secure: bool = False
    cookie_httponly: bool = True
    cookie_samesite: Literal["lax", "strict", "none"] = "lax"
    cookie_domain: str | None = None


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BASE_PATH / ".env",
        extra="ignore",
        case_sensitive=False,
        env_nested_delimiter="__",
        env_prefix="APP_CONFIG__",
    )

    logger: LoggerConfig = LoggerConfig()
    api: ApiConfig = ApiConfig()
    run: RunConfig = RunConfig()
    db: DbConfig
    openrouter: OpenRouterConfig
    wavespeed: WaveSpeedConfig
    redis: RedisConfig = RedisConfig()
    rabbitmq: RabbitMQConfig = RabbitMQConfig()
    storage: StorageConfig = StorageConfig()
    ai_logic: AILogicConfig = AILogicConfig()
    billing: BillingConfig = BillingConfig()
    payment: PaymentConfig = PaymentConfig()
    tg: TgConfig = TgConfig()
    auth: AuthConfig = AuthConfig()


settings = Settings()
