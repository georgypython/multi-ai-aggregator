from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter, Depends, status

from src.api.dependencies import validate_wavespeed_webhook_signature
from src.schemas import WavespeedWebhookPayloadSchema
from src.services.generation_webhook import GenerationWebhookService

router = APIRouter(prefix="/webhooks", route_class=DishkaRoute)


@router.post("/wavespeed", status_code=status.HTTP_200_OK)
async def wavespeed_webhook(
    payload: WavespeedWebhookPayloadSchema,
    service: FromDishka[GenerationWebhookService],
    _: None = Depends(validate_wavespeed_webhook_signature),
):
    """Принимает webhook WaveSpeed после проверки подписи через dependency."""
    await service.handle_wavespeed_webhook(payload=payload)
    return {"status": "ok"}
