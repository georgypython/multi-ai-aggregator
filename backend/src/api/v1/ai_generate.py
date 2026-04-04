from uuid import UUID

from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter, Body, Depends, HTTPException, status
from pydantic import BaseModel

from src.api.dependencies import (
    TgRateLimiter,
    require_api_key,
    resolve_whitelisted_user_id_by_telegram_id,
)
from src.exceptions.generation import (
    ImageGenerationNotCompletedError,
    InactiveModelError,
    InsufficientBalanceError,
    ModelConfigError,
    ProviderError,
    ProviderTimeoutError,
    UserBalanceNotConfiguredError,
)
from src.schemas import (
    GenerationResultResponseDataSchema,
    ImageGenerationCreateRequestSchema,
    VideoGenerationCreateRequestSchema,
    LLMGenerationCreateRequestSchema,
)
from src.services.image_generation import ImageGenerationService
from src.services.llm_generation import LLMGenerationService
from src.services.video_generation import VideoGenerationService

router = APIRouter(
    prefix="/ai",
    route_class=DishkaRoute,
    dependencies=[Depends(require_api_key)],
)


@router.post(
    "/{model_id}/generate/image",
    response_model=GenerationResultResponseDataSchema,
    dependencies=[
        Depends(
            TgRateLimiter(limit=6, window_seconds=60, path_name_key="generate_image")
        )
    ],
)
async def generate_image(
    model_id: UUID,
    payload: ImageGenerationCreateRequestSchema,
    service: FromDishka[ImageGenerationService],
    user_id: UUID = Depends(resolve_whitelisted_user_id_by_telegram_id),
):
    """Запускает генерацию изображения для выбранной модели."""
    try:
        return await service.generate_image(
            user_id=user_id,
            model_id=model_id,
            prompt=payload.prompt,
            size=payload.size,
            quality=payload.quality,
            media_file_ids=payload.media_file_ids,
        )
    except ModelConfigError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        )
    except ImageGenerationNotCompletedError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
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


@router.post(
    "/{model_id}/generate/llm",
    response_model=GenerationResultResponseDataSchema,
    dependencies=[
        Depends(
            TgRateLimiter(limit=20, window_seconds=60, path_name_key="generate_llm")
        )
    ],
)
async def generate_llm(
    model_id: UUID,
    payload: LLMGenerationCreateRequestSchema,
    service: FromDishka[LLMGenerationService],
    user_id: UUID = Depends(resolve_whitelisted_user_id_by_telegram_id),
):
    """Генерирует текстовый ответ LLM для пользователя."""
    try:
        return await service.generate_llm_response(
            user_id=user_id,
            model_id=model_id,
            prompt=payload.prompt,
        )
    except InsufficientBalanceError as exc:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail=str(exc),
        )
    except (UserBalanceNotConfiguredError, InactiveModelError) as exc:
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


@router.post(
    "/{model_id}/generate/video",
    response_model=GenerationResultResponseDataSchema,
    dependencies=[
        Depends(
            TgRateLimiter(limit=2, window_seconds=60, path_name_key="generate_video")
        )
    ],
)
async def generate_video(
    model_id: UUID,
    payload: VideoGenerationCreateRequestSchema,
    service: FromDishka[VideoGenerationService],
    user_id: UUID = Depends(resolve_whitelisted_user_id_by_telegram_id),
):
    """Запускает генерацию видео для выбранной модели."""
    try:
        return await service.generate_video(
            user_id=user_id,
            model_id=model_id,
            prompt=payload.prompt,
            duration_seconds=payload.duration_seconds,
            media_file_id=payload.media_file_id,
        )
    except ModelConfigError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        )
    except InsufficientBalanceError as exc:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail=str(exc),
        )
    except UserBalanceNotConfiguredError as exc:
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
