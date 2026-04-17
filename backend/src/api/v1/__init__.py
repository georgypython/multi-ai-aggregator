from fastapi import APIRouter

from src.api.v1 import ai_generate
from src.api.v1 import ai_models
from src.api.v1 import generations
from src.api.v1 import invoice
from src.api.v1 import media
from src.api.v1 import users
from src.api.v1 import webhooks
from src.core.config import settings

router = APIRouter(prefix=settings.api.v1.prefix)

router.include_router(generations.router, tags=["Generations"])
router.include_router(ai_models.router, tags=["AI Models"])
router.include_router(ai_generate.router, tags=["AI Generate"])
router.include_router(media.router, tags=["Media"])
router.include_router(users.router, tags=["User"])
router.include_router(invoice.router, tags=["Invoice"])
router.include_router(webhooks.router, tags=["Webhooks"])
