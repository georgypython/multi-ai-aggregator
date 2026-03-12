import asyncio
from uuid import UUID

from src.services.common import BaseBackendService
from src.core.schemas import ImageGenerationResult, UploadMediaImagesResult


class ImageGenerationService(BaseBackendService):
    async def generate_image(
        self,
        tg_user_id: int,
        model_id: UUID,
        prompt: str,
        size: str,
        quality: str,
        media_file_ids: list[UUID] | None = None,
    ) -> ImageGenerationResult:
        payload: dict[str, object] = {
            "model_id": str(model_id),
            "prompt": prompt,
            "size": size,
            "quality": quality,
        }
        if media_file_ids:
            payload["media_file_ids"] = [str(media_file_id) for media_file_id in media_file_ids]

        response = await self._client.post(
            f"{self._base_url}/api/v1/ai/image/generations",
            params={"tg_user_id": str(tg_user_id)},
            headers=self._base_headers,
            json=payload,
        )
        response.raise_for_status()
        return ImageGenerationResult.model_validate(response.json())

    async def upload_image(
        self,
        tg_user_id: int,
        file: tuple[str, bytes, str],
    ) -> UploadMediaImagesResult:
        filename, file_bytes, content_type = file
        response = await self._client.post(
            f"{self._base_url}/api/v1/ai/media/images",
            params={"tg_user_id": str(tg_user_id)},
            headers=self._base_headers,
            files={"file": (filename, file_bytes, content_type)},
        )
        response.raise_for_status()
        return UploadMediaImagesResult.model_validate(response.json())

    async def get_image_generation_content(
        self,
        tg_user_id: int,
        generation_id: UUID,
    ) -> bytes:
        response = await self._client.get(
            f"{self._base_url}/api/v1/ai/image/generations/{generation_id}/content",
            params={"tg_user_id": str(tg_user_id)},
            headers=self._base_headers,
        )
        response.raise_for_status()

        if not response.content:
            raise ValueError("Empty image content from backend")

        return response.content

    async def get_image_generation_status(
        self,
        tg_user_id: int,
        generation_id: UUID,
    ) -> ImageGenerationResult:
        response = await self._client.get(
            f"{self._base_url}/api/v1/ai/image/generations/{generation_id}",
            params={"tg_user_id": str(tg_user_id)},
            headers=self._base_headers,
        )
        response.raise_for_status()
        return ImageGenerationResult.model_validate(response.json())

    async def wait_for_image_generation_status(
        self,
        tg_user_id: int,
        generation_id: UUID,
        poll_interval_seconds: float = 2.0,
        max_attempts: int = 60,
    ) -> ImageGenerationResult:
        for _ in range(max_attempts):
            result = await self.get_image_generation_status(
                tg_user_id=tg_user_id,
                generation_id=generation_id,
            )

            if result.status in ("completed", "failed", "canceled"):
                return result

            await asyncio.sleep(poll_interval_seconds)

        raise TimeoutError("Image generation status polling timed out")
