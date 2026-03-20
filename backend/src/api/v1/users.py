from fastapi import APIRouter, Depends, HTTPException, status
from dishka.integrations.fastapi import DishkaRoute, FromDishka

from src.api.dependencies import require_api_key
from src.schemas.ai import UserBalanceResponseSchema
from src.services.users import UsersService

router = APIRouter(
    prefix="/users",
    route_class=DishkaRoute,
    dependencies=[Depends(require_api_key)],
)


@router.get("/{user_id}/balance", response_model=UserBalanceResponseSchema)
async def get_user_balance(
    user_id: str,
    service: FromDishka[UsersService],
) -> UserBalanceResponseSchema:
    try:
        return await service.get_user_balance(user_id=user_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )
