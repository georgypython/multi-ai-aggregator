from fastapi import APIRouter

from src.api.v1.ai import llm
from src.api.v1.ai import ai_models

router = APIRouter(prefix="/ai")

router.include_router(ai_models.router, tags=["AI Models"])
router.include_router(llm.router, tags=["LLM"])
