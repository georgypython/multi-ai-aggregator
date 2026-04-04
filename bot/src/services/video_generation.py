import asyncio
from uuid import UUID

import httpx

from src.services.common import BaseBackendService
from src.core.schemas import (
    GenerationStatus,
    UploadMediaImagesResult,
    VideoGenerationResult,
)


class VideoGenerationService(BaseBackendService):
    async def generate_video(
        self,
        tg_user_id: int,
        model_id: UUID,
        prompt: str,
        duration_seconds: int,
        media_file_id: UUID | None = None,
    ) -> VideoGenerationResult:
        payload: dict[str, object] = {
            "prompt": prompt,
            "duration_seconds": duration_seconds,
        }
        if media_file_id:
            payload["media_file_id"] = str(media_file_id)

        response = await self._client.post(
            f"{self._base_url}/api/v1/ai/{model_id}/generate/video",
            params={"tg_user_id": tg_user_id},
            json=payload,
            headers=self._base_headers,
        )
        response.raise_for_status()
        return VideoGenerationResult.model_validate(response.json())

    async def upload_image(
        self,
        tg_user_id: int,
        file: tuple[str, bytes, str],
    ) -> UploadMediaImagesResult:
        filename, file_bytes, content_type = file
        response = await self._client.post(
            f"{self._base_url}/api/v1/media/images",
            params={"tg_user_id": tg_user_id},
            headers=self._base_headers,
            files={"file": (filename, file_bytes, content_type)},
        )
        response.raise_for_status()
        return UploadMediaImagesResult.model_validate(response.json())

    async def get_video_generation_status(
        self,
        tg_user_id: int,
        generation_id: UUID,
    ) -> VideoGenerationResult:
        response = await self._client.get(
            f"{self._base_url}/api/v1/generations/{generation_id}",
            params={"tg_user_id": tg_user_id},
            headers=self._base_headers,
        )
        response.raise_for_status()
        return VideoGenerationResult.model_validate(response.json())

    async def wait_for_video_generation_status(
        self,
        tg_user_id: int,
        generation_id: UUID,
        poll_interval_seconds: float = 2.0,
        max_attempts: int = 60,
    ) -> VideoGenerationResult:
        for _ in range(max_attempts):
            try:
                result = await self.get_video_generation_status(
                    tg_user_id=tg_user_id,
                    generation_id=generation_id,
                )
            except httpx.HTTPStatusError as exc:
                # Tolerate transient not-found during first polls.
                if exc.response.status_code == 404:
                    await asyncio.sleep(poll_interval_seconds)
                    continue
                raise

            if result.status in (
                GenerationStatus.COMPLETED,
                GenerationStatus.FAILED,
                GenerationStatus.CANCELED,
            ):
                return result

            await asyncio.sleep(poll_interval_seconds)

        raise TimeoutError("Video generation status polling timed out")

    async def get_video_generation_content(
        self,
        tg_user_id: int,
        generation_id: UUID,
    ) -> bytes:
        response = await self._client.get(
            f"{self._base_url}/api/v1/generations/{generation_id}/content",
            params={"tg_user_id": tg_user_id},
            headers=self._base_headers,
        )
        response.raise_for_status()

        if not response.content:
            raise ValueError("Empty video content from backend")

        return response.content
