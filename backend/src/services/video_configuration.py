from uuid import UUID
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from backend.src.core.exceptions.generation import ModelConfigError
from src.core.models import AIModel
from src.core.models.enums import ModelProvider, ModelType
from src.core.schemas.ai import VideoModelDetailResponseSchema, VideoModelPriceResponseSchema
from src.repositories import AIModelRepository, GenerationRepository
from .generation_billing import GenerationBillingService


class VideoConfigurationService:
    def __init__(
        self,
        session: AsyncSession,
        ai_model_repo: AIModelRepository,
        generation_repo: GenerationRepository,
        generation_billing_service: GenerationBillingService,
        video_model_configs: dict[str, dict],
    ) -> None:
        self.session = session
        self.ai_model_repo = ai_model_repo
        self.generation_repo = generation_repo
        self.generation_billing_service = generation_billing_service
        self.video_model_configs = video_model_configs

    async def _get_active_video_model(self, model_id: UUID) -> AIModel:
        ai_model = await self.ai_model_repo.get_one(
            session=self.session,
            id=model_id,
            is_active=True,
        )
        if not ai_model:
            raise ValueError(f"Active AIModel not found for model_id={model_id}")

        if ai_model.model_type != ModelType.VIDEO:
            raise ModelConfigError(f"AIModel is not video type for model_id={model_id}")

        return ai_model

    def _get_model_config(self, provider_key: str) -> dict:
        model_config = self.video_model_configs.get(provider_key)
        if not model_config:
            raise ModelConfigError(
                f"Video model config not found for provider_key={provider_key}"
            )
        return model_config

    def _resolve_provider(self, model_config: dict) -> ModelProvider:
        provider_raw = model_config.get("provider")
        try:
            return ModelProvider(provider_raw)
        except ValueError as exc:
            raise ModelConfigError(
                f"Unsupported video provider in config: {provider_raw}"
            ) from exc

    def _resolve_price(
        self,
        model_config: dict,
        duration_seconds: int | None,
        size: str | None,
    ) -> tuple[int, str, Decimal]:
        durations_seconds = model_config.get("durations_seconds")
        sizes = model_config.get("sizes")
        prices_usd_by_duration = model_config.get("prices_usd_by_duration")

        if not isinstance(durations_seconds, list) or not durations_seconds:
            raise ModelConfigError("Video model durations config is invalid")
        if not isinstance(sizes, list) or not sizes:
            raise ModelConfigError("Video model sizes config is invalid")
        if not isinstance(prices_usd_by_duration, dict) or not prices_usd_by_duration:
            raise ModelConfigError("Video model prices config is invalid")

        resolved_duration = duration_seconds or durations_seconds[0]
        resolved_size = size or sizes[0]

        if resolved_duration not in durations_seconds:
            raise ModelConfigError(
                f"Unsupported duration_seconds '{resolved_duration}'. Allowed: {durations_seconds}"
            )
        if resolved_size not in sizes:
            raise ModelConfigError(
                f"Unsupported size '{resolved_size}'. Allowed: {sizes}"
            )

        duration_prices = prices_usd_by_duration.get(str(resolved_duration))
        if not isinstance(duration_prices, dict):
            raise ModelConfigError(
                f"Missing prices for duration_seconds='{resolved_duration}'"
            )

        provider_price = duration_prices.get(resolved_size)
        if provider_price is None:
            raise ModelConfigError(
                f"Missing price for duration_seconds='{resolved_duration}', size='{resolved_size}'"
            )

        if not isinstance(provider_price, (int, float, Decimal)):
            raise ModelConfigError(
                f"Invalid provider price for duration_seconds='{resolved_duration}', size='{resolved_size}'"
            )

        return int(resolved_duration), resolved_size, Decimal(str(provider_price))

    async def get_video_model_configuration(
        self,
        model_id: UUID,
    ) -> VideoModelDetailResponseSchema:
        ai_model = await self._get_active_video_model(model_id=model_id)
        model_config = self._get_model_config(provider_key=ai_model.provider_key)
        provider = self._resolve_provider(model_config=model_config)

        durations_seconds = model_config.get("durations_seconds")
        sizes = model_config.get("sizes")
        prices_usd_by_duration = model_config.get("prices_usd_by_duration")

        if (
            not isinstance(durations_seconds, list)
            or not isinstance(sizes, list)
            or not isinstance(prices_usd_by_duration, dict)
        ):
            raise ModelConfigError(
                f"Video model config is invalid for provider_key={ai_model.provider_key}"
            )

        return VideoModelDetailResponseSchema(
            id=ai_model.id,
            name=ai_model.name,
            provider_key=ai_model.provider_key,
            provider=provider,
            durations_seconds=durations_seconds,
            sizes=sizes,
            prices_usd_by_duration=prices_usd_by_duration,
        )

    async def get_video_model_price(
        self,
        user_id: UUID,
        model_id: UUID,
        duration_seconds: int | None,
        size: str | None,
    ) -> VideoModelPriceResponseSchema:
        ai_model = await self._get_active_video_model(model_id=model_id)
        model_config = self._get_model_config(provider_key=ai_model.provider_key)

        resolved_duration, resolved_size, provider_price = self._resolve_price(
            model_config=model_config,
            duration_seconds=duration_seconds,
            size=size,
        )
        tokens_price = await self.generation_billing_service.calculate_tokens_cost_from_provider_cost(
            provider_cost=provider_price,
            model_token_price_id=ai_model.token_price_id,
            hold_amount=ai_model.min_charge_tokens,
        )

        if ai_model.free_requests_limit > 0:
            generation_count = await self.generation_repo.count_by_user_and_model(
                session=self.session,
                user_id=user_id,
                ai_model_id=ai_model.id,
                max_count=ai_model.free_requests_limit,
            )
            if generation_count < ai_model.free_requests_limit:
                tokens_price = Decimal("0")

        return VideoModelPriceResponseSchema(
            ai_model_id=ai_model.id,
            provider_key=ai_model.provider_key,
            duration_seconds=resolved_duration,
            size=resolved_size,
            tokens_price=tokens_price,
        )
