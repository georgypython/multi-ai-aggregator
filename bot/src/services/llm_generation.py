from uuid import UUID

from src.services.common import BaseBackendService
from src.core.schemas import LLMConfigResult, LLMGenerationResult


class LLMGenerationService(BaseBackendService):
    async def generate_llm_response(
        self,
        tg_user_id: int,
        model_id: UUID,
        prompt: str,
    ) -> LLMGenerationResult:
        response = await self._client.post(
            f"{self._base_url}/api/v1/ai/{model_id}/generate/llm",
            params={"tg_user_id": tg_user_id},
            json={"prompt": prompt},
            headers=self._base_headers,
        )
        response.raise_for_status()
        return LLMGenerationResult.model_validate(response.json())

    async def create_or_update_llm_config(
        self,
        tg_user_id: int,
        temperature: float | None = None,
        instructions: str | None = None,
    ) -> LLMConfigResult:
        payload: dict[str, float | str] = {}
        if temperature is not None:
            payload["temperature"] = temperature
        if instructions is not None:
            payload["instructions"] = instructions

        response = await self._client.post(
            f"{self._base_url}/api/v1/users/me/llm-config",
            params={"tg_user_id": tg_user_id},
            json=payload,
            headers=self._base_headers,
        )
        response.raise_for_status()
        return LLMConfigResult.model_validate(response.json())
