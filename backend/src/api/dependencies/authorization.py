from src.services.authorization import AuthorizationService

from src.core.config import settings


async def get_auth_service() -> AuthorizationService:
    return AuthorizationService(
        **settings.auth.model_dump(),
        tg_bot_token=settings.tg.bot_token,
    )
