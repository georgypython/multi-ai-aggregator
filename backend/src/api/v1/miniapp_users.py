from dishka.integrations.fastapi import DishkaRoute
from fastapi import APIRouter, Depends, Response

from src.api.dependencies import (
    resolve_telegram_user_from_init_data,
    get_users_service,
    get_auth_service,
)
from src.schemas.authorization import TokenData
from src.models import User
from src.schemas.telegram_account import TelegramUser
from src.services.users import UsersService
from src.services.authorization import AuthorizationService
from src.exceptions.http import Forbidden

router = APIRouter(
    route_class=DishkaRoute,
)


@router.post("/users/me")
async def create_miniapp_session(
    response: Response,
    telegram_user: TelegramUser = Depends(resolve_telegram_user_from_init_data),
    user_service: UsersService = Depends(get_users_service),
    auth_service: AuthorizationService = Depends(get_auth_service),
) -> dict[str, str | int]:
    user = await user_service.get_one(
        model=User, telegram_id=telegram_user.id, is_active=True, is_whitelist=True
    )
    if not user:
        raise Forbidden("Access denied")

    auth_service.set_auth_cookies(
        response,
        TokenData(user_id=user.id, scope="user"),
    )
    return {
        "status": "ok",
        "telegram_id": user.telegram_id,
    }
