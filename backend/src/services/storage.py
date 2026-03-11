from botocore.client import BaseClient
from botocore.exceptions import BotoCoreError, ClientError
from fastapi import UploadFile
from fastapi.concurrency import run_in_threadpool
from uuid import UUID, uuid4
from datetime import datetime, timedelta, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from src.core.exceptions.storage import (
    EmptyFileError,
    FileTooLargeError,
    StorageUploadError,
    UnsupportedFileTypeError,
)
from src.core.schemas.ai import (
    UploadFileResponseSchema, 
    UpdloadFileDataSchema,
    MediaFileDbDataSchema
)
from src.repositories import MediaFilesRepository


class StorageService:
    def __init__(
        self,
        client: BaseClient,
        session: AsyncSession,
        media_files_repo: MediaFilesRepository,
        bucket: str,
        presigned_ttl_seconds: int,
        input_retention_hours: int,
        input_prefix: str,
        max_upload_bytes: int,
        allowed_image_content_types: tuple[str, ...],
        image_extensions: dict[str, str],
    ) -> None:
        self.client = client
        self.session = session
        self.media_files_repo = media_files_repo
        self.bucket = bucket
        self.presigned_ttl_seconds = presigned_ttl_seconds
        self.input_retention_hours = input_retention_hours
        self.input_prefix = input_prefix
        self.max_upload_bytes = max_upload_bytes
        self.allowed_image_content_types = allowed_image_content_types
        self.image_extensions = image_extensions

    async def _upload_bytes(
        self,
        object_key: str,
        data: bytes,
        content_type: str,
    ) -> None:
        try:
            await run_in_threadpool(
                self.client.put_object,
                Bucket=self.bucket,
                Key=object_key,
                Body=data,
                ContentType=content_type,
            )
        except (BotoCoreError, ClientError) as exc:
            raise StorageUploadError("Failed to upload file to storage") from exc

    async def _create_upload_file_data(self, user_id: UUID, file: UploadFile) -> UpdloadFileDataSchema:
        expires_at = datetime.now(timezone.utc) + timedelta(
            hours=self.input_retention_hours
        )

        content_type = file.content_type
        if (
                not content_type
                or content_type not in self.allowed_image_content_types
            ):
                raise UnsupportedFileTypeError(
                    "Unsupported file type. Allowed: "
                    + ", ".join(self.allowed_image_content_types)
                )
        
        data = await file.read()
        if not data:
                raise EmptyFileError("Uploaded file is empty")
        
        size_bytes=len(data)
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
            expires_at=expires_at
        )
    )
    
    async def upload_image(
        self,
        files: list[UploadFile],
        user_id: UUID,
    ) -> UploadFileResponseSchema:
        total_upload_files: list[UpdloadFileDataSchema] = []

        for file in files:
            upload_file_data = await self._create_upload_file_data(
                user_id=user_id, file=file
            )
            total_upload_files.append(upload_file_data)

        async with self.session.begin():
            await self.media_files_repo.add_uploaded_items(
                session=self.session,
                items=[
                    upload.file.model_dump() for upload in total_upload_files
                ],
            )

            for upload in total_upload_files:
                await self._upload_bytes(
                    object_key=upload.file.object_key,
                    data=upload.data,
                    content_type=upload.file.content_type
                )

                
        return UploadFileResponseSchema(
            media_file_ids=[upload.file.id for upload in total_upload_files],
        )