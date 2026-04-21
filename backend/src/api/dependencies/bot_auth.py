from uuid import UUID

from fastapi import Depends, HTTPException, Query, status
from fastapi.security import APIKeyHeader

from src.core.config import settings
from src.exceptions.http import Unauthorized, Forbidden
from src.services.users import UsersService
from src.models import User

from .users import get_users_service

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def require_api_key(
    api_key: str = Depends(api_key_header),
) -> None:
    expected_api_key = settings.api.api_key
    if not expected_api_key or expected_api_key == "YOUR_API_KEY":
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Server API key is not configured",
        )

    if not api_key or api_key != expected_api_key:
        raise Unauthorized("Invalid API key")


async def resolve_user_id_by_telegram_id(
    tg_user_id: int = Query(..., ge=1),
    user_service: UsersService = Depends(get_users_service),
) -> UUID:
    user = await user_service.get_active_user_by_tg_id_with_creation(tg_user_id)
    return user.id


async def resolve_whitelisted_user_id_by_telegram_id(
    tg_user_id: int = Query(..., ge=1),
    user_service: UsersService = Depends(get_users_service),
) -> UUID:
    user = await user_service.get_one(
        model=User, telegram_id=tg_user_id, is_active=True, is_whitelist=True
    )
    if not user:
        raise Forbidden("Access denied")
    return user.id
