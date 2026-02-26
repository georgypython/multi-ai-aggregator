from uuid import UUID

from fastapi import APIRouter
from dishka.integrations.fastapi import FromDishka, DishkaRoute
from src.services.llm import LLMService

router = APIRouter(route_class=DishkaRoute)


@router.post("/generations/llm")
async def generate_llm_response(
    user_id: UUID, model_id: UUID, prompt: str, service: FromDishka[LLMService]
):
    response = await service.generate_llm_response()
