from base64 import b64decode
from uuid import UUID

from jwt import ExpiredSignatureError, InvalidTokenError
from fastapi import Depends, Request, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from src.schemas.telegram_account import TelegramUser
from src.schemas.authorization import TokenType
from src.services.users import UsersService
from src.services.authorization import AuthorizationService
from src.models import User

from .users import get_users_service
from .authorization import get_auth_service

from src.exceptions.http import Forbidden, Unauthorized

bearer_scheme = HTTPBearer(auto_error=False)


def resolve_telegram_user_from_init_data(
    header: HTTPAuthorizationCredentials | None = Security(bearer_scheme),
    auth_service: AuthorizationService = Depends(get_auth_service),
) -> TelegramUser:
    if not header or not header.credentials:
        raise Unauthorized("Authorization header required")

    try:
        init_data = b64decode(header.credentials.encode()).decode()
        tg_user = auth_service.verify_init_data(init_data=init_data)
    except Exception:
        raise Unauthorized("Invalid init data")

    return tg_user


async def resolve_user_id_session(
    request: Request,
    user_service: UsersService = Depends(get_users_service),
    auth_service: AuthorizationService = Depends(get_auth_service),
) -> UUID:
    access_token = request.cookies.get("access_token")

    if not access_token:
        raise Unauthorized()
    try:
        payload = auth_service.verify_token(
            token=access_token, token_type=TokenType.ACCESS
        )
        user = await user_service.get_one(
            model=User, id=payload.user_id, is_active=True, is_whitelist=True
        )
        if not user:
            raise Forbidden("Access denied")
    except ExpiredSignatureError:
        raise Unauthorized("Token Expired")
    except InvalidTokenError:
        raise Unauthorized("Invalid Token Error")

    return user.id
