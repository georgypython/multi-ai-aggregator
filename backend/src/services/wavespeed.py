import asyncio
from typing import Any

from httpx import AsyncClient, HTTPStatusError, RequestError, TimeoutException

from src.core.exceptions.llm import (
    ProviderHTTPError,
    ProviderNetworkError,
    ProviderResponseFormatError,
    ProviderTimeoutError,
)
from src.core.models.enums import GenerationStatus, ModelProvider
from src.core.schemas.ai import (
    ImageRequestDataSchema,
    WavespeedGenerationResponseSchema,
    VideoRequestDataSchema,
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

    async def _request(
        self,
        method: str,
        url: str,
        **kwargs: Any,
    ):
        try:
            response = await self.client.request(method=method, url=url, **kwargs)
            response.raise_for_status()
            return response
        except TimeoutException as exc:
            raise ProviderTimeoutError("WaveSpeed request timeout") from exc
        except HTTPStatusError as exc:
            raise ProviderHTTPError(status_code=exc.response.status_code) from exc
        except RequestError as exc:
            raise ProviderNetworkError("WaveSpeed network error") from exc

    @staticmethod
    def _parse_response_data(payload: dict[str, Any]) -> dict[str, Any]:
        data = payload.get("data")
        if not isinstance(data, dict):
            raise ProviderResponseFormatError("WaveSpeed response has invalid data payload")
        return data

    @staticmethod
    def _pick_output_url(payload: dict[str, Any]) -> str | None:
        data = payload.get("data")
        candidates: list[dict[str, Any]] = [payload]
        if isinstance(data, dict):
            candidates.append(data)

        for source in candidates:
            outputs = source.get("outputs")
            if isinstance(outputs, list) and outputs:
                first = outputs[0]
                if isinstance(first, str) and first.strip():
                    return first.strip()

            result_url = source.get("result_url")
            if isinstance(result_url, str) and result_url.strip():
                return result_url.strip()

        return None

    async def download_image_bytes(self, url: str) -> bytes:
        response = await self._request("GET", url, headers=self._base_headers)
        payload = response.json()

        output_url = self._pick_output_url(payload)
        if not output_url:
            raise ProviderResponseFormatError("WaveSpeed result endpoint returned JSON without outputs")

        response = await self._request("GET", output_url, headers=self._base_headers)
        if not response.content:
            raise ProviderResponseFormatError("WaveSpeed output image body is empty")

        return response.content

    async def download_video_bytes(self, url: str) -> bytes:
        return await self.download_image_bytes(url=url)

    async def create_image_generation(
        self,
        request_data: ImageRequestDataSchema,
    ) -> WavespeedGenerationResponseSchema:
        payload: dict[str, Any] = {
            "prompt": request_data.prompt,
        }

        if request_data.provider == ModelProvider.OPENAI:
            payload["size"] = request_data.size
            payload["quality"] = request_data.quality
        elif request_data.provider == ModelProvider.GOOGLE:
            payload["aspect_ratio"] = request_data.size
            payload["resolution"] = request_data.quality
        else:
            raise ProviderResponseFormatError(
                f"Unsupported WaveSpeed provider: {request_data.provider}"
            )

        return await self._create_generation_request(
            provider_model_key=request_data.provider_model_key,
            payload=payload,
        )

    async def create_video_generation(
        self,
        request_data: VideoRequestDataSchema,
    ) -> WavespeedGenerationResponseSchema:
        payload: dict[str, Any] = {
            "prompt": request_data.prompt,
            "duration": request_data.duration_seconds,
        }

        if request_data.provider == ModelProvider.OPENAI:
            payload["size"] = request_data.size
        elif request_data.provider == ModelProvider.GOOGLE:
            payload["aspect_ratio"] = request_data.size
        else:
            raise ProviderResponseFormatError(
                f"Unsupported WaveSpeed provider: {request_data.provider}"
            )

        return await self._create_generation_request(
            provider_model_key=request_data.provider_model_key,
            payload=payload,
        )

    async def _create_generation_request(
        self,
        provider_model_key: str,
        payload: dict[str, Any],
    ) -> WavespeedGenerationResponseSchema:
        response = await self._request(
            "POST",
            f"{self._base_url}/api/v3/{provider_model_key}",
            headers=self._base_headers,
            json=payload,
        )
        response_data = response.json()
        data = self._parse_response_data(response_data)

        generation_status: str = data.get("status")
        urls = data.get("urls") if isinstance(data.get("urls"), dict) else {}
        task_id = str(data.get("id") or "")
        if not task_id:
            raise ProviderResponseFormatError("WaveSpeed response does not contain task id")

        return WavespeedGenerationResponseSchema(
            task_id=task_id,
            model_key=data.get("model"),
            status=GenerationStatus(generation_status.lower()),
            result_url=urls.get("get"),
            created_at=data.get("created_at"),
            error=data.get("error"),
        )

    async def get_image_generation_status(
        self,
        task_id: str,
    ) -> WavespeedGenerationResponseSchema:
        response = await self._request(
            "GET",
            f"{self._base_url}/api/v3/predictions/{task_id}/result",
            headers=self._base_headers,
        )
        response_data = response.json()
        data = self._parse_response_data(response_data)

        urls = data.get("urls") if isinstance(data.get("urls"), dict) else {}
        result_url = None
        if isinstance(urls, dict):
            result_url = urls.get("get")

        generation_status: str = data.get("status")
        return WavespeedGenerationResponseSchema(
            task_id=str(data.get("id") or task_id),
            model_key=data.get("model"),
            status=GenerationStatus(generation_status.lower()),
            result_url=result_url,
            created_at=data.get("created_at"),
            error=data.get("error"),
        )

    async def poll_generation_status(
        self,
        task_id: str,
        poll_interval_seconds: int,
        max_attempts: int,
    ) -> WavespeedGenerationResponseSchema:
        if max_attempts < 1:
            raise ValueError("max_attempts must be greater than 0")
        if poll_interval_seconds < 0:
            raise ValueError("poll_interval_seconds must be >= 0")

        for attempt in range(1, max_attempts + 1):
            response = await self.get_image_generation_status(task_id=task_id)
            status = response.status

            if status in (
                GenerationStatus.COMPLETED,
                GenerationStatus.FAILED,
            ):
                return response

            if attempt < max_attempts and poll_interval_seconds > 0:
                await asyncio.sleep(poll_interval_seconds)

        raise ProviderTimeoutError(
            f"WaveSpeed generation polling timeout: task_id={task_id}, attempts={max_attempts}"
        )
