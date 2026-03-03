from uuid import UUID

import httpx
from pydantic import BaseModel


class BackendAPIError(Exception):
    def __init__(self, status_code: int, detail: str) -> None:
        self.status_code = status_code
        self.detail = detail
        super().__init__(detail)


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


class AIService:
    def __init__(
        self,
        base_url: str,
        api_key: str,
        timeout_seconds: float = 15.0,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._api_key = api_key
        self._client = httpx.AsyncClient(timeout=timeout_seconds)

    async def aclose(self) -> None:
        await self._client.aclose()

    @staticmethod
    def _extract_error_detail(response: httpx.Response) -> str:
        try:
            payload = response.json()
        except ValueError:
            return f"HTTP {response.status_code}"

        if isinstance(payload, dict):
            detail = payload.get("detail")
            if isinstance(detail, str) and detail.strip():
                return detail

        return f"HTTP {response.status_code}"

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
            headers={"Authorization": f"Bearer {self._api_key}"},
        )
        try:
            response.raise_for_status()
        except httpx.HTTPStatusError:
            raise BackendAPIError(
                status_code=response.status_code,
                detail=self._extract_error_detail(response),
            )

        payload = response.json()
        return [AIModelItem.model_validate(item) for item in payload]

    async def generate_llm_response(
        self,
        tg_user_id: int,
        model_id: UUID,
        prompt: str,
    ) -> LLMGenerationResult:
        response = await self._client.post(
            f"{self._base_url}/api/v1/ai/llm/generations",
            params={
                "tg_user_id": str(tg_user_id),
                "model_id": str(model_id),
                "prompt": prompt,
            },
            headers={"Authorization": f"Bearer {self._api_key}"},
        )
        try:
            response.raise_for_status()
        except httpx.HTTPStatusError:
            raise BackendAPIError(
                status_code=response.status_code,
                detail=self._extract_error_detail(response),
            )
        return LLMGenerationResult.model_validate(response.json())

    async def get_llm_config(self, tg_user_id: int) -> LLMConfigResult:
        response = await self._client.get(
            f"{self._base_url}/api/v1/ai/llm/configs",
            params={"tg_user_id": str(tg_user_id)},
            headers={"Authorization": f"Bearer {self._api_key}"},
        )
        try:
            response.raise_for_status()
        except httpx.HTTPStatusError:
            raise BackendAPIError(
                status_code=response.status_code,
                detail=self._extract_error_detail(response),
            )
        return LLMConfigResult.model_validate(response.json())

    async def create_or_update_llm_config(
        self,
        tg_user_id: int,
        *,
        temperature: float | None = None,
        instructions: str | None = None,
    ) -> LLMConfigResult:
        payload: dict[str, float | str] = {}
        if temperature is not None:
            payload["temperature"] = temperature
        if instructions is not None:
            payload["instructions"] = instructions

        response = await self._client.post(
            f"{self._base_url}/api/v1/ai/llm/configs",
            params={"tg_user_id": str(tg_user_id)},
            json=payload,
            headers={"Authorization": f"Bearer {self._api_key}"},
        )
        try:
            response.raise_for_status()
        except httpx.HTTPStatusError:
            raise BackendAPIError(
                status_code=response.status_code,
                detail=self._extract_error_detail(response),
            )
        return LLMConfigResult.model_validate(response.json())
