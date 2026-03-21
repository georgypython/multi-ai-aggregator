from uuid import UUID

from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter, Depends, HTTPException, status

from src.api.dependencies import require_api_key, resolve_user_id_by_telegram_id
from src.core.logger_setup import logger
from src.exceptions.generation import ModelConfigError
from src.models.enums.ai import ModelType
from src.schemas import (
    AIModelListItemResponseSchema,
    ImageModelPriceResponseSchema,
    ImageModelProfileResponseSchema,
    VideoModelPriceResponseSchema,
    VideoModelProfileResponseSchema,
)
from src.services.ai_models import AIModelsService
from src.services.image_profile import ImageProfileService
from src.services.video_profile import VideoProfileService

router = APIRouter(
    prefix="/ai",
    route_class=DishkaRoute,
    dependencies=[Depends(require_api_key)],
)


@router.get("/", response_model=list[AIModelListItemResponseSchema])
async def get_ai_models_list(
    service: FromDishka[AIModelsService],
    model_type: ModelType | None = None,
    active_only: bool = True,
    user_id: UUID = Depends(resolve_user_id_by_telegram_id),
) -> list[AIModelListItemResponseSchema]:
    """Возвращает список доступных AI-моделей для пользователя."""
    try:
        return await service.get_ai_models_list(
            user_id=user_id,
            model_type=model_type,
            active_only=active_only,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )
    except Exception as exc:
        logger.exception("Unhandled error in /ai")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {exc}",
        )


@router.get("/{model_id}/profile/image", response_model=ImageModelProfileResponseSchema)
async def get_image_profile(
    model_id: UUID,
    service: FromDishka[ImageProfileService],
):
    """Возвращает профиль и варианты параметров image-модели."""
    try:
        return await service.load_image_profile_with_prices_by_ai_model_id(
            ai_model_id=model_id
        )
    except ModelConfigError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )


@router.get("/{model_id}/profile/video", response_model=VideoModelProfileResponseSchema)
async def get_video_profile(
    model_id: UUID,
    service: FromDishka[VideoProfileService],
):
    """Возвращает профиль и варианты параметров video-модели."""
    try:
        return await service.load_video_profile_with_prices_by_ai_model_id(
            ai_model_id=model_id
        )
    except ModelConfigError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )


@router.get("/{model_id}/price/image", response_model=ImageModelPriceResponseSchema)
async def get_image_price(
    model_id: UUID,
    service: FromDishka[ImageProfileService],
    size: str | None = None,
    quality: str | None = None,
    user_id: UUID = Depends(resolve_user_id_by_telegram_id),
):
    """Считает цену image-генерации с учетом выбранных параметров."""
    try:
        return await service.get_image_model_price(
            user_id=user_id,
            model_id=model_id,
            size=size,
            quality=quality,
        )
    except ModelConfigError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        )


@router.get("/{model_id}/price/video", response_model=VideoModelPriceResponseSchema)
async def get_video_price(
    model_id: UUID,
    service: FromDishka[VideoProfileService],
    duration_seconds: int | None = None,
    user_id: UUID = Depends(resolve_user_id_by_telegram_id),
):
    """Считает цену video-генерации с учетом параметров."""
    try:
        return await service.get_video_model_price(
            user_id=user_id,
            model_id=model_id,
            duration_seconds=duration_seconds,
        )
    except ModelConfigError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        )
