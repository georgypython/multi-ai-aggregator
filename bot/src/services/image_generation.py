from uuid import UUID

from src.services.common import BaseBackendService
from src.core.schemas import ImageGenerationResult


class ImageGenerationService(BaseBackendService):
    async def generate_image(
        self,
        tg_user_id: int,
        model_id: UUID,
        prompt: str,
        size: str,
        quality: str,
    ) -> ImageGenerationResult:
        response = await self._client.post(
            f"{self._base_url}/api/v1/ai/image/generations",
            params={
                "tg_user_id": str(tg_user_id),
                "model_id": str(model_id),
                "prompt": prompt,
                "size": size,
                "quality": quality,
            },
            headers=self._base_headers,
        )
        response.raise_for_status()
        return ImageGenerationResult.model_validate(response.json())

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
