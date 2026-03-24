from uuid import UUID

from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter, Depends, HTTPException, Response, status

from src.api.dependencies import require_api_key, resolve_user_id_by_telegram_id
from src.exceptions.generation import (
    MediaGenerationNotCompletedError,
    ProviderError,
    ProviderTimeoutError,
)
from src.schemas import GenerationResultResponseDataSchema
from src.services.generation_info import GenerationInfoService

router = APIRouter(
    prefix="/generations",
    route_class=DishkaRoute,
    dependencies=[Depends(require_api_key)],
)


@router.get("/{generation_id}", response_model=GenerationResultResponseDataSchema)
async def get_generation_status(
    generation_id: UUID,
    service: FromDishka[GenerationInfoService],
    user_id: UUID = Depends(resolve_user_id_by_telegram_id),
):
    """Возвращает текущий статус и стоимость генерации."""
    try:
        return await service.get_generation_status(
            user_id=user_id,
            generation_id=generation_id,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )


@router.get("/{generation_id}/content")
async def get_generation_content(
    generation_id: UUID,
    service: FromDishka[GenerationInfoService],
    user_id: UUID = Depends(resolve_user_id_by_telegram_id),
):
    """Возвращает бинарный результат завершенной media-генерации."""
    try:
        content = await service.get_media_generation_content(
            user_id=user_id,
            generation_id=generation_id,
        )
        return Response(content=content, headers={"Cache-Control": "no-store"})
    except MediaGenerationNotCompletedError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
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
