from pydantic import BaseModel

from src.models.enums import GenerationStatus


class WavespeedGenerationResponseSchema(BaseModel):
    task_id: str
    model_key: str | None = None
    status: GenerationStatus
    result_url: str
    created_at: str | None = None
    error: str | None = None


class WavespeedWebhookUrlsSchema(BaseModel):
    get: str | None = None


class WavespeedWebhookPayloadSchema(BaseModel):
    id: str
    status: GenerationStatus
    model: str | None = None
    created_at: str | None = None
    error: str | None = None
    urls: WavespeedWebhookUrlsSchema | None = None
    outputs: list[str] | None = None
    event: str | None = None
    type: str | None = None
