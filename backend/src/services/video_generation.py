from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.core.logger_setup import logger
from src.exceptions.generation import (
    ProviderError,
    UserBalanceNotConfiguredError,
    AIGenerationError,
)
from src.exceptions.storage import StoragePresignedUrlError
from src.models import AIModel, User
from src.models.enums import GenerationStatus, GenerationType, ModelType
from src.schemas import (
    GenerationResultResponseDataSchema,
    VideoRequestDataSchema,
)
from src.schemas.generations import PollDbGenerationTaskSchema
from src.services.db_access import DBAccessService
from .generation_billing import GenerationBillingService
from .storage import StorageService
from .video_profile import VideoProfileService
from .wavespeed import WaveSpeedService


class VideoGenerationService(DBAccessService):
    def __init__(
        self,
        session: AsyncSession,
        generation_billing_service: GenerationBillingService,
        video_profile_service: VideoProfileService,
        wavespeed_service: WaveSpeedService,
        storage_service: StorageService,
        poll_interval_seconds: int,
        poll_max_attempts: int,
    ):
        self.session = session
        self.generation_billing_service = generation_billing_service
        self.video_profile_service = video_profile_service
        self.wavespeed_service = wavespeed_service
        self.storage_service = storage_service
        self.poll_interval_seconds = poll_interval_seconds
        self.poll_max_attempts = poll_max_attempts

    async def _get_user_with_balance(self, *, user_id: UUID) -> User | None:
        stmt = (
            select(User)
            .options(selectinload(User.balance))
            .filter_by(id=user_id, is_active=True)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def _create_and_validate_request_video_data(
        self,
        user_id: UUID,
        model_id: UUID,
        prompt: str,
        duration_seconds: int | None,
        media_file_id: UUID | None,
    ) -> VideoRequestDataSchema:
        async with self.session.begin():
            user = await self._get_user_with_balance(user_id=user_id)
            if not user:
                raise ValueError(f"Active user not found for user_id={user_id}")

            if not user.balance:
                raise UserBalanceNotConfiguredError(
                    f"User balance is not configured for user_id={user_id}"
                )

            ai_model = await self.get_one(
                model=AIModel,
                id=model_id,
                is_active=True,
            )
            if not ai_model:
                raise ValueError(f"Active AIModel not found for model_id={model_id}")

            if ai_model.model_type != ModelType.VIDEO:
                raise ValueError(f"AIModel is not video type for model_id={model_id}")

            if not ai_model.is_active:
                raise ValueError(f"AIModel inactive for model_id={model_id}")

            media_file_url: str | None = None
            if media_file_id:
                try:
                    resolved_media_file_urls = (
                        await self.storage_service.get_files_urls(
                            user_id=user_id,
                            media_file_ids=[media_file_id],
                        )
                    )
                    if resolved_media_file_urls:
                        media_file_url = resolved_media_file_urls[0]
                except (ValueError, StoragePresignedUrlError) as e:
                    logger.warning(
                        f"Error while get media_file_url from storage for user_id={user_id}, media_file_id={media_file_id}, error={e}"
                    )
                    media_file_url = None

            raw_profile_price = (
                await self.video_profile_service.get_video_profile_with_raw_price(
                    model_id=model_id,
                    duration_seconds=duration_seconds,
                )
            )

            request_provider_model_key = ai_model.provider_key
            if media_file_url:
                image_edit_model_name = raw_profile_price.image_edit_model_name
                if image_edit_model_name and image_edit_model_name.strip():
                    request_provider_model_key = image_edit_model_name
                else:
                    logger.warning(
                        "Video image-to-video input was provided but model has no image_edit_model_name; dropping media_file_url "
                        f"for model_id={model_id}, user_id={user_id}"
                    )
                    media_file_url = None

            return VideoRequestDataSchema(
                user_id=user_id,
                ai_model_id=model_id,
                generation_type=GenerationType.VIDEO,
                provider_model_key=request_provider_model_key,
                prompt=prompt,
                model_token_price_id=ai_model.token_price_id,
                hold_amount=ai_model.min_charge_tokens,
                media_file_url=media_file_url,
                free_requests_limit=ai_model.free_requests_limit,
                duration_seconds=raw_profile_price.duration_seconds,
                provider_cost=raw_profile_price.provider_cost,
                provider=raw_profile_price.provider,
                user_tg_id=user.telegram_id,
            )

    async def generate_video(
        self,
        user_id: UUID,
        model_id: UUID,
        prompt: str,
        duration_seconds: int | None,
        media_file_id: UUID | None = None,
    ) -> GenerationResultResponseDataSchema:
        request_data = await self._create_and_validate_request_video_data(
            user_id=user_id,
            model_id=model_id,
            prompt=prompt,
            duration_seconds=duration_seconds,
            media_file_id=media_file_id,
        )

        async with self.session.begin():
            calc_hold_amount = await self.generation_billing_service.calculate_hold_tokens_cost_from_providers_cost(
                provider_cost=request_data.provider_cost,
                model_token_price_id=request_data.model_token_price_id,
            )

        request_data.hold_amount = calc_hold_amount

        generation = await self.generation_billing_service.prepare_generation_and_freeze_user_tokens(
            data=request_data
        )
        try:
            response_create_data = await self.wavespeed_service.create_video_generation(
                request_data=request_data,
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
            raise AIGenerationError("Unexpected video polling error") from e

        from src.tasks.poll_db_generation_status import poll_db_generation_status

        await poll_db_generation_status.kiq(
            data=PollDbGenerationTaskSchema(
                poll_interval_seconds=self.poll_interval_seconds,
                max_attempts=self.poll_max_attempts,
                current_attempt=1,
                user_tg_id=request_data.user_tg_id,
                ai_model_id=request_data.ai_model_id,
                generation_id=generation.id,
                generation_type=generation.generation_type,
                model_token_price_id=request_data.model_token_price_id,
                hold_amount=final_tokens_cost,
                provider_cost=request_data.provider_cost,
                final_tokens_cost=final_tokens_cost,
            ),
            api_key=self.wavespeed_service.api_key,
            base_url=self.wavespeed_service.base_url,
        )

        return GenerationResultResponseDataSchema(
            ai_model_id=request_data.ai_model_id,
            user_id=request_data.user_id,
            generation_id=generation.id,
            tokens_cost=final_tokens_cost,
            status=GenerationStatus.PROCESSING,
            is_free_request=request_data.hold_amount == 0,
        )
