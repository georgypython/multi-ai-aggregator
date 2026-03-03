from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from dishka.integrations.fastapi import FromDishka, DishkaRoute

from src.api.dependencies import require_api_key, resolve_user_id_by_telegram_id
from src.core.schemas.ai import AIModelListItemResponseSchema
from src.core.logger_setup import logger
from src.services.ai_models import AIModelsService
from src.core.models.enums.ai import ModelType


router = APIRouter(
    route_class=DishkaRoute,
    dependencies=[Depends(require_api_key)],
)


@router.get("/", response_model=list[AIModelListItemResponseSchema])
async def get_ai_models_list(
    service: FromDishka[AIModelsService],
    model_type: ModelType | None = None,
    active_only: bool = True,
    user_id: UUID = Depends(resolve_user_id_by_telegram_id),
) -> list[AIModelListItemResponseSchema]:
    try:
        return await service.get_ai_models_list(
            user_id=user_id,
            model_type=model_type,
            active_only=active_only,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )
    except Exception as exc:
        logger.exception("Unhandled error in /models")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {exc}",
        )
