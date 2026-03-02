from uuid import UUID

from fastapi import APIRouter, Depends
from dishka.integrations.fastapi import FromDishka, DishkaRoute
from src.api.dependencies import require_api_key, resolve_user_id_by_telegram_id
from src.services.image_generation import ImageGenerationService

router = APIRouter(
    prefix="/image",
    route_class=DishkaRoute,
    dependencies=[Depends(require_api_key)],
)


@router.post("/generations")
async def generate_image(
    service: FromDishka[ImageGenerationService],
    model_id: UUID,
    prompt: str,
    user_id: UUID = Depends(resolve_user_id_by_telegram_id),
):
    response = await service.generate_image(
        user_id=user_id, model_id=model_id, prompt=prompt
    )


# TODO
# Синхронизировать конфиги с image из utils с БД моделями 
# Добавить эндпоинт на получение стандартизированного инфо по image модели (качество / размер / цена)
# Добавить создание и валидацию request даты у image с маппингом DB model.provider_key / name -> model_config
# Добавить замарозку user баланса перед отправкой запроса у image
# Сделать отпарвку запроса на генерацию перед этим можно
# созранять ее id в generation)
#  сделать базовую celery таск по обработке image generation (раз в N секунд проверяем статус таски
# Сделать финальную обработку генерации - и возврат ответа с ссылкой на изображение
# добавить кнопочный pipeline на создание генерации в бота + обработку сгенерированной картинки
# затестить