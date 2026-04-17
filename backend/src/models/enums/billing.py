from enum import StrEnum


class TariffCode(StrEnum):
    BAZOVYY = "bazovyy"
    OPTIMALNYY = "optimalnyy"
    PREMIUM = "premium"


class BillingInterval(StrEnum):
    MONTHLY = "monthly"
    ONE_TIME = "one_time"


class PaymentMethod(StrEnum):
    CARD_RU = "card_ru"
    SBP = "sbp"
    CARD_INTERNATIONAL = "card_international"
    PAYPAL = "paypal"


class PaymentProvider(StrEnum):
    LAVA_TOP = "lava_top"


class PaymentCurrency(StrEnum):
    RUB = "rub"
    USD = "usd"


class ProductPaymentType(StrEnum):
    RECURRING = "recurring"
    ONE_TIME = "one_time"


class OrderStatus(StrEnum):
    PENDING = "pending"
    PAID = "paid"
    CANCELED = "canceled"
    EXPIRED = "expired"


class PaymentIntentStatus(StrEnum):
    CREATED = "created"
    AWAITING_PAYMENT = "awaiting_payment"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELED = "canceled"


class TransactionStatus(StrEnum):
    SUCCESS = "success"
    FAILED = "failed"


class TransactionType(StrEnum):
    PAYMENT = "payment"
    RENEWAL = "renewal"
    REFUND = "refund"


class SubscriptionStatus(StrEnum):
    PENDING = "pending"
    ACTIVE = "active"
    CANCELED = "canceled"
    EXPIRED = "expired"


class BalanceTransactionType(StrEnum):
    CREDIT = "credit"
    DEBIT = "debit"
    REFUND = "refund"
    ADJUSTMENT = "adjustment"


class LavaTopPeriodicity(StrEnum):
    ONE_TIME = "ONE_TIME"
    MONTHLY = "MONTHLY"


class LavaTopPaymentMethod(StrEnum):
    BANK131 = "BANK131"
    UNLIMINT = "UNLIMINT"
    PAYPAL = "PAYPAL"
    SBP = "SBP"
