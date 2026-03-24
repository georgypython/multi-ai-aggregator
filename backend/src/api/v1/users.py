from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from dishka.integrations.fastapi import DishkaRoute, FromDishka

from src.api.dependencies import require_api_key, resolve_user_id_by_telegram_id
from src.schemas import (
    LLMConfigCreateRequestSchema,
    LLMConfigResponseSchema,
    UserBalanceResponseSchema,
)
from src.services.llm_configuration import LLMConfigurationService
from src.services.users import UsersService

router = APIRouter(
    prefix="/users",
    route_class=DishkaRoute,
    dependencies=[Depends(require_api_key)],
)


@router.post("/me/llm-config", response_model=LLMConfigResponseSchema)
async def create_or_update_llm_config(
    payload: LLMConfigCreateRequestSchema,
    service: FromDishka[LLMConfigurationService],
    user_id: UUID = Depends(resolve_user_id_by_telegram_id),
):
    """Создает или обновляет LLM-настройки текущего пользователя."""
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


@router.get("/me/llm-config", response_model=LLMConfigResponseSchema)
async def get_llm_config(
    service: FromDishka[LLMConfigurationService],
    user_id: UUID = Depends(resolve_user_id_by_telegram_id),
):
    """Возвращает сохраненные LLM-настройки текущего пользователя."""
    try:
        return await service.get_user_llm_config(user_id=user_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )


@router.get("/me/balance", response_model=UserBalanceResponseSchema)
async def get_my_balance(
    service: FromDishka[UsersService],
    user_id: UUID = Depends(resolve_user_id_by_telegram_id),
) -> UserBalanceResponseSchema:
    """Возвращает токен-баланс текущего пользователя."""
    try:
        return await service.get_user_balance(user_id=str(user_id))
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )
