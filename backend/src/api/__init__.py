from fastapi import APIRouter

from src.api import v1
from src.core.config import settings

router = APIRouter()

router.include_router(
    v1.router,
    prefix=settings.api.prefix,
)
