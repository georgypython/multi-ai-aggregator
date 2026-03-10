from botocore.client import BaseClient
from botocore.exceptions import BotoCoreError, ClientError
from fastapi import UploadFile
from fastapi.concurrency import run_in_threadpool
from uuid import UUID, uuid4

from src.core.exceptions.storage import (
    EmptyFileError,
    FileTooLargeError,
    StorageUploadError,
    UnsupportedFileTypeError,
)
from src.core.schemas.ai import UploadImageResponseSchema


class StorageService:
    def __init__(
        self,
        client: BaseClient,
        bucket: str,
        presigned_ttl_seconds: int,
        input_retention_hours: int,
        input_prefix: str,
        max_upload_bytes: int,
        allowed_image_content_types: tuple[str, ...],
        image_extensions: dict[str, str],
    ) -> None:
        self.client = client
        self.bucket = bucket
        self.presigned_ttl_seconds = presigned_ttl_seconds
        self.input_retention_hours = input_retention_hours
        self.input_prefix = input_prefix
        self.max_upload_bytes = max_upload_bytes
        self.allowed_image_content_types = allowed_image_content_types
        self.image_extensions = image_extensions

    async def upload_bytes(
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

    async def upload_image(
        self,
        file: UploadFile,
        user_id: UUID,
    ) -> UploadImageResponseSchema:
        content_type = file.content_type
        if not content_type or content_type not in self.allowed_image_content_types:
            raise UnsupportedFileTypeError(
                "Unsupported file type. Allowed: "
                + ", ".join(self.allowed_image_content_types)
            )

        data = await file.read()
        if not data:
            raise EmptyFileError("Uploaded file is empty")

        if len(data) > self.max_upload_bytes:
            raise FileTooLargeError(
                f"File is too large. Max size is {self.max_upload_bytes} bytes"
            )

        extension = self.image_extensions[content_type]
        object_key = f"{self.input_prefix}/{user_id}/{uuid4()}.{extension}"

        await self.upload_bytes(
            object_key=object_key,
            data=data,
            content_type=content_type,
        )

        return UploadImageResponseSchema(
            object_key=object_key,
            content_type=content_type,
            size_bytes=len(data),
        )