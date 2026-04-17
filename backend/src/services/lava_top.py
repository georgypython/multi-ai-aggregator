from uuid import UUID

from httpx import AsyncClient

from src.core.config import settings
from src.exceptions.payment import (
    PaymentProviderRequestError,
    PaymentProviderUnavailableError,
    PaymentValidationError,
)
from src.models.enums import (
    BillingInterval,
    PaymentCurrency,
    PaymentMethod,
    ProductPaymentType,
    LavaTopPaymentMethod,
    LavaTopPeriodicity
)

class LavaTopService:
    def __init__(self, client: AsyncClient) -> None:
        self._client = client

    @staticmethod
    def to_lavatop_method(method: PaymentMethod) -> LavaTopPaymentMethod:
        mapping = {
            PaymentMethod.CARD_RU: LavaTopPaymentMethod.BANK131,
            PaymentMethod.SBP: LavaTopPaymentMethod.SBP,
            PaymentMethod.CARD_INTERNATIONAL: LavaTopPaymentMethod.UNLIMINT,
            PaymentMethod.PAYPAL: LavaTopPaymentMethod.PAYPAL,
        }
        try:
            return mapping[method]
        except KeyError as exc:
            raise PaymentValidationError("Unsupported Lavatop payment method") from exc

    async def create_invoice(
        self,
        *,
        currency: PaymentCurrency,
        payment_method: PaymentMethod,
        payment_type: ProductPaymentType,
        periodicity: BillingInterval,
        offer_id: UUID,
        email: str | None,
    ) -> dict:
        if not offer_id:
            raise PaymentValidationError("offer_id is required for LavaTop")

        if not email:
            raise PaymentValidationError("email is required for LavaTop")

        lava_periodicity = LavaTopPeriodicity.ONE_TIME
        if payment_type == ProductPaymentType.RECURRING and periodicity == BillingInterval.MONTHLY:
            lava_periodicity = LavaTopPeriodicity.MONTHLY

        body = {
            "email": email,
            "offerId": str(offer_id),
            "periodicity": lava_periodicity.value,
            "currency": currency.value,
            "buyerLanguage": "RU",
        }

        lava_method = self.to_lavatop_method(payment_method)
        if lava_method == LavaTopPaymentMethod.SBP:
            body["paymentProvider"] = "PAY2ME"
        else:
            body["paymentMethod"] = lava_method.value

        try:
            response = await self._client.post(
                f"{settings.payment.base_url}/v2/invoice",
                headers={"X-Api-Key": settings.payment.api_key},
                json=body,
            )
        except Exception as exc:
            raise PaymentProviderUnavailableError("LavaTop is unavailable") from exc

        if response.status_code not in (200, 201):
            raise PaymentProviderRequestError(response.text)

        data = response.json()
        return {
            "provider_invoice_id": str(data.get("id")),
            "provider_data": data,
            "invoice_url": data.get("paymentUrl"),
        }
