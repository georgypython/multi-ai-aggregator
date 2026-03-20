from uuid import UUID
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from src.exceptions.generation import ModelConfigError
from src.models import AIModel, VideoPrice, VideoProfile
from src.models.enums import ModelType
from src.schemas import (
    VideoModelPriceResponseSchema,
    VideoModelProfileResponseSchema,
    VideoPriceParamsSchema,
    VideoModelRawPriceDataSchema,
    VideoModelRawDataSchema,
)
from src.repositories import (
    AIModelRepository,
    GenerationRepository,
    VideoPriceRepository,
)
from .generation_billing import GenerationBillingService


class VideoProfileService:
    def __init__(
        self,
        session: AsyncSession,
        ai_model_repo: AIModelRepository,
        video_price_repo: VideoPriceRepository,
        generation_repo: GenerationRepository,
        generation_billing_service: GenerationBillingService,
    ) -> None:
        self.session = session
        self.ai_model_repo = ai_model_repo
        self.video_price_repo = video_price_repo
        self.generation_repo = generation_repo
        self.generation_billing_service = generation_billing_service

    def _validate_video_model(
        self, ai_model_id: UUID, ai_model: AIModel | None
    ) -> AIModel:
        if not ai_model:
            raise ValueError(f"AIModel not found for model_id={ai_model_id}")

        if not ai_model.is_active:
            raise ValueError(f"AIModel inactive for model_id={ai_model_id}")

        if ai_model.model_type != ModelType.VIDEO:
            raise ModelConfigError(
                f"AIModel is not video type for model_id={ai_model_id}"
            )

        return ai_model

    def _validate_video_profile_with_prices(
        self, video_profile: VideoProfile | None
    ) -> VideoProfile:
        if not video_profile:
            raise ModelConfigError("VideoProfile is not configured")

        if not video_profile.is_active:
            raise ModelConfigError("VideoProfile is inactive")

        if not video_profile.prices:
            raise ModelConfigError("VideoPrice configs are missing")

        return video_profile

    def _build_video_model_durations_and_sizes(
        self, video_prices: list[VideoPrice]
    ) -> VideoPriceParamsSchema:
        durations_seconds: set[int] = set()
        sizes: set[str] = set()

        for price in video_prices:
            durations_seconds.add(price.duration_seconds)
            sizes.add(price.size)

        resolved_durations = sorted(durations_seconds)
        resolved_sizes = sorted(sizes)

        if not resolved_durations or not resolved_sizes:
            raise ModelConfigError("VideoProfile pricing config is invalid")

        return VideoPriceParamsSchema(
            durations_seconds=resolved_durations,
            sizes=resolved_sizes,
        )

    async def _get_raw_video_price_data(
        self,
        model_id: UUID,
        video_profile: VideoProfile | None,
        duration_seconds: int | None,
        size: str | None,
    ) -> VideoModelRawPriceDataSchema:
        video_profile = self._validate_video_profile_with_prices(
            video_profile=video_profile
        )

        price_params = self._build_video_model_durations_and_sizes(
            video_prices=video_profile.prices,
        )
        resolved_duration = duration_seconds or price_params.durations_seconds[0]
        resolved_size = size or price_params.sizes[0]

        video_price = await self.video_price_repo.get_one_by_ai_model_duration_size(
            session=self.session,
            ai_model_id=model_id,
            duration_seconds=resolved_duration,
            size=resolved_size,
        )
        if not video_price:
            raise ModelConfigError(
                f"Missing price for duration_seconds='{resolved_duration}', size='{resolved_size}'"
            )

        return VideoModelRawPriceDataSchema(
            ai_model_id=model_id,
            duration_seconds=resolved_duration,
            size=resolved_size,
            usd_price=video_price.provider_cost,
        )

    async def load_video_profile_with_prices_by_ai_model_id(
        self,
        ai_model_id: UUID,
    ) -> VideoModelProfileResponseSchema:
        ai_model = await self.ai_model_repo.get_one_with_video_profile_and_prices(
            session=self.session,
            ai_model_id=ai_model_id,
        )
        ai_model = self._validate_video_model(
            ai_model_id=ai_model_id, ai_model=ai_model
        )

        video_profile = self._validate_video_profile_with_prices(
            video_profile=ai_model.video_profile,
        )

        price_params = self._build_video_model_durations_and_sizes(
            video_prices=video_profile.prices,
        )

        return VideoModelProfileResponseSchema(
            id=ai_model.id,
            name=ai_model.name,
            provider_key=ai_model.provider_key,
            provider=video_profile.provider,
            **price_params.model_dump(),
        )

    async def get_video_model_price(
        self,
        user_id: UUID,
        model_id: UUID,
        duration_seconds: int | None,
        size: str | None,
    ) -> VideoModelPriceResponseSchema:
        ai_model = await self.ai_model_repo.get_one_with_video_profile_and_prices(
            session=self.session,
            ai_model_id=model_id,
        )
        ai_model = self._validate_video_model(ai_model_id=model_id, ai_model=ai_model)

        raw_price_data = await self._get_raw_video_price_data(
            model_id=model_id,
            video_profile=ai_model.video_profile,
            duration_seconds=duration_seconds,
            size=size,
        )

        provider_price = raw_price_data.usd_price
        tokens_price = (
            await self.generation_billing_service.calculate_final_tokens_cost(
                provider_cost=provider_price,
                model_token_price_id=ai_model.token_price_id,
                hold_amount=ai_model.min_charge_tokens,
            )
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
            duration_seconds=raw_price_data.duration_seconds,
            size=raw_price_data.size,
            tokens_price=tokens_price,
        )

    async def get_video_profile_with_raw_price(
        self,
        model_id: UUID,
        duration_seconds: int | None,
        size: str | None,
    ) -> VideoModelRawDataSchema:
        ai_model = await self.ai_model_repo.get_one_with_video_profile_and_prices(
            session=self.session,
            ai_model_id=model_id,
        )
        ai_model = self._validate_video_model(ai_model_id=model_id, ai_model=ai_model)

        video_profile = self._validate_video_profile_with_prices(
            video_profile=ai_model.video_profile,
        )
        raw_price_data = await self._get_raw_video_price_data(
            model_id=model_id,
            video_profile=video_profile,
            duration_seconds=duration_seconds,
            size=size,
        )

        return VideoModelRawDataSchema(
            duration_seconds=raw_price_data.duration_seconds,
            size=raw_price_data.size,
            provider_cost=raw_price_data.usd_price,
            provider=video_profile.provider,
        )
