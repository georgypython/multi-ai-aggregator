from pydantic import BaseModel

from src.models.enums import GenerationStatus


class WavespeedGenerationResponseSchema(BaseModel):
    task_id: str
    model_key: str | None = None
    status: GenerationStatus
    result_url: str | None = None
    created_at: str | None = None
    error: str | None = None
