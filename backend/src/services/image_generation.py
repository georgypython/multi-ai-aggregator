from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from src.core.logger_setup import logger
from src.exceptions.generation import (
    ImageGenerationNotCompletedError,
    ProviderError,
)
from src.exceptions.storage import StoragePresignedUrlError
from src.models.enums import (
    GenerationStatus,
    GenerationType,
    ModelType,
)
from src.schemas import (
    ImageRequestDataSchema,
    GenerationResultResponseDataSchema,
)
from src.repositories import AIModelRepository, UserRepository
from src.repositories import GenerationRepository
from .generation_billing import GenerationBillingService
from .image_profile import ImageProfileService
from .wavespeed import WaveSpeedService
from .storage import StorageService
from .video_profile import VideoProfileService


class ImageGenerationService:
    def __init__(
        self,
        session: AsyncSession,
        user_repo: UserRepository,
        ai_model_repo: AIModelRepository,
        generation_repo: GenerationRepository,
        generation_billing_service: GenerationBillingService,
        image_profile_service: ImageProfileService,
        wavespeed_service: WaveSpeedService,
        storage_service: StorageService,
    ):
        self.session = session
        self.user_repo = user_repo
        self.ai_model_repo = ai_model_repo
        self.generation_repo = generation_repo
        self.generation_billing_service = generation_billing_service
        self.image_profile_service = image_profile_service
        self.wavespeed_service = wavespeed_service
        self.storage_service = storage_service

    async def _create_and_validate_request_image_data(
        self,
        user_id: UUID,
        model_id: UUID,
        prompt: str,
        size: str | None,
        quality: str | None,
        media_file_ids: list[UUID] | None,
    ) -> ImageRequestDataSchema:
        async with self.session.begin():
            user = await self.user_repo.get_one_with_balance(
                session=self.session,
                id=user_id,
                is_active=True,
            )
            if not user:
                raise ValueError(f"Active user not found for user_id={user_id}")

            if not user.balance:
                raise ValueError(
                    f"User balance is not configured for user_id={user_id}"
                )

            ai_model = await self.ai_model_repo.get_one(
                session=self.session,
                id=model_id,
                is_active=True,
            )
            if not ai_model:
                raise ValueError(f"Active AIModel not found for model_id={model_id}")

            if ai_model.model_type != ModelType.IMAGE:
                raise ValueError(f"AIModel is not image type for model_id={model_id}")

            if not ai_model.is_active:
                raise ValueError(f"AIModel inactive for model_id={model_id}")

            media_file_urls: list[str] | None = None
            if media_file_ids:
                try:
                    resolved_media_file_urls = (
                        await self.storage_service.get_files_urls(
                            user_id=user_id,
                            media_file_ids=media_file_ids,
                        )
                    )
                    if resolved_media_file_urls:
                        media_file_urls = resolved_media_file_urls
                except (ValueError, StoragePresignedUrlError) as e:
                    logger.warning(
                        f"Error while get media_file_urls from storage for user_id={user_id}, error={e}"
                    )
                    media_file_urls = None

            raw_profile_price = (
                await self.image_profile_service.get_image_profile_with_raw_price(
                    model_id=model_id,
                    size=size,
                    quality=quality,
                )
            )

            provider_model_key = ai_model.provider_key
            if media_file_urls:
                image_edit_model_name = raw_profile_price.image_edit_model_name
                if image_edit_model_name and image_edit_model_name.strip():
                    provider_model_key = image_edit_model_name
                else:
                    logger.warning(
                        "Image edit input was provided but model has no image_edit_model_name; dropping media_file_urls "
                        f"for model_id={model_id}, user_id={user_id}"
                    )
                    media_file_urls = None

            return ImageRequestDataSchema(
                user_id=user_id,
                ai_model_id=model_id,
                generation_type=GenerationType.IMAGE,
                provider_model_key=provider_model_key,
                model_token_price_id=ai_model.token_price_id,
                hold_amount=ai_model.min_charge_tokens,
                prompt=prompt,
                media_file_urls=media_file_urls,
                free_requests_limit=ai_model.free_requests_limit,
                size=raw_profile_price.size,
                quality=raw_profile_price.quality,
                provider_cost=raw_profile_price.provider_cost,
                provider=raw_profile_price.provider,
            )

    async def generate_image(
        self,
        user_id: UUID,
        model_id: UUID,
        prompt: str,
        size: str | None,
        quality: str | None,
        media_file_ids: list[UUID] | None = None,
    ) -> GenerationResultResponseDataSchema:
        request_data = await self._create_and_validate_request_image_data(
            user_id, model_id, prompt, size, quality, media_file_ids
        )

        calc_hold_amount = await self.generation_billing_service.calculate_hold_tokens_cost_from_providers_cost(
            provider_cost=request_data.provider_cost,
            model_token_price_id=request_data.model_token_price_id,
        )

        request_data.hold_amount = calc_hold_amount
        generation = await self.generation_billing_service.prepare_generation_and_freeze_user_tokens(
            data=request_data
        )
        try:
            response_create_data = await self.wavespeed_service.create_image_generation(
                request_data=request_data
            )
            await self.generation_billing_service.set_generation_task_id(
                generation_id=generation.id,
                task_id=response_create_data.task_id,
            )

            final_tokens_cost = request_data.hold_amount
        except ProviderError:
            await self.generation_billing_service.rollback_failed_generation(
                user_id=request_data.user_id,
                hold_amount=request_data.hold_amount,
                generation_id=generation.id,
            )
            raise

        except Exception as e:
            await self.generation_billing_service.rollback_failed_generation(
                user_id=request_data.user_id,
                hold_amount=request_data.hold_amount,
                generation_id=generation.id,
            )
            raise ImageGenerationNotCompletedError(
                "Unexpected image polling error"
            ) from e

        return GenerationResultResponseDataSchema(
            ai_model_id=request_data.ai_model_id,
            user_id=request_data.user_id,
            generation_id=generation.id,
            tokens_cost=final_tokens_cost,
            status=GenerationStatus.PROCESSING,
            is_free_request=request_data.hold_amount == 0,
        )
