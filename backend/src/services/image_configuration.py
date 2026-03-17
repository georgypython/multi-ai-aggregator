from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from backend.src.core.exceptions.generation import ModelConfigError
from src.core.models.enums import ModelProvider, ModelType
from src.core.schemas.ai import (
    ImageModelDetailResponseSchema,
    ImageModelPriceResponseSchema,
)
from src.repositories import AIModelRepository, GenerationRepository
from .generation_billing import GenerationBillingService


class ImageConfigurationService:
    def __init__(
        self,
        session: AsyncSession,
        ai_model_repo: AIModelRepository,
        generation_repo: GenerationRepository,
        generation_billing_service: GenerationBillingService,
        image_model_configs: dict[str, dict],
    ) -> None:
        self.session = session
        self.ai_model_repo = ai_model_repo
        self.generation_repo = generation_repo
        self.generation_billing_service = generation_billing_service
        self.image_model_configs = image_model_configs

    async def _get_active_image_model(self, model_id: UUID):
        ai_model = await self.ai_model_repo.get_one(
            session=self.session,
            id=model_id,
            is_active=True,
        )
        if not ai_model:
            raise ValueError(f"Active AIModel not found for model_id={model_id}")

        if ai_model.model_type != ModelType.IMAGE:
            raise ModelConfigError(f"AIModel is not image type for model_id={model_id}")

        return ai_model

    def _get_model_config(self, provider_key: str) -> dict:
        model_config = self.image_model_configs.get(provider_key)
        if model_config:
            return model_config

        raise ModelConfigError(
            f"Image model config not found for provider_key={provider_key}"
        )

    def _resolve_provider(self, model_config: dict) -> ModelProvider:
        provider_raw = model_config.get("provider")
        try:
            return ModelProvider(provider_raw)
        except ValueError as exc:
            raise ModelConfigError(
                f"Unsupported image provider in config: {provider_raw}"
            ) from exc

    def _resolve_price(
        self,
        model_config: dict,
        size: str | None,
        quality: str | None,
    ) -> tuple[str, str, float]:
        sizes = model_config.get("sizes")
        qualities = model_config.get("qualities")
        prices_usd = model_config.get("prices_usd")

        if not isinstance(sizes, list) or not sizes:
            raise ModelConfigError("Image model sizes config is invalid")
        if not isinstance(qualities, list) or not qualities:
            raise ModelConfigError("Image model qualities config is invalid")
        if not isinstance(prices_usd, dict) or not prices_usd:
            raise ModelConfigError("Image model prices config is invalid")

        resolved_size = size or sizes[0]
        resolved_quality = quality or qualities[0]

        if resolved_size not in sizes:
            raise ModelConfigError(
                f"Unsupported size '{resolved_size}'. Allowed: {sizes}"
            )
        if resolved_quality not in qualities:
            raise ModelConfigError(
                f"Unsupported quality '{resolved_quality}'. Allowed: {qualities}"
            )

        quality_prices = prices_usd.get(resolved_quality)
        if not isinstance(quality_prices, dict):
            raise ModelConfigError(
                f"Missing prices for quality='{resolved_quality}'"
            )

        provider_price = quality_prices.get(resolved_size)
        if provider_price is None:
            raise ModelConfigError(
                f"Missing price for size='{resolved_size}', quality='{resolved_quality}'"
            )

        return resolved_size, resolved_quality, float(provider_price)

    async def get_image_model_configuration(
        self,
        model_id: UUID,
    ) -> ImageModelDetailResponseSchema:
        ai_model = await self._get_active_image_model(model_id=model_id)
        model_config = self._get_model_config(provider_key=ai_model.provider_key)
        print(model_config)
        provider = self._resolve_provider(model_config=model_config)

        sizes = model_config.get("sizes")
        qualities = model_config.get("qualities")
        prices_usd = model_config.get("prices_usd")

        if not isinstance(sizes, list) or not isinstance(qualities, list) or not isinstance(prices_usd, dict):
            raise ModelConfigError(
                f"Image model config is invalid for provider_key={ai_model.provider_key}"
            )

        return ImageModelDetailResponseSchema(
            id=ai_model.id,
            name=ai_model.name,
            provider_key=ai_model.provider_key,
            provider=provider,
            sizes=sizes,
            qualities=qualities,
            prices_usd=prices_usd,
        )

    async def get_image_model_price(
        self,
        user_id: UUID,
        model_id: UUID,
        size: str | None,
        quality: str | None,
    ) -> ImageModelPriceResponseSchema:
        ai_model = await self._get_active_image_model(model_id=model_id)
        model_config = self._get_model_config(provider_key=ai_model.provider_key)

        resolved_size, resolved_quality, provider_price = self._resolve_price(
            model_config=model_config,
            size=size,
            quality=quality,
        )
        tokens_price = await self.generation_billing_service.calculate_tokens_cost_from_provider_cost(
            provider_cost=provider_price
        )

        if ai_model.free_requests_limit > 0:
            generation_count = await self.generation_repo.count_by_user_and_model(
                session=self.session,
                user_id=user_id,
                ai_model_id=ai_model.id,
                max_count=ai_model.free_requests_limit,
            )
            if generation_count < ai_model.free_requests_limit:
                provider_price = 0.0
                tokens_price = 0.0

        return ImageModelPriceResponseSchema(
            ai_model_id=ai_model.id,
            provider_key=ai_model.provider_key,
            size=resolved_size,
            quality=resolved_quality,
            tokens_price=tokens_price,
        )
