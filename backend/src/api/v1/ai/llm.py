from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from dishka.integrations.fastapi import FromDishka, DishkaRoute
from src.api.dependencies import require_api_key, resolve_user_id_by_telegram_id
from src.core.exceptions.llm import (
    InactiveModelError,
    InsufficientBalanceError,
    ProviderError,
    ProviderHTTPError,
    ProviderNetworkError,
    ProviderResponseFormatError,
    ProviderTimeoutError,
    UserBalanceNotConfiguredError,
)
from src.core.schemas.ai import GenerationResultResponseDataSchema
from src.core.schemas.ai import LLMConfigCreateRequestSchema, LLMConfigResponseSchema
from src.core.logger_setup import logger
from src.services.llm_configuration import LLMConfigurationService
from src.services.llm_generation import LLMGenerationService


router = APIRouter(
    prefix="/llm",
    route_class=DishkaRoute,
    dependencies=[Depends(require_api_key)],
)


@router.post("/configs", response_model=LLMConfigResponseSchema)
async def create_or_update_llm_config(
    payload: LLMConfigCreateRequestSchema,
    service: FromDishka[LLMConfigurationService],
    user_id: UUID = Depends(resolve_user_id_by_telegram_id),
) -> LLMConfigResponseSchema:
    try:
        return await service.create_or_update_user_llm_config(
            user_id=user_id,
            payload=payload,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )
    except Exception as exc:
        logger.exception("Unhandled error in /llm/configs POST")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {exc}",
        )


@router.get("/configs", response_model=LLMConfigResponseSchema)
async def get_llm_config(
    service: FromDishka[LLMConfigurationService],
    user_id: UUID = Depends(resolve_user_id_by_telegram_id),
) -> LLMConfigResponseSchema:
    try:
        return await service.get_user_llm_config(user_id=user_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )
    except Exception as exc:
        logger.exception("Unhandled error in /llm/configs GET")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {exc}",
        )
    

@router.post("/generations", response_model=GenerationResultResponseDataSchema)
async def generate_llm_response(
    model_id: UUID,
    prompt: str,
    service: FromDishka[LLMGenerationService],
    user_id: UUID = Depends(resolve_user_id_by_telegram_id),
) -> GenerationResultResponseDataSchema:
    """
    Генерирует текстовый ответ LLM и возвращает итог по генерации.

    Параметры:
    - user_id: идентификатор пользователя.
    - model_id: идентификатор выбранной AI-модели.
    - prompt: пользовательский текстовый запрос.

    Что делает эндпоинт:
    - Валидирует пользователя/модель и доступность генерации.
    - Вызывает внешнего LLM-провайдера.
    - Финализирует генерацию и возвращает результат.

    Ошибки:
    - 402: недостаточно токенов у пользователя.
    - 409: не настроен баланс или модель недоступна.
    - 404: пользователь/модель не найдены.
    - 502/504: ошибки внешнего провайдера.
    - 500: непредвиденная внутренняя ошибка.
    """
    try:
        return await service.generate_llm_response(
            user_id=user_id,
            model_id=model_id,
            prompt=prompt,
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
    except InactiveModelError as exc:
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
    except ProviderNetworkError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        )
    except ProviderResponseFormatError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        )
    except ProviderHTTPError as exc:
        mapped_status = (
            exc.status_code
            if 400 <= exc.status_code <= 599
            else status.HTTP_502_BAD_GATEWAY
        )
        raise HTTPException(status_code=mapped_status, detail=str(exc))
    except ProviderError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        )
    except Exception as exc:
        logger.exception("Unhandled error in /generations/llm")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {exc}",
        )

