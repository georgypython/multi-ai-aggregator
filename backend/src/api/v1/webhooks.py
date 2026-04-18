from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError

from src.api.dependencies import (
    validate_lavatop_webhook_api_key,
    validate_wavespeed_webhook_signature,
)
from src.exceptions.payment import (
    PaymentConflictError,
    PaymentNotFoundError,
    PaymentProcessingError,
    PaymentProviderRequestError,
    PaymentProviderUnavailableError,
    PaymentValidationError,
)
from src.schemas import LavaTopWebhookRequestData, WavespeedWebhookPayloadSchema
from src.services.generation_webhook import GenerationWebhookService
from src.services.payment_webhook import PaymentWebhookService

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


@router.post(
    "/lava-top/regular",
    dependencies=[Depends(validate_lavatop_webhook_api_key)],
    status_code=status.HTTP_200_OK,
)
async def lavatop_regular_webhook(
    payload: LavaTopWebhookRequestData,
    service: FromDishka[PaymentWebhookService],
):
    try:
        return await service.process_lava_top_regular_webhook(payload)
    except IntegrityError:
        return {"status": "ok", "duplicate": True}
    except (
        PaymentValidationError,
        PaymentProviderRequestError,
        PaymentProcessingError,
    ) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except PaymentNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except PaymentConflictError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except PaymentProviderUnavailableError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.post(
    "/lava-top/recurrent",
    dependencies=[Depends(validate_lavatop_webhook_api_key)],
    status_code=status.HTTP_200_OK,
)
async def lavatop_recurrent_webhook(
    payload: LavaTopWebhookRequestData,
    service: FromDishka[PaymentWebhookService],
):
    try:
        return await service.process_lava_top_recurrent_webhook(payload)
    except IntegrityError:
        return {"status": "ok", "duplicate": True}
    except (
        PaymentValidationError,
        PaymentProviderRequestError,
        PaymentProcessingError,
    ) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except PaymentNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except PaymentConflictError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except PaymentProviderUnavailableError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
