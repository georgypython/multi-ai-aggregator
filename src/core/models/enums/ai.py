from enum import StrEnum


class GenerationStatus(StrEnum):
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELED = "canceled"


class LLMConfigurationType(StrEnum):
    USER = "user"
    TEMPLATE = "template"
