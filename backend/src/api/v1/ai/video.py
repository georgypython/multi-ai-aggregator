from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response, status
from dishka.integrations.fastapi import FromDishka, DishkaRoute
from src.api.dependencies import require_api_key, resolve_user_id_by_telegram_id
from src.core.exceptions.llm import (
	InsufficientBalanceError,
	ProviderError,
	ProviderTimeoutError,
	UserBalanceNotConfiguredError,
)
from src.core.exceptions.video import (
	VideoGenerationError,
	VideoGenerationNotCompletedError,
	VideoModelConfigError,
)
from src.core.schemas.ai import (
	GenerationResultResponseDataSchema,
	VideoModelDetailResponseSchema,
	VideoModelPriceResponseSchema,
)
from src.services.video_configuration import VideoConfigurationService
from src.services.video_generation import VideoGenerationService

router = APIRouter(
	prefix="/video",
	route_class=DishkaRoute,
	dependencies=[Depends(require_api_key)],
)


@router.get("/{model_id}", response_model=VideoModelDetailResponseSchema)
async def get_video_model_configuration(
	service: FromDishka[VideoConfigurationService],
	model_id: UUID,
):
	try:
		return await service.get_video_model_configuration(model_id=model_id)
	except VideoModelConfigError as exc:
		raise HTTPException(
			status_code=status.HTTP_400_BAD_REQUEST,
			detail=str(exc),
		)
	except ValueError as exc:
		raise HTTPException(
			status_code=status.HTTP_404_NOT_FOUND,
			detail=str(exc),
		)


@router.get("/{model_id}/price", response_model=VideoModelPriceResponseSchema)
async def get_video_model_price(
	service: FromDishka[VideoConfigurationService],
	model_id: UUID,
	duration_seconds: int | None = None,
	size: str | None = None,
	user_id: UUID = Depends(resolve_user_id_by_telegram_id),
):
	try:
		return await service.get_video_model_price(
			user_id=user_id,
			model_id=model_id,
			duration_seconds=duration_seconds,
			size=size,
		)
	except VideoModelConfigError as exc:
		raise HTTPException(
			status_code=status.HTTP_400_BAD_REQUEST,
			detail=str(exc),
		)
	except ValueError as exc:
		raise HTTPException(
			status_code=status.HTTP_404_NOT_FOUND,
			detail=str(exc),
		)
	except RuntimeError as exc:
		raise HTTPException(
			status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
			detail=str(exc),
		)


@router.post("/generations", response_model=GenerationResultResponseDataSchema)
async def generate_video(
	service: FromDishka[VideoGenerationService],
	model_id: UUID,
	prompt: str,
	duration_seconds: int | None = None,
	size: str | None = None,
	user_id: UUID = Depends(resolve_user_id_by_telegram_id),
):
	try:
		return await service.generate_video(
			user_id=user_id,
			model_id=model_id,
			prompt=prompt,
			duration_seconds=duration_seconds,
			size=size,
		)
	except VideoModelConfigError as exc:
		raise HTTPException(
			status_code=status.HTTP_400_BAD_REQUEST,
			detail=str(exc),
		)
	except VideoGenerationNotCompletedError as exc:
		raise HTTPException(
			status_code=status.HTTP_502_BAD_GATEWAY,
			detail=str(exc),
		)
	except VideoGenerationError as exc:
		raise HTTPException(
			status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
			detail=str(exc),
		)
	except InsufficientBalanceError as exc:
		raise HTTPException(
			status_code=status.HTTP_402_PAYMENT_REQUIRED,
			detail=str(exc),
		)
	except UserBalanceNotConfiguredError as exc:
		raise HTTPException(
			status_code=status.HTTP_409_CONFLICT,
			detail=str(exc),
		)
	except ValueError as exc:
		raise HTTPException(
			status_code=status.HTTP_404_NOT_FOUND,
			detail=str(exc),
		)
	except ProviderTimeoutError as exc:
		raise HTTPException(
			status_code=status.HTTP_504_GATEWAY_TIMEOUT,
			detail=str(exc),
		)
	except ProviderError as exc:
		raise HTTPException(
			status_code=status.HTTP_502_BAD_GATEWAY,
			detail=str(exc),
		)
	except RuntimeError as exc:
		raise HTTPException(
			status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
			detail=str(exc),
		)


@router.get("/generations/{generation_id}/content")
async def get_video_generation_content(
	service: FromDishka[VideoGenerationService],
	generation_id: UUID,
	user_id: UUID = Depends(resolve_user_id_by_telegram_id),
):
	try:
		content = await service.get_video_generation_content(
			user_id=user_id,
			generation_id=generation_id,
		)
		return Response(
			content=content,
			headers={"Cache-Control": "no-store"},
		)
	except VideoGenerationNotCompletedError as exc:
		raise HTTPException(
			status_code=status.HTTP_409_CONFLICT,
			detail=str(exc),
		)
	except ValueError as exc:
		raise HTTPException(
			status_code=status.HTTP_404_NOT_FOUND,
			detail=str(exc),
		)
	except ProviderTimeoutError as exc:
		raise HTTPException(
			status_code=status.HTTP_504_GATEWAY_TIMEOUT,
			detail=str(exc),
		)
	except ProviderError as exc:
		raise HTTPException(
			status_code=status.HTTP_502_BAD_GATEWAY,
			detail=str(exc),
		)