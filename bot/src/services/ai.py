import httpx
from uuid import UUID

from src.services.common import BaseBackendService
from src.core.schemas import (
    AIModelItem,
    ImageModelConfigResult,
    ImageModelPriceResult,
    LLMConfigResult,
)


class AIService(BaseBackendService):

    async def get_models(
        self,
        tg_user_id: int,
        model_type: str | None = "llm",
        active_only: bool = True,
    ) -> list[AIModelItem]:
        params: dict[str, str | bool] = {
            "tg_user_id": str(tg_user_id),
            "active_only": active_only,
        }
        if model_type is not None:
            params["model_type"] = model_type

        response = await self._client.get(
            f"{self._base_url}/api/v1/ai/",
            params=params,
            headers=self._base_headers,
        )
        response.raise_for_status()

        payload = response.json()
        return [AIModelItem.model_validate(item) for item in payload]

    async def get_llm_config(self, tg_user_id: int) -> LLMConfigResult:
        response = await self._client.get(
            f"{self._base_url}/api/v1/ai/llm/configs",
            params={"tg_user_id": str(tg_user_id)},
            headers=self._base_headers,
        )
        response.raise_for_status()
        return LLMConfigResult.model_validate(response.json())

    async def get_image_model_config(
        self,
        model_id: UUID,
    ) -> ImageModelConfigResult:
        response = await self._client.get(
            f"{self._base_url}/api/v1/ai/image/{model_id}",
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
            f"{self._base_url}/api/v1/ai/image/{model_id}/price",
            params={
                "tg_user_id": str(tg_user_id),
                "size": size,
                "quality": quality,
            },
            headers=self._base_headers,
        )
        response.raise_for_status()
        return ImageModelPriceResult.model_validate(response.json())
