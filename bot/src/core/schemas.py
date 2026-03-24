from uuid import UUID

from pydantic import BaseModel


class AIModelItem(BaseModel):
    id: UUID
    name: str
    provider_key: str
    is_active: bool
    description: str | None = None
    model_type: str


class LLMGenerationResult(BaseModel):
    text: str
    ai_model_id: UUID
    user_id: UUID
    generation_id: UUID
    tokens_cost: float


class LLMConfigResult(BaseModel):
    id: UUID
    user_id: UUID | None
    name: str | None = None
    configuration_type: str
    temperature: float | None = None
    instructions: str | None = None


class ImageModelConfigResult(BaseModel):
    id: UUID
    name: str
    provider_key: str
    provider: str
    sizes: list[str]
    qualities: list[str]
    prices_usd: dict[str, dict[str, float]]


class ImageModelPriceResult(BaseModel):
    ai_model_id: UUID
    provider_key: str
    size: str
    quality: str
    tokens_price: float


class VideoModelConfigResult(BaseModel):
    id: UUID
    name: str
    provider_key: str
    provider: str
    durations_seconds: list[int]
    sizes: list[str]
    prices_usd_by_duration: dict[str, dict[str, float]]


class VideoModelPriceResult(BaseModel):
    ai_model_id: UUID
    provider_key: str
    duration_seconds: int
    size: str
    tokens_price: float


class ImageGenerationResult(BaseModel):
    ai_model_id: UUID
    user_id: UUID
    generation_id: UUID
    tokens_cost: float
    status: str
    text: str | None = None


class UploadMediaImagesResult(BaseModel):
    media_file_id: UUID


class VideoGenerationResult(BaseModel):
    ai_model_id: UUID
    user_id: UUID
    generation_id: UUID
    tokens_cost: float


class UserBalanceResult(BaseModel):
    user_id: UUID
    telegram_id: int
    available_tokens: float
    hold_tokens: float
