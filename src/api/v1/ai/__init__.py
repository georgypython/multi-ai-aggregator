from fastapi import APIRouter

from src.api.v1.ai import llm
from src.api.v1.ai import ai_models

router = APIRouter()

router.include_router(ai_models.router, prefix="/models", tags=["AI Models"])
router.include_router(llm.router, prefix="/llm", tags=["LLM"])

