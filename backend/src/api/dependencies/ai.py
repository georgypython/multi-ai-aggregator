from uuid import UUID

from fastapi import HTTPException, Query, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from src.core.config import settings
from src.models.db_helper import db_helper
from src.repositories import UserRepository

bearer_scheme = HTTPBearer(auto_error=False)


async def require_api_key(
    credentials: HTTPAuthorizationCredentials | None = Security(bearer_scheme),
) -> None:
    expected_api_key = settings.api.api_key
    if not expected_api_key or expected_api_key == "YOUR_API_KEY":
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Server API key is not configured",
        )

    api_key = credentials.credentials if credentials else None
    if api_key != expected_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
        )


async def resolve_user_id_by_telegram_id(
    tg_user_id: int = Query(..., ge=1),
) -> UUID:
    user_repo = UserRepository()
    async with db_helper.session_factory() as session:
        async with session.begin():
            user = await user_repo.get_or_create_by_telegram_id(
                session=session,
                telegram_id=tg_user_id,
                available_tokens=settings.ai_logic.new_user_free_tokens,
            )
            return user.id
