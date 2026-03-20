from aiogram import Router

from .ai_mode_handlers import router as mode_router
from .ai_balance_handlers import router as balance_router
from .ai_model_handlers import router as model_router
from .ai_image_handlers import router as image_router
from .ai_video_handlers import router as video_router
from .ai_config_handlers import router as config_router
from .ai_generation_handlers import router as generation_router

router = Router()

router.include_router(mode_router)
router.include_router(balance_router)
router.include_router(model_router)
router.include_router(image_router)
router.include_router(video_router)
router.include_router(config_router)
router.include_router(generation_router)
