from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from dishka.integrations.fastapi import FromDishka, DishkaRoute
from src.api.dependencies import require_api_key, resolve_user_id_by_telegram_id
from src.core.exceptions.image import (
    ImageGenerationFinalizeError,
    ImageGenerationNotCompletedError,
    ImageModelConfigError,
)
from src.core.exceptions.llm import (
    ProviderError,
    ProviderTimeoutError,
)
from src.core.schemas.ai import (
    ImageModelDetailResponseSchema,
    ImageModelPriceResponseSchema,
    ImageResultResponseDataSchema,
)
from src.services.image_configuration import ImageConfigurationService
from src.services.image_generation import ImageGenerationService

router = APIRouter(
    prefix="/image",
    route_class=DishkaRoute,
    dependencies=[Depends(require_api_key)],
)


@router.post("/generations", response_model=ImageResultResponseDataSchema)
async def generate_image(
    service: FromDishka[ImageGenerationService],
    model_id: UUID,
    prompt: str,
    size: str | None = None,
    quality: str | None = None,
    user_id: UUID = Depends(resolve_user_id_by_telegram_id),
):
    try:
        return await service.generate_image(
            user_id=user_id,
            model_id=model_id,
            prompt=prompt,
            size=size,
            quality=quality,
        )
    except ImageModelConfigError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )
    except ImageGenerationNotCompletedError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        )
    except ImageGenerationFinalizeError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )
    except ProviderTimeoutError as exc:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail=str(exc),
        )
    except ProviderError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        )


@router.get("/{model_id}", response_model=ImageModelDetailResponseSchema)
async def get_image_model_configuration(
    service: FromDishka[ImageConfigurationService],
    model_id: UUID,
):
    try:
        return await service.get_image_model_configuration(model_id=model_id)
    except ImageModelConfigError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )


@router.get("/{model_id}/price", response_model=ImageModelPriceResponseSchema)
async def get_image_model_price(
    service: FromDishka[ImageConfigurationService],
    model_id: UUID,
    size: str | None = None,
    quality: str | None = None,
):
    try:
        return await service.get_image_model_price(
            model_id=model_id,
            size=size,
            quality=quality,
        )
    except ImageModelConfigError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
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
