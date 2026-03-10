from fastapi import APIRouter

from src.api.v1.ai import llm
from src.api.v1.ai import media
from src.api.v1.ai import ai_models
from src.api.v1.ai import image
from src.api.v1.ai import video

router = APIRouter(prefix="/ai")

router.include_router(ai_models.router, tags=["AI Models"])
router.include_router(llm.router, tags=["LLM"])
router.include_router(media.router, tags=["Media"])
router.include_router(image.router, tags=["Image"])
router.include_router(video.router, tags=["Video"])
