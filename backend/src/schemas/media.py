from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class UploadFileResponseSchema(BaseModel):
    media_file_id: UUID


class MediaFileDbDataSchema(BaseModel):
    id: UUID
    user_id: UUID
    content_type: str
    size_bytes: int
    object_key: str
    expires_at: datetime


class UpdloadFileDataSchema(BaseModel):
    data: bytes
    file: MediaFileDbDataSchema
