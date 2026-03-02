from uuid import UUID

from fastapi import Header, HTTPException, Query, status

from src.core.config import settings
from src.core.models.db_helper import db_helper
from src.repositories import UserRepository


def _extract_api_key(
    authorization: str | None,
    x_api_key: str | None,
) -> str | None:
    if x_api_key:
        return x_api_key

    if authorization and authorization.lower().startswith("bearer "):
        return authorization.split(" ", maxsplit=1)[1].strip()

    return None


async def require_api_key(
    authorization: str | None = Header(default=None),
    x_api_key: str | None = Header(default=None, alias="X-API-Key"),
) -> None:
    expected_api_key = settings.api.api_key
    if not expected_api_key or expected_api_key == "YOUR_API_KEY":
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Server API key is not configured",
        )

    api_key = _extract_api_key(authorization=authorization, x_api_key=x_api_key)
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
