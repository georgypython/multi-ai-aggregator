from uuid import UUID

from src.services.common import BaseBackendService
from src.core.schemas import (
    AIModelItem,
    ImageModelConfigResult,
    ImageModelPriceResult,
    InvoiceCreateResult,
    LLMConfigResult,
    PaymentMethodsResult,
    PaymentProductsResult,
    UserBalanceResult,
    VideoModelConfigResult,
    VideoModelPriceResult,
)


class AIService(BaseBackendService):
    async def get_models(
        self,
        tg_user_id: int,
        model_type: str | None = "llm",
        active_only: bool = True,
    ) -> list[AIModelItem]:
        params: dict[str, int | str | bool] = {
            "tg_user_id": tg_user_id,
            "active_only": active_only,
        }
        if model_type is not None:
            params["model_type"] = model_type

        response = await self._client.get(
            f"{self.base_url}/api/v1/ai/",
            params=params,
            headers=self._base_headers,
        )
        response.raise_for_status()

        payload = response.json()
        return [AIModelItem.model_validate(item) for item in payload]

    async def get_llm_config(self, tg_user_id: int) -> LLMConfigResult:
        response = await self._client.get(
            f"{self.base_url}/api/v1/users/me/llm-config",
            params={"tg_user_id": tg_user_id},
            headers=self._base_headers,
        )
        response.raise_for_status()
        return LLMConfigResult.model_validate(response.json())

    async def get_image_model_config(
        self,
        tg_user_id: int,
        model_id: UUID,
    ) -> ImageModelConfigResult:
        response = await self._client.get(
            f"{self.base_url}/api/v1/ai/{model_id}/profile/image",
            params={"tg_user_id": tg_user_id},
            headers=self._base_headers,
        )
        response.raise_for_status()
        return ImageModelConfigResult.model_validate(response.json())

    async def get_image_model_price(
        self,
        tg_user_id: int,
        model_id: UUID,
        size: str,
        quality: str,
    ) -> ImageModelPriceResult:
        response = await self._client.get(
            f"{self.base_url}/api/v1/ai/{model_id}/price/image",
            params={
                "tg_user_id": tg_user_id,
                "size": size,
                "quality": quality,
            },
            headers=self._base_headers,
        )
        response.raise_for_status()
        return ImageModelPriceResult.model_validate(response.json())

    async def get_video_model_config(
        self,
        tg_user_id: int,
        model_id: UUID,
    ) -> VideoModelConfigResult:
        response = await self._client.get(
            f"{self.base_url}/api/v1/ai/{model_id}/profile/video",
            params={"tg_user_id": tg_user_id},
            headers=self._base_headers,
        )
        response.raise_for_status()
        return VideoModelConfigResult.model_validate(response.json())

    async def get_video_model_price(
        self,
        tg_user_id: int,
        model_id: UUID,
        duration_seconds: int,
    ) -> VideoModelPriceResult:
        response = await self._client.get(
            f"{self.base_url}/api/v1/ai/{model_id}/price/video",
            params={
                "tg_user_id": tg_user_id,
                "duration_seconds": duration_seconds,
            },
            headers=self._base_headers,
        )
        response.raise_for_status()
        return VideoModelPriceResult.model_validate(response.json())

    async def get_user_balance(
        self,
        tg_user_id: int,
    ) -> UserBalanceResult:
        response = await self._client.get(
            f"{self.base_url}/api/v1/users/me/balance",
            params={"tg_user_id": tg_user_id},
            headers=self._base_headers,
        )
        response.raise_for_status()
        return UserBalanceResult.model_validate(response.json())

    async def get_payment_products(
        self,
        tg_user_id: int,
    ) -> PaymentProductsResult:
        response = await self._client.get(
            f"{self.base_url}/api/v1/invoice/products",
            params={"tg_user_id": tg_user_id},
            headers=self._base_headers,
        )
        response.raise_for_status()
        return PaymentProductsResult.model_validate(response.json())

    async def get_payment_methods(
        self,
        tg_user_id: int,
    ) -> PaymentMethodsResult:
        response = await self._client.get(
            f"{self.base_url}/api/v1/invoice/methods",
            params={"tg_user_id": tg_user_id},
            headers=self._base_headers,
        )
        response.raise_for_status()
        return PaymentMethodsResult.model_validate(response.json())

    async def create_invoice(
        self,
        *,
        tg_user_id: int,
        plan_id: UUID | str,
        payment_method: str = "card_ru",
    ) -> InvoiceCreateResult:
        response = await self._client.post(
            f"{self.base_url}/api/v1/invoice",
            params={"tg_user_id": tg_user_id},
            headers=self._base_headers,
            json={
                "plan_id": str(plan_id),
                "payment_method": payment_method,
            },
        )
        response.raise_for_status()
        return InvoiceCreateResult.model_validate(response.json())
