from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel

from src.models.enums import PaymentCurrency, PaymentMethod, PaymentProvider


class InvoiceCreateRequestSchema(BaseModel):
    plan_id: UUID
    payment_method: PaymentMethod


class InvoiceCreateResponseSchema(BaseModel):
    order_id: UUID
    payment_intent_id: UUID
    payment_url: str | None
    amount: Decimal
    currency: PaymentCurrency
    provider: PaymentProvider
    payment_method: PaymentMethod


class PaymentMethodOptionSchema(BaseModel):
    code: PaymentMethod
    enabled: bool
    is_soon: bool


class PaymentMethodsResponseSchema(BaseModel):
    methods: list[PaymentMethodOptionSchema]


class PaymentProductItemSchema(BaseModel):
    plan_id: UUID
    tariff_code: str
    name: str
    display_name: str
    description: str | None
    billing_interval: str
    duration_days: int
    price_rub: Decimal
    tokens_amount: Decimal
    is_vpn_bonus_enabled: bool
    llm_max_limit: int
    image_max_limit: int
    video_max_limit: int


class PaymentProductsResponseSchema(BaseModel):
    products: list[PaymentProductItemSchema]
