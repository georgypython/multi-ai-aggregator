from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from src.core.models.enums import ModelType
from src.core.schemas.ai import (
    ImageRequestDataSchema, 
    ImageModelConfigDataSchema,
    GenerationRequestSchema
)
from src.core.utils.image_configs import IMAGE_MODEL_CONFIGS
from src.repositories import AIModelRepository, UserRepository
from .generation_billing import GenerationBillingService


class ImageGenerationService:
    def __init__(
        self,
        session: AsyncSession,
        user_repo: UserRepository,
        ai_model_repo: AIModelRepository,
        generation_billing_service: GenerationBillingService,
    ):
        self.session = session
        self.user_repo = user_repo
        self.ai_model_repo = ai_model_repo
        self.generation_billing_service = generation_billing_service

    def _get_image_model_config_fields(self, provider_model_key: str) -> ImageModelConfigDataSchema:
        model_config = IMAGE_MODEL_CONFIGS.get(provider_model_key)
        if not model_config:
            raise ValueError(
                f"Image model config not found for provider_key={provider_model_key}"
            )

        sizes = model_config.get("sizes")
        qualities = model_config.get("qualities")
        provider_prices = model_config.get("prices_usd")

        if not isinstance(sizes, list) or not sizes:
            raise ValueError(
                f"Image model sizes config invalid for provider_key={provider_model_key}"
            )
        if not isinstance(qualities, list) or not qualities:
            raise ValueError(
                f"Image model qualities config invalid for provider_key={provider_model_key}"
            )
        if not isinstance(provider_prices, dict) or not provider_prices:
            raise ValueError(
                f"Image model prices config invalid for provider_key={provider_model_key}"
            )

        return ImageModelConfigDataSchema(sizes=sizes, qualities=qualities, provider_prices=provider_prices)

    async def _create_and_validate_request_image_data(
        self,
        user_id: UUID,
        model_id: UUID,
        prompt: str,
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

            provider_model_key = ai_model.provider_key
            model_config = self._get_image_model_config_fields(
                provider_model_key=provider_model_key
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

    async def generate_image(
        self,
        user_id: UUID,
        model_id: UUID,
        prompt: str,
    ):
        request_data = await self._create_and_validate_request_image_data(
            user_id, model_id, prompt
        )

        generation_data = GenerationRequestSchema(
            user_id=user_id,
            ai_model_id=model_id,
            min_charge_tokens=request_data.min_charge_tokens,
            free_requests_limit=request_data.free_requests_limit,
        )
        generation = await self.generation_billing_service.prepare_generation_and_freeze_user_tokens(
            data=generation_data
        )