from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from backend.src.core.exceptions.generation import (
    InsufficientBalanceError,
    ProviderError,
    UserBalanceNotConfiguredError,
    VideoGenerationError,
    VideoGenerationNotCompletedError,
    ModelConfigError,
)
from src.core.models.enums import GenerationStatus, GenerationType, ModelType
from src.core.schemas.ai import (
    GenerationResultResponseDataSchema,
    GenerationRequestSchema,
    PollWaveSpeedGenerationTaskSchema,
    VideoModelConfigDataSchema,
    VideoRequestDataSchema,
)
from src.repositories import AIModelRepository, UserRepository
from src.repositories import GenerationRepository
from src.tasks.generation_tasks import poll_generation_status
from .generation_billing import GenerationBillingService
from .wavespeed import WaveSpeedService


class VideoGenerationService:
    def __init__(
        self,
        session: AsyncSession,
        user_repo: UserRepository,
        ai_model_repo: AIModelRepository,
        generation_repo: GenerationRepository,
        generation_billing_service: GenerationBillingService,
        wavespeed_service: WaveSpeedService,
        video_model_configs: dict[str, dict],
        poll_interval_seconds: int,
        poll_max_attempts: int,
    ):
        self.session = session
        self.user_repo = user_repo
        self.ai_model_repo = ai_model_repo
        self.generation_repo = generation_repo
        self.generation_billing_service = generation_billing_service
        self.video_model_configs = video_model_configs
        self.wavespeed_service = wavespeed_service
        self.poll_interval_seconds = poll_interval_seconds
        self.poll_max_attempts = poll_max_attempts

    def _get_video_model_config_fields(
        self,
        provider_model_key: str,
        duration_seconds: int | None,
        size: str | None,
    ) -> VideoModelConfigDataSchema:
        model_config = self.video_model_configs.get(provider_model_key)
        if not model_config:
            raise ModelConfigError(
                f"Video model config not found for provider_key={provider_model_key}"
            )

        durations_seconds: list[int] = model_config.get("durations_seconds")
        sizes: list[str] = model_config.get("sizes")
        provider_prices: dict[str, dict[str, float]] = model_config.get("prices_usd_by_duration")
        model_provider: str = model_config.get("provider")

        if durations_seconds and sizes and provider_prices and model_provider:
            resolved_duration_seconds = duration_seconds or durations_seconds[0]
            resolved_size = size or sizes[0]

            if resolved_duration_seconds in durations_seconds and resolved_size in sizes:
                duration_prices = provider_prices.get(str(resolved_duration_seconds))
                if duration_prices:
                    price = duration_prices.get(resolved_size)
                    if price is not None:
                        return VideoModelConfigDataSchema(
                            duration_seconds=int(resolved_duration_seconds),
                            size=resolved_size,
                            provider_cost=price,
                            provider=model_provider,
                        )

        raise ModelConfigError(
            f"Video model config is invalid for provider_key={provider_model_key}"
        )

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

            if user.balance.available_tokens <= ai_model.min_charge_tokens:
                raise InsufficientBalanceError(
                    f"Insufficient active balance for generation: available={user.balance.available_tokens}, required>{ai_model.min_charge_tokens}"
                )

            provider_model_key = ai_model.provider_key
            model_config = self._get_video_model_config_fields(
                provider_model_key=provider_model_key,
                duration_seconds=duration_seconds,
                size=size,
            )
            return VideoRequestDataSchema(
                user_id=user_id,
                ai_model_id=model_id,
                provider_model_key=provider_model_key,
                prompt=prompt,
                media_file_id=media_file_id,
                min_charge_tokens=ai_model.min_charge_tokens,
                free_requests_limit=ai_model.free_requests_limit,
                **model_config.model_dump(),
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

        generation_data = GenerationRequestSchema(
            user_id=user_id,
            ai_model_id=model_id,
            generation_type=GenerationType.VIDEO,
            hold_amount=request_data.min_charge_tokens,
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

            final_tokens_cost = 0.0
            if generation_data.hold_amount > 0:
                final_tokens_cost = (
                    await self.generation_billing_service.calculate_tokens_cost_from_provider_cost(
                        provider_cost=request_data.provider_cost,
                    )
                )

            await poll_generation_status.kiq(
                data=PollWaveSpeedGenerationTaskSchema(
                    ai_model_id=request_data.ai_model_id,
                    user_id=request_data.user_id,
                    generation_id=generation.id,
                    generation_type=generation_data.generation_type,
                    hold_amount=generation_data.hold_amount,
                    provider_cost=request_data.provider_cost,
                    wavespeed_task_id=response_create_data.task_id,
                    poll_interval_seconds=self.poll_interval_seconds,
                    max_attempts=self.poll_max_attempts,
                    current_attempt=1,
                    timeout=30,
                    final_tokens_cost=final_tokens_cost,
                    result_url=response_create_data.result_url or "",
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
            raise VideoGenerationError(
                "Unexpected video polling error"
            ) from e

        return GenerationResultResponseDataSchema(
            ai_model_id=request_data.ai_model_id,
            user_id=request_data.user_id,
            generation_id=generation.id,
            tokens_cost=final_tokens_cost,
            status=GenerationStatus.PROCESSING,
        )

    async def get_video_generation_content(
        self,
        user_id: UUID,
        generation_id: UUID,
    ) -> bytes:
        generation = await self.generation_repo.get_one(
            session=self.session,
            id=generation_id,
            user_id=user_id,
            generation_type=GenerationType.VIDEO,
            status=GenerationStatus.COMPLETED,
        )

        if not generation:
            raise ValueError(
                f"Completed video generation not found for generation_id={generation_id}"
            )

        if not generation.result_url:
            raise VideoGenerationNotCompletedError(
                "Video generation content is unavailable: result_url is empty"
            )

        return await self.wavespeed_service.download_video_bytes(url=generation.result_url)