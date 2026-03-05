from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from src.core.exceptions.image import (
    ImageGenerationFinalizeError,
    ImageGenerationNotCompletedError,
    ImageModelConfigError,
)
from src.core.exceptions.llm import ProviderError
from src.core.models.enums import GenerationType, ImageGenerationStatus, ModelType
from src.core.schemas.ai import (
    GenerationResultSchema,
    ImageProviderResponseSchema,
    ImageRequestDataSchema,
    ImageResultResponseDataSchema,
    ImageModelConfigDataSchema,
    GenerationRequestSchema,
)
from src.repositories import AIModelRepository, UserRepository
from .generation_billing import GenerationBillingService
from .wavespeed import WaveSpeedService
from src.core.config import settings


class ImageGenerationService:
    def __init__(
        self,
        session: AsyncSession,
        user_repo: UserRepository,
        ai_model_repo: AIModelRepository,
        generation_billing_service: GenerationBillingService,
        wavespeed_service: WaveSpeedService,
        image_model_configs: dict[str, dict],
    ):
        self.session = session
        self.user_repo = user_repo
        self.ai_model_repo = ai_model_repo
        self.generation_billing_service = generation_billing_service
        self.image_model_configs = image_model_configs
        self.wavespeed_service = wavespeed_service

    def _get_image_model_config_fields(
        self,
        provider_model_key: str,
        size: str | None,
        quality: str | None,
    ) -> ImageModelConfigDataSchema:
        model_config = self.image_model_configs.get(provider_model_key)
        if not model_config:
            raise ImageModelConfigError(
                f"Image model config not found for provider_key={provider_model_key}"
            )

        sizes: list[str] = model_config.get("sizes")
        qualities: list[str] = model_config.get("qualities")
        provider_prices: dict[str, dict[str, float]] = model_config.get("prices_usd")
        model_provider: str = model_config.get("provider")

        if sizes and qualities and provider_prices and model_provider:
            resolved_size = size or sizes[0]
            resolved_quality = quality or qualities[0]

            if resolved_size in sizes and resolved_quality in qualities:
                prices = provider_prices.get(resolved_quality)
                if prices:
                    price = prices.get(resolved_size)
                    if price is not None:
                        return ImageModelConfigDataSchema(
                            size=resolved_size,
                            quality=resolved_quality,
                            provider_cost=price,
                            provider=model_provider,
                        )

        raise ImageModelConfigError(
            f"Image model config is invalid for provider_key={provider_model_key}"
        )
        
    async def _create_and_validate_request_image_data(
        self,
        user_id: UUID,
        model_id: UUID,
        prompt: str,
        size: str | None,
        quality: str | None,
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

            if user.balance.available_tokens <= ai_model.min_charge_tokens:
                raise ValueError(
                    f"Insufficient active balance for generation: available={user.balance.available_tokens}, required>{ai_model.min_charge_tokens}"
                )

            provider_model_key = ai_model.provider_key
            model_config = self._get_image_model_config_fields(
                provider_model_key=provider_model_key,
                size=size,
                quality=quality,
            )
            return ImageRequestDataSchema(
                user_id=user_id,
                ai_model_id=model_id,
                provider_model_key=provider_model_key,
                prompt=prompt,
                min_charge_tokens=ai_model.min_charge_tokens,
                free_requests_limit=ai_model.free_requests_limit,
                **model_config.model_dump(),
            )

    async def _finish_image_generation(
        self,
        poll_response: ImageProviderResponseSchema,
        request_data: ImageRequestDataSchema,
        generation_data: GenerationRequestSchema,
        generation_id: UUID,
    ) -> ImageResultResponseDataSchema:
        if poll_response.status != ImageGenerationStatus.COMPLETED:
            await self.generation_billing_service.rollback_failed_generation(
                data=generation_data,
                generation_id=generation_id,
            )
            raise ImageGenerationNotCompletedError(
                f"Image generation failed with status={poll_response.status}"
            )

        result_url = poll_response.result_url

        if result_url is None:
            await self.generation_billing_service.rollback_failed_generation(
                data=generation_data,
                generation_id=generation_id,
            )
            raise ImageGenerationNotCompletedError(
                "Image generation completed without result URL"
            )
        
        try:
            final_tokens_cost = await self.generation_billing_service.finalize_generation_billing(
                data=GenerationResultSchema(
                    user_id=request_data.user_id,
                    generation_id=generation_id,
                    hold_amount=generation_data.hold_amount,
                    provider_cost=request_data.provider_cost,
                )
            )
        except Exception as e:
            raise ImageGenerationFinalizeError(
                "Failed to finalize image generation billing"
            ) from e

        return ImageResultResponseDataSchema(
            ai_model_id=request_data.ai_model_id,
            user_id=request_data.user_id,
            generation_id=generation_id,
            result_url=result_url,
            tokens_cost=final_tokens_cost,
        )

    async def generate_image(
        self,
        user_id: UUID,
        model_id: UUID,
        prompt: str,
        size: str | None,
        quality: str | None,
    ) -> ImageResultResponseDataSchema:
        request_data = await self._create_and_validate_request_image_data(
            user_id, model_id, prompt, size, quality
        )

        generation_data = GenerationRequestSchema(
            user_id=user_id,
            ai_model_id=model_id,
            generation_type=GenerationType.IMAGE,
            hold_amount=request_data.min_charge_tokens,
            free_requests_limit=request_data.free_requests_limit,
        )
        generation = await self.generation_billing_service.prepare_generation_and_freeze_user_tokens(
            data=generation_data
        )
        response_create_data = await self.wavespeed_service.create_image_generation(
            request_data=request_data
        )
        await self.generation_billing_service.set_generation_task_id(
            generation_id=generation.id,
            task_id=response_create_data.task_id,
        )

        try:
            poll_response = await self.wavespeed_service.poll_image_generation_status(
                task_id=response_create_data.task_id,
                poll_interval_seconds=settings.wavespeed.poll_interval_seconds,
                max_attempts=settings.wavespeed.poll_max_attempts,
            )
        except ProviderError:
            await self.generation_billing_service.rollback_failed_generation(
                data=generation_data,
                generation_id=generation.id,
            )
            raise
        
        except Exception as e:
            await self.generation_billing_service.rollback_failed_generation(
                data=generation_data,
                generation_id=generation.id,
            )
            raise ImageGenerationNotCompletedError(
                "Unexpected image polling error"
            ) from e
        
        final_result = await self._finish_image_generation(
            poll_response=poll_response,
            request_data=request_data,
            generation_data=generation_data,
            generation_id=generation.id,
        )
        return final_result
