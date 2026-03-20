from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from dishka.integrations.fastapi import DishkaRoute, FromDishka

from src.api.dependencies import require_api_key, resolve_user_id_by_telegram_id
from src.exceptions.storage import (
    EmptyFileError,
    FileTooLargeError,
    StorageMetadataPersistError,
    StorageUploadError,
    UnsupportedFileTypeError,
)
from src.schemas.ai import UploadFileResponseSchema
from src.services.storage import StorageService

router = APIRouter(
    prefix="/media",
    route_class=DishkaRoute,
    dependencies=[Depends(require_api_key)],
)


@router.post("/images", response_model=UploadFileResponseSchema)
async def upload_image(
    storage_service: FromDishka[StorageService],
    file: UploadFile = File(...),
    user_id: UUID = Depends(resolve_user_id_by_telegram_id),
):
    try:
        return await storage_service.upload_image(file=file, user_id=user_id)
    except (UnsupportedFileTypeError, EmptyFileError) as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )
    except FileTooLargeError as exc:
        raise HTTPException(
            status_code=status.HTTP_413_CONTENT_TOO_LARGE,
            detail=str(exc),
        )
    except StorageUploadError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        )
    except StorageMetadataPersistError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        )
