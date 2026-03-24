from uuid import UUID

from src.services.common import BaseBackendService
from src.core.schemas import VideoGenerationResult


class VideoGenerationService(BaseBackendService):
    async def generate_video(
        self,
        tg_user_id: int,
        model_id: UUID,
        prompt: str,
        duration_seconds: int,
        size: str,
    ) -> VideoGenerationResult:
        response = await self._client.post(
            f"{self._base_url}/api/v1/ai/video/generations",
            params={
                "tg_user_id": str(tg_user_id),
                "model_id": str(model_id),
                "prompt": prompt,
                "duration_seconds": duration_seconds,
                "size": size,
            },
            headers=self._base_headers,
        )
        response.raise_for_status()
        return VideoGenerationResult.model_validate(response.json())

    async def get_video_generation_content(
        self,
        tg_user_id: int,
        generation_id: UUID,
    ) -> bytes:
        response = await self._client.get(
            f"{self._base_url}/api/v1/ai/video/generations/{generation_id}/content",
            params={"tg_user_id": str(tg_user_id)},
            headers=self._base_headers,
        )
        response.raise_for_status()

        if not response.content:
            raise ValueError("Empty video content from backend")

        return response.content
