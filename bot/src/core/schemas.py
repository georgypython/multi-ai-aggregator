from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel


class GenerationStatus(StrEnum):
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELED = "canceled"


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
    created_at: str | None = None


class ImageModelConfigResult(BaseModel):
    id: UUID
    name: str
    provider_key: str
    provider: str
    sizes: list[str]
    qualities: list[str]


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


class VideoModelPriceResult(BaseModel):
    ai_model_id: UUID
    provider_key: str
    duration_seconds: int
    tokens_price: float


class ImageGenerationResult(BaseModel):
    ai_model_id: UUID
    user_id: UUID
    generation_id: UUID
    tokens_cost: float
    status: GenerationStatus


class UploadMediaImagesResult(BaseModel):
    media_file_id: UUID


class VideoGenerationResult(BaseModel):
    ai_model_id: UUID
    user_id: UUID
    generation_id: UUID
    tokens_cost: float
    status: GenerationStatus


class UserBalanceResult(BaseModel):
    user_id: UUID
    telegram_id: int
    available_tokens: float
    hold_tokens: float


class PaymentProductItem(BaseModel):
    plan_id: UUID
    tariff_code: str
    name: str
    display_name: str
    description: str | None = None
    billing_interval: str
    duration_days: int
    price_rub: float
    tokens_amount: float
    is_vpn_bonus_enabled: bool


class PaymentProductsResult(BaseModel):
    products: list[PaymentProductItem]


class PaymentMethodOption(BaseModel):
    code: str
    enabled: bool
    is_soon: bool


class PaymentMethodsResult(BaseModel):
    methods: list[PaymentMethodOption]


class InvoiceCreateResult(BaseModel):
    order_id: UUID
    payment_intent_id: UUID
    payment_url: str | None = None
    amount: float
    currency: str
    provider: str
    payment_method: str
