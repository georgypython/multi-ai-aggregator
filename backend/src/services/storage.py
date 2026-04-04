import asyncio
from botocore.client import BaseClient
from botocore.exceptions import BotoCoreError, ClientError
from fastapi import UploadFile
from fastapi.concurrency import run_in_threadpool
from uuid import UUID, uuid4
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.exceptions.storage import (
    EmptyFileError,
    FileTooLargeError,
    StoragePresignedUrlError,
    StorageUploadError,
    UnsupportedFileTypeError,
)
from src.schemas import (
    UploadFileResponseSchema,
    UpdloadFileDataSchema,
    MediaFileDbDataSchema,
)
from src.models import MediaFile
from src.services.db_access import DBAccessService


class StorageService(DBAccessService):
    def __init__(
        self,
        client: BaseClient,
        session: AsyncSession,
        bucket: str,
        presigned_ttl_seconds: int,
        input_retention_hours: int,
        input_prefix: str,
        max_upload_bytes: int,
        allowed_image_content_types: tuple[str, ...],
        image_extensions: dict[str, str],
        operation_timeout_seconds: float,
    ) -> None:
        self.client = client
        self.session = session
        self.bucket = bucket
        self.presigned_ttl_seconds = presigned_ttl_seconds
        self.input_retention_hours = input_retention_hours
        self.input_prefix = input_prefix
        self.max_upload_bytes = max_upload_bytes
        self.allowed_image_content_types = allowed_image_content_types
        self.image_extensions = image_extensions
        self.operation_timeout_seconds = operation_timeout_seconds

    async def _add_uploaded_items(self, items: list[dict[str, Any]]) -> list[MediaFile]:
        media_files = [MediaFile(**item) for item in items]
        self.session.add_all(media_files)
        await self.session.flush()
        return media_files

    async def _get_active_user_files_by_ids(
        self,
        *,
        user_id: UUID,
        media_file_ids: list[UUID],
        now: datetime,
    ) -> list[MediaFile]:
        if not media_file_ids:
            return []

        stmt = select(MediaFile).where(
            MediaFile.user_id == user_id,
            MediaFile.id.in_(media_file_ids),
            MediaFile.expires_at > now,
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def _upload_bytes(
        self,
        object_key: str,
        data: bytes,
        content_type: str,
    ) -> None:
        try:
            await asyncio.wait_for(
                run_in_threadpool(
                    self.client.put_object,
                    Bucket=self.bucket,
                    Key=object_key,
                    Body=data,
                    ContentType=content_type,
                ),
                timeout=self.operation_timeout_seconds,
            )
        except TimeoutError as exc:
            raise StorageUploadError("Storage upload timed out") from exc
        except (BotoCoreError, ClientError) as exc:
            raise StorageUploadError(
                f"Failed to upload file to storage: {exc}"
            ) from exc

    async def _create_presigned_get_url(self, object_key: str) -> str:
        try:
            return await asyncio.wait_for(
                run_in_threadpool(
                    self.client.generate_presigned_url,
                    "get_object",
                    Params={"Bucket": self.bucket, "Key": object_key},
                    ExpiresIn=self.presigned_ttl_seconds,
                ),
                timeout=self.operation_timeout_seconds,
            )
        except TimeoutError as exc:
            raise StoragePresignedUrlError(
                f"Presigned URL generation timed out for object_key={object_key}"
            ) from exc
        except (BotoCoreError, ClientError) as exc:
            raise StoragePresignedUrlError(
                f"Failed to generate presigned URL for object_key={object_key}"
            ) from exc

    async def _get_active_media_files_by_ids(
        self,
        user_id: UUID,
        media_file_ids: list[UUID],
    ) -> list[MediaFileDbDataSchema]:
        now = datetime.now(timezone.utc)
        media_files = await self._get_active_user_files_by_ids(
            user_id=user_id,
            media_file_ids=media_file_ids,
            now=now,
        )
        media_files_by_id = {item.id: item for item in media_files}

        ordered_media_files: list[MediaFileDbDataSchema] = []
        for media_file_id in media_file_ids:
            media = media_files_by_id.get(media_file_id)
            if not media:
                raise ValueError(
                    f"Media file not found or expired for media_file_id={media_file_id}"
                )

            ordered_media_files.append(
                MediaFileDbDataSchema(
                    id=media.id,
                    user_id=media.user_id,
                    content_type=media.content_type,
                    size_bytes=media.size_bytes,
                    object_key=media.object_key,
                    expires_at=media.expires_at,
                )
            )

        return ordered_media_files

    async def _create_presigned_urls_for_media_files(
        self,
        files: list[MediaFileDbDataSchema],
    ) -> list[str]:
        urls: list[str] = []
        for file in files:
            url = await self._create_presigned_get_url(object_key=file.object_key)
            urls.append(url)
        return urls

    async def get_files_urls(
        self,
        user_id: UUID,
        media_file_ids: list[UUID],
    ) -> list[str]:
        media_files = await self._get_active_media_files_by_ids(
            user_id=user_id,
            media_file_ids=media_file_ids,
        )
        return await self._create_presigned_urls_for_media_files(files=media_files)

    async def _create_upload_file_data(
        self, user_id: UUID, file: UploadFile
    ) -> UpdloadFileDataSchema:
        expires_at = datetime.now(timezone.utc) + timedelta(
            hours=self.input_retention_hours
        )

        content_type = file.content_type
        if not content_type or content_type not in self.allowed_image_content_types:
            raise UnsupportedFileTypeError(
                "Unsupported file type. Allowed: "
                + ", ".join(self.allowed_image_content_types)
            )

        data = await file.read()
        if not data:
            raise EmptyFileError("Uploaded file is empty")

        size_bytes = len(data)
        if size_bytes > self.max_upload_bytes:
            raise FileTooLargeError("File too large to upload")

        file_id = uuid4()
        object_key = f"{self.input_prefix}/{user_id}/{file_id}.{self.image_extensions[content_type]}"

        return UpdloadFileDataSchema(
            data=data,
            file=MediaFileDbDataSchema(
                id=file_id,
                user_id=user_id,
                content_type=file.content_type,
                size_bytes=len(data),
                object_key=object_key,
                expires_at=expires_at,
            ),
        )

    async def upload_image(
        self,
        file: UploadFile,
        user_id: UUID,
    ) -> UploadFileResponseSchema:
        upload_file_data = await self._create_upload_file_data(
            user_id=user_id,
            file=file,
        )

        async with self.session.begin():
            await self._add_uploaded_items(items=[upload_file_data.file.model_dump()])

            await self._upload_bytes(
                object_key=upload_file_data.file.object_key,
                data=upload_file_data.data,
                content_type=upload_file_data.file.content_type,
            )

        return UploadFileResponseSchema(
            media_file_id=upload_file_data.file.id,
        )
