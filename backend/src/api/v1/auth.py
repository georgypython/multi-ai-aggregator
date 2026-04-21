from dishka.integrations.fastapi import DishkaRoute
from fastapi import APIRouter, Request, Response, Depends
from jwt import ExpiredSignatureError, InvalidTokenError

from src.exceptions.http import Unauthorized
from src.api.dependencies import get_auth_service
from src.services.authorization import AuthorizationService
from src.schemas.authorization import TokenType, TokenData

router = APIRouter(
    prefix="/auth",
    route_class=DishkaRoute,
)


@router.post("/refresh")
async def refresh_auth(
    request: Request,
    response: Response,
    auth_service: AuthorizationService = Depends(get_auth_service),
) -> dict[str, str]:
    refresh_token = request.cookies.get("refresh_token")
    if not refresh_token:
        raise Unauthorized("Refresh token cookie required")

    try:
        payload = auth_service.verify_token(refresh_token, TokenType.REFRESH)
    except ExpiredSignatureError:
        raise Unauthorized("Refresh token expired")
    except InvalidTokenError:
        raise Unauthorized("Invalid refresh token")

    auth_service.set_auth_cookies(
        response,
        TokenData(user_id=payload.user_id, scope=payload.scope),
    )
    return {"status": "refreshed"}


@router.post("/logout")
async def logout_auth(
    response: Response, auth_service: AuthorizationService = Depends(get_auth_service)
) -> dict[str, str]:
    auth_service.clear_auth_cookies(response)
    return {"status": "logged_out"}
