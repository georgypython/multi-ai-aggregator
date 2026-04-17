from datetime import datetime
from decimal import Decimal
from enum import Enum

from pydantic import BaseModel

from src.models.enums import PaymentCurrency


class LavaTopWebhookEventType(str, Enum):
    PAYMENT_SUCCESS = "payment.success"
    PAYMENT_FAILED = "payment.failed"
    SUBSCRIPTION_RECURRING_PAYMENT_SUCCESS = "subscription.recurring.payment.success"
    SUBSCRIPTION_RECURRING_PAYMENT_FAILED = "subscription.recurring.payment.failed"
    SUBSCRIPTION_CANCELLED = "subscription.cancelled"


class LavaTopContractStatus(str, Enum):
    NEW = "new"
    IN_PROGRESS = "in-progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    SUBSCRIPTION_ACTIVE = "subscription-active"
    SUBSCRIPTION_EXPIRED = "subscription-expired"
    SUBSCRIPTION_CANCELLED = "subscription-cancelled"
    SUBSCRIPTION_FAILED = "subscription-failed"


class LavaTopWebhookProduct(BaseModel):
    id: str
    title: str


class LavaTopWebhookBuyer(BaseModel):
    email: str


class LavaTopWebhookRequestData(BaseModel):
    eventType: LavaTopWebhookEventType
    product: LavaTopWebhookProduct
    contractId: str
    parentContractId: str | None = None
    buyer: LavaTopWebhookBuyer

    amount: Decimal | None = None
    currency: PaymentCurrency | None = None
    status: LavaTopContractStatus | None = None
    timestamp: datetime | None = None
    errorMessage: str | None = None

    cancelledAt: datetime | None = None
    willExpireAt: datetime | None = None

    def is_successful(self) -> bool:
        return self.eventType in (
            LavaTopWebhookEventType.PAYMENT_SUCCESS,
            LavaTopWebhookEventType.SUBSCRIPTION_RECURRING_PAYMENT_SUCCESS,
        )

    def is_failed(self) -> bool:
        return self.eventType in (
            LavaTopWebhookEventType.PAYMENT_FAILED,
            LavaTopWebhookEventType.SUBSCRIPTION_RECURRING_PAYMENT_FAILED,
        )

    def is_recurring(self) -> bool:
        return self.eventType in (
            LavaTopWebhookEventType.SUBSCRIPTION_RECURRING_PAYMENT_SUCCESS,
            LavaTopWebhookEventType.SUBSCRIPTION_RECURRING_PAYMENT_FAILED,
        )

    def is_cancellation(self) -> bool:
        return self.eventType == LavaTopWebhookEventType.SUBSCRIPTION_CANCELLED
