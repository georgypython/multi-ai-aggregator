from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from src.exceptions.generation import (
    ProviderError,
    UserBalanceNotConfiguredError,
    AIGenerationError,
)
from src.models.enums import GenerationStatus, GenerationType, ModelType
from src.schemas import (
    GenerationResultResponseDataSchema,
    GenerationRequestSchema,
    PollWaveSpeedGenerationTaskSchema,
    VideoRequestDataSchema,
)
from src.repositories import AIModelRepository, UserRepository
from src.repositories import GenerationRepository
from src.tasks.generation_tasks import poll_generation_status
from .generation_billing import GenerationBillingService
from .video_profile import VideoProfileService
from .wavespeed import WaveSpeedService


class VideoGenerationService:
    def __init__(
        self,
        session: AsyncSession,
        user_repo: UserRepository,
        ai_model_repo: AIModelRepository,
        generation_repo: GenerationRepository,
        generation_billing_service: GenerationBillingService,
        video_profile_service: VideoProfileService,
        wavespeed_service: WaveSpeedService,
        poll_interval_seconds: int,
        poll_max_attempts: int,
    ):
        self.session = session
        self.user_repo = user_repo
        self.ai_model_repo = ai_model_repo
        self.generation_repo = generation_repo
        self.generation_billing_service = generation_billing_service
        self.video_profile_service = video_profile_service
        self.wavespeed_service = wavespeed_service
        self.poll_interval_seconds = poll_interval_seconds
        self.poll_max_attempts = poll_max_attempts

    async def _create_and_validate_request_video_data(
        self,
        user_id: UUID,
        model_id: UUID,
        prompt: str,
        duration_seconds: int | None,
        size: str | None,
        media_file_id: UUID | None,
    ) -> VideoRequestDataSchema:
        async with self.session.begin():
            user = await self.user_repo.get_one_with_balance(
                session=self.session,
                id=user_id,
                is_active=True,
            )
            if not user:
                raise ValueError(f"Active user not found for user_id={user_id}")

            if not user.balance:
                raise UserBalanceNotConfiguredError(
                    f"User balance is not configured for user_id={user_id}"
                )

            ai_model = await self.ai_model_repo.get_one(
                session=self.session,
                id=model_id,
                is_active=True,
            )
            if not ai_model:
                raise ValueError(f"Active AIModel not found for model_id={model_id}")

            if ai_model.model_type != ModelType.VIDEO:
                raise ValueError(f"AIModel is not video type for model_id={model_id}")

            if not ai_model.is_active:
                raise ValueError(f"AIModel inactive for model_id={model_id}")

            raw_profile_price = (
                await self.video_profile_service.get_video_profile_with_raw_price(
                    model_id=model_id,
                    duration_seconds=duration_seconds,
                    size=size,
                )
            )
            return VideoRequestDataSchema(
                user_id=user_id,
                ai_model_id=model_id,
                provider_model_key=ai_model.provider_key,
                prompt=prompt,
                model_token_price_id=ai_model.token_price_id,
                media_file_id=media_file_id,
                min_charge_tokens=ai_model.min_charge_tokens,
                free_requests_limit=ai_model.free_requests_limit,
                duration_seconds=raw_profile_price.duration_seconds,
                size=raw_profile_price.size,
                provider_cost=raw_profile_price.provider_cost,
                provider=raw_profile_price.provider,
            )

    async def generate_video(
        self,
        user_id: UUID,
        model_id: UUID,
        prompt: str,
        duration_seconds: int | None,
        size: str | None,
        media_file_id: UUID | None = None,
    ) -> GenerationResultResponseDataSchema:
        request_data = await self._create_and_validate_request_video_data(
            user_id=user_id,
            model_id=model_id,
            prompt=prompt,
            duration_seconds=duration_seconds,
            size=size,
            media_file_id=media_file_id,
        )

        if request_data.media_file_id:
            pass

        hold_amount = await self.generation_billing_service.calculate_hold_tokens_cost_from_providers_cost(
            provider_cost=request_data.provider_cost,
            model_token_price_id=request_data.model_token_price_id,
            min_hold_amount=request_data.min_charge_tokens,
        )

        generation_data = GenerationRequestSchema(
            user_id=user_id,
            ai_model_id=model_id,
            generation_type=GenerationType.VIDEO,
            hold_amount=hold_amount,
            free_requests_limit=request_data.free_requests_limit,
        )
        generation = await self.generation_billing_service.prepare_generation_and_freeze_user_tokens(
            data=generation_data
        )
        try:
            response_create_data = await self.wavespeed_service.create_video_generation(
                request_data=request_data,
            )
            await self.generation_billing_service.set_generation_task_id(
                generation_id=generation.id,
                task_id=response_create_data.task_id,
            )

            final_tokens_cost = (
                await self.generation_billing_service.calculate_final_tokens_cost(
                    provider_cost=request_data.provider_cost,
                    model_token_price_id=request_data.model_token_price_id,
                    hold_amount=generation_data.hold_amount,
                )
            )

            await poll_generation_status.kiq(
                data=PollWaveSpeedGenerationTaskSchema(
                    ai_model_id=request_data.ai_model_id,
                    user_id=request_data.user_id,
                    generation_id=generation.id,
                    generation_type=generation_data.generation_type,
                    model_token_price_id=request_data.model_token_price_id,
                    hold_amount=generation_data.hold_amount,
                    provider_cost=request_data.provider_cost,
                    wavespeed_task_id=response_create_data.task_id,
                    poll_interval_seconds=self.poll_interval_seconds,
                    max_attempts=self.poll_max_attempts,
                    current_attempt=1,
                    timeout=30,
                    final_tokens_cost=final_tokens_cost,
                    result_url=response_create_data.result_url,
                ),
                api_key=self.wavespeed_service._api_key,
                base_url=self.wavespeed_service._base_url,
            )
        except ProviderError:
            await self.generation_billing_service.rollback_failed_generation(
                user_id=generation_data.user_id,
                hold_amount=generation_data.hold_amount,
                generation_id=generation.id,
            )
            raise
        except Exception as e:
            await self.generation_billing_service.rollback_failed_generation(
                user_id=generation_data.user_id,
                hold_amount=generation_data.hold_amount,
                generation_id=generation.id,
            )
            raise AIGenerationError("Unexpected video polling error") from e

        return GenerationResultResponseDataSchema(
            ai_model_id=request_data.ai_model_id,
            user_id=request_data.user_id,
            generation_id=generation.id,
            tokens_cost=final_tokens_cost,
            status=GenerationStatus.PROCESSING,
            is_free_request=generation_data.hold_amount == 0,
        )
