from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from src.exceptions.generation import (
    MediaGenerationNotCompletedError,
)
from src.models.enums import GenerationStatus, GenerationType
from src.schemas import GenerationResultResponseDataSchema
from src.repositories import GenerationRepository

from .wavespeed import WaveSpeedService


class GenerationInfoService:
    def __init__(
        self,
        session: AsyncSession,
        generation_repo: GenerationRepository,
        wavespeed_service: WaveSpeedService,
    ) -> None:
        self.session = session
        self.generation_repo = generation_repo
        self.wavespeed_service = wavespeed_service

    async def get_generation_status(
        self,
        user_id: UUID,
        generation_id: UUID,
    ) -> GenerationResultResponseDataSchema:
        generation = await self.generation_repo.get_one(
            session=self.session,
            id=generation_id,
            user_id=user_id,
        )

        if not generation:
            raise ValueError(f"not found for generation_id={generation_id}")

        return GenerationResultResponseDataSchema(
            ai_model_id=generation.ai_model_id,
            user_id=generation.user_id,
            generation_id=generation.id,
            tokens_cost=generation.charged_tokens,
            status=generation.status,
            is_free_request=generation.hold_tokens_amount == 0,
        )

    async def get_media_generation_content(
        self,
        user_id: UUID,
        generation_id: UUID,
    ) -> bytes:
        generation = await self.generation_repo.get_one(
            session=self.session,
            id=generation_id,
            user_id=user_id,
            status=GenerationStatus.COMPLETED,
        )
        if not generation or generation.generation_type not in (
            GenerationType.IMAGE,
            GenerationType.VIDEO,
        ):
            raise ValueError(
                f"Completed media generation not found or unsupported for generation_id={generation_id}"
            )

        if not generation.result_url:
            raise MediaGenerationNotCompletedError(
                "Media generation content is unavailable: result_url is empty"
            )

        return await self.wavespeed_service.download_video_bytes(
            url=generation.result_url
        )
