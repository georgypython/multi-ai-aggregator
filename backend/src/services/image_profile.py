from uuid import UUID
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from src.exceptions.generation import ModelConfigError
from src.models import AIModel, ImagePrice, ImageProfile
from src.models.enums import ModelType
from src.schemas import (
    ImageModelPriceResponseSchema,
    ImageModelProfileResponseSchema,
    ImagePriceParamsSchema,
    ImageModelRawPriceDataSchema,
    ImageModelRawDataSchema,
)
from src.repositories import (
    AIModelRepository,
    GenerationRepository,
    ImagePriceRepository,
)
from .generation_billing import GenerationBillingService


class ImageProfileService:
    def __init__(
        self,
        session: AsyncSession,
        ai_model_repo: AIModelRepository,
        image_price_repo: ImagePriceRepository,
        generation_repo: GenerationRepository,
        generation_billing_service: GenerationBillingService,
    ) -> None:
        self.session = session
        self.ai_model_repo = ai_model_repo
        self.image_price_repo = image_price_repo
        self.generation_repo = generation_repo
        self.generation_billing_service = generation_billing_service

    def _validate_image_model(
        self, ai_model_id: UUID, ai_model: AIModel | None
    ) -> AIModel:
        if not ai_model:
            raise ValueError(f"AIModel not found for model_id={ai_model_id}")

        if not ai_model.is_active:
            raise ValueError(f"AIModel inactive for model_id={ai_model_id}")

        if ai_model.model_type != ModelType.IMAGE:
            raise ModelConfigError(
                f"AIModel is not image type for model_id={ai_model_id}"
            )

        return ai_model

    def _validate_image_profile_with_prices(
        self, image_profile: ImageProfile | None
    ) -> ImageProfile:
        if not image_profile:
            raise ModelConfigError(f"ImageProfile is not configured")

        if not image_profile.is_active:
            raise ModelConfigError(f"ImageProfile is inactive")

        if not image_profile.prices:
            raise ModelConfigError(f"ImagePrice configs are missing")

        return image_profile

    def _build_image_model_qualities_and_sizes(
        self, image_prices: list[ImagePrice]
    ) -> ImagePriceParamsSchema:
        sizes: set[str] = set()
        qualities: set[str] = set()

        for price in image_prices:
            sizes.add(price.size)
            qualities.add(price.quality)

        resolved_sizes = sorted(sizes)
        resolved_qualities = sorted(qualities)

        if not resolved_sizes or not resolved_qualities:
            raise ModelConfigError(f"ImageProfile pricing config is invalid")
        return ImagePriceParamsSchema(
            sizes=resolved_sizes, qualities=resolved_qualities
        )

    async def _get_raw_image_price_data(
        self,
        model_id: UUID,
        image_profile: ImageProfile | None,
        size: str | None,
        quality: str | None,
    ) -> ImageModelRawPriceDataSchema:
        image_profile = self._validate_image_profile_with_prices(
            image_profile=image_profile
        )

        price_params = self._build_image_model_qualities_and_sizes(
            image_prices=image_profile.prices,
        )
        resolved_size = size or price_params.sizes[0]
        resolved_quality = quality or price_params.qualities[0]
        image_price = await self.image_price_repo.get_one_by_ai_model_size_quality(
            session=self.session,
            ai_model_id=model_id,
            size=resolved_size,
            quality=resolved_quality,
        )
        if not image_price:
            raise ModelConfigError(
                f"Missing price for size='{resolved_size}', quality='{resolved_quality}'"
            )

        return ImageModelRawPriceDataSchema(
            ai_model_id=model_id,
            quality=resolved_quality,
            size=resolved_size,
            usd_price=image_price.provider_cost,
        )

    async def load_image_profile_with_prices_by_ai_model_id(
        self,
        ai_model_id: UUID,
    ) -> ImageModelProfileResponseSchema:
        ai_model = await self.ai_model_repo.get_one_with_profile(
            session=self.session,
            ai_model_id=ai_model_id,
            model_type=ModelType.IMAGE,
        )
        ai_model = self._validate_image_model(
            ai_model_id=ai_model_id, ai_model=ai_model
        )

        image_profile = self._validate_image_profile_with_prices(
            image_profile=ai_model.image_profile
        )

        price_params = self._build_image_model_qualities_and_sizes(
            image_prices=image_profile.prices,
        )

        return ImageModelProfileResponseSchema(
            id=ai_model.id,
            name=ai_model.name,
            provider_key=ai_model.provider_key,
            provider=image_profile.provider,
            **price_params.model_dump(),
        )

    async def get_image_model_price(
        self,
        user_id: UUID,
        model_id: UUID,
        size: str | None,
        quality: str | None,
    ) -> ImageModelPriceResponseSchema:
        ai_model = await self.ai_model_repo.get_one_with_profile(
            session=self.session,
            ai_model_id=model_id,
            model_type=ModelType.IMAGE,
        )
        ai_model = self._validate_image_model(ai_model_id=model_id, ai_model=ai_model)

        raw_price_data = await self._get_raw_image_price_data(
            model_id=model_id,
            image_profile=ai_model.image_profile,
            size=size,
            quality=quality,
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

        return ImageModelPriceResponseSchema(
            ai_model_id=ai_model.id,
            provider_key=ai_model.provider_key,
            size=raw_price_data.size,
            quality=raw_price_data.quality,
            tokens_price=tokens_price,
        )

    async def get_image_profile_with_raw_price(
        self,
        model_id: UUID,
        size: str | None,
        quality: str | None,
    ) -> ImageModelRawDataSchema:
        ai_model = await self.ai_model_repo.get_one_with_profile(
            session=self.session,
            ai_model_id=model_id,
            model_type=ModelType.IMAGE,
        )
        ai_model = self._validate_image_model(ai_model_id=model_id, ai_model=ai_model)

        image_profile = self._validate_image_profile_with_prices(
            image_profile=ai_model.image_profile,
        )
        raw_price_data = await self._get_raw_image_price_data(
            model_id=model_id,
            image_profile=image_profile,
            size=size,
            quality=quality,
        )

        return ImageModelRawDataSchema(
            size=raw_price_data.size,
            quality=raw_price_data.quality,
            provider_cost=raw_price_data.usd_price,
            provider=image_profile.provider,
            image_edit_model_name=image_profile.image_edit_model_name,
        )
