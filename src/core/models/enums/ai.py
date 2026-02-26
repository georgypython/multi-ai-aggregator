from enum import StrEnum


class AIModelType(StrEnum):
    LLM = "llm"
    IMAGE = "image"
    VIDEO = "video"


class GenerationStatus(StrEnum):
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELED = "canceled"
