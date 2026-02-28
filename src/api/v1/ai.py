from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from dishka.integrations.fastapi import FromDishka, DishkaRoute
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
from src.core.schemas.ai import LLMResultResponseSchema
from src.core.logger_setup import logger
from src.services.llm import LLMService

router = APIRouter(route_class=DishkaRoute)


@router.post("/generations/llm", response_model=LLMResultResponseSchema)
async def generate_llm_response(
    user_id: UUID, model_id: UUID, prompt: str, service: FromDishka[LLMService]
) -> LLMResultResponseSchema:
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
