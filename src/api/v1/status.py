from fastapi import APIRouter
from dishka.integrations.fastapi import FromDishka, DishkaRoute

from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(route_class=DishkaRoute)


@router.get("/status")
async def get_status(session: FromDishka[AsyncSession]):
    return {"status": "ok"}
