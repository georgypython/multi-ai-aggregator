from uuid import UUID
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.exceptions.generation import ModelConfigError
from src.models import AIModel, AIGeneration, ImagePrice, ImageProfile
from src.models.enums import GenerationStatus, ModelType
from src.schemas import (
    ImageModelPriceResponseSchema,
    ImageModelProfileResponseSchema,
    ImagePriceParamsSchema,
    ImageModelRawPriceDataSchema,
    ImageModelRawDataSchema,
)
from src.services.db_access import DBAccessService
from .generation_billing import GenerationBillingService


class ImageProfileService(DBAccessService):
    def __init__(
        self,
        session: AsyncSession,
        generation_billing_service: GenerationBillingService,
    ) -> None:
        self.session = session
        self.generation_billing_service = generation_billing_service

    async def _get_ai_model_with_profile(
        self,
        *,
        ai_model_id: UUID,
        model_type: ModelType,
    ) -> AIModel | None:
        stmt = select(AIModel).where(AIModel.id == ai_model_id)

        if model_type == ModelType.IMAGE:
            stmt = stmt.options(
                selectinload(AIModel.image_profile).selectinload(ImageProfile.prices)
            )
        else:
            raise ValueError(f"Unsupported model_type={model_type}")

        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def _get_image_price_by_model_size_quality(
        self,
        *,
        ai_model_id: UUID,
        size: str,
        quality: str,
    ) -> ImagePrice | None:
        stmt = (
            select(ImagePrice)
            .join(ImageProfile, ImagePrice.image_profile_id == ImageProfile.id)
            .where(
                ImageProfile.ai_model_id == ai_model_id,
                ImagePrice.size == size,
                ImagePrice.quality == quality,
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def _count_generations_by_user_and_model(
        self,
        *,
        user_id: UUID,
        ai_model_id: UUID,
        max_count: int,
    ) -> int:
        base_stmt = (
            select(AIGeneration.id)
            .where(
                AIGeneration.user_id == user_id,
                AIGeneration.ai_model_id == ai_model_id,
                AIGeneration.status.in_(
                    (
                        GenerationStatus.PROCESSING,
                        GenerationStatus.COMPLETED,
                        GenerationStatus.FAILED,
                    )
                ),
            )
            .limit(max_count)
        )
        stmt = select(func.count()).select_from(base_stmt.subquery())
        result = await self.session.execute(stmt)
        return int(result.scalar_one() or 0)

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
        image_price = await self._get_image_price_by_model_size_quality(
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
        ai_model = await self._get_ai_model_with_profile(
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
        ai_model = await self._get_ai_model_with_profile(
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
            generation_count = await self._count_generations_by_user_and_model(
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
        ai_model = await self._get_ai_model_with_profile(
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
