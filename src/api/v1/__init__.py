from fastapi import APIRouter

from src.api.v1 import status
from src.api.v1 import ai
from src.core.config import settings

router = APIRouter(prefix=settings.api.v1.prefix)

router.include_router(
    status.router,
    tags=["status"],
)
router.include_router(ai.router, prefix="/ai", tags=["AI"])
