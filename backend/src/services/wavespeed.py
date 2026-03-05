import asyncio
from typing import Any

from httpx import AsyncClient, HTTPStatusError, RequestError, TimeoutException

from src.core.exceptions.llm import (
    ProviderHTTPError,
    ProviderNetworkError,
    ProviderResponseFormatError,
    ProviderTimeoutError,
)
from src.core.models.enums import ImageGenerationStatus, ImageProvider
from src.core.schemas.ai import (
    ImageRequestDataSchema,
    ImageProviderResponseSchema,
)

class WaveSpeedService:
    def __init__(
        self,
        client: AsyncClient,
        api_key: str,
        base_url: str,
    ) -> None:
        self.client = client
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")
        self._base_headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }

    async def create_image_generation(
        self,
        request_data: ImageRequestDataSchema,
    ) -> ImageProviderResponseSchema:
        payload: dict[str, Any] = {
            "prompt": request_data.prompt,
        }

        if request_data.provider == ImageProvider.OPENAI:
            payload["size"] = request_data.size
            payload["quality"] = request_data.quality
        elif request_data.provider == ImageProvider.GOOGLE:
            payload["aspect_ratio"] = request_data.size
            payload["resolution"] = request_data.quality
        else:
            raise ProviderResponseFormatError(
                f"Unsupported WaveSpeed provider: {request_data.provider}"
            )

        try:
            response = await self.client.post(
                f"{self._base_url}/api/v3/{request_data.provider_model_key}",
                headers=self._base_headers,
                json=payload,
            )
            response.raise_for_status()
        except TimeoutException as exc:
            raise ProviderTimeoutError("WaveSpeed request timeout") from exc
        except HTTPStatusError as exc:
            raise ProviderHTTPError(status_code=exc.response.status_code) from exc
        except RequestError as exc:
            raise ProviderNetworkError("WaveSpeed network error") from exc

        try:
            response_data = response.json()
        except ValueError as exc:
            raise ProviderResponseFormatError(
                "WaveSpeed returned non-JSON response"
            ) from exc

        if not isinstance(response_data, dict):
            raise ProviderResponseFormatError("WaveSpeed response has invalid JSON format")

        data = response_data.get("data")
        if not isinstance(data, dict):
            raise ProviderResponseFormatError("WaveSpeed response has invalid data payload")

        urls = data.get("urls")
        if not isinstance(urls, dict):
            raise ProviderResponseFormatError("WaveSpeed response has invalid urls payload")

        generation_status: str = data.get("status")

        return ImageProviderResponseSchema(
            task_id=data.get("id"),
            model_key=data.get("model"),
            status=ImageGenerationStatus(generation_status.lower()),
            result_url=urls.get("get"),
            created_at=data.get("created_at"),
            error=data.get("error"),
        )

    async def get_image_generation_status(
        self,
        task_id: str,
    ) -> ImageProviderResponseSchema:
        try:
            response = await self.client.get(
                f"{self._base_url}/api/v3/predictions/{task_id}/result",
                headers=self._base_headers,
            )
            response.raise_for_status()
        except TimeoutException as exc:
            raise ProviderTimeoutError("WaveSpeed request timeout") from exc
        except HTTPStatusError as exc:
            raise ProviderHTTPError(status_code=exc.response.status_code) from exc
        except RequestError as exc:
            raise ProviderNetworkError("WaveSpeed network error") from exc

        try:
            response_data = response.json()
        except ValueError as exc:
            raise ProviderResponseFormatError(
                "WaveSpeed returned non-JSON response"
            ) from exc

        if not isinstance(response_data, dict):
            raise ProviderResponseFormatError("WaveSpeed response has invalid JSON format")

        data = response_data.get("data")
        if not isinstance(data, dict):
            raise ProviderResponseFormatError("WaveSpeed response has invalid data payload")

        urls = data.get("urls")
        result_url = None
        if isinstance(urls, dict):
            result_url = urls.get("get")

        generation_status: str = data.get("status")
        return ImageProviderResponseSchema(
            task_id=str(data.get("id") or task_id),
            model_key=data.get("model"),
            status=ImageGenerationStatus(generation_status.lower()),
            result_url=result_url,
            created_at=data.get("created_at"),
            error=data.get("error"),
        )

    async def poll_image_generation_status(
        self,
        task_id: str,
        poll_interval_seconds: int,
        max_attempts: int,
    ) -> ImageProviderResponseSchema:
        if max_attempts < 1:
            raise ValueError("max_attempts must be greater than 0")
        if poll_interval_seconds < 0:
            raise ValueError("poll_interval_seconds must be >= 0")

        for attempt in range(1, max_attempts + 1):
            response = await self.get_image_generation_status(task_id=task_id)
            status = response.status

            if status in (
                ImageGenerationStatus.COMPLETED,
                ImageGenerationStatus.FAILED,
            ):
                return response

            if attempt < max_attempts and poll_interval_seconds > 0:
                await asyncio.sleep(poll_interval_seconds)

        raise ProviderTimeoutError(
            f"WaveSpeed generation polling timeout: task_id={task_id}, attempts={max_attempts}"
        )