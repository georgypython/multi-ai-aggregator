from enum import StrEnum


class GenerationStatus(StrEnum):
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELED = "canceled"


class LLMConfigurationType(StrEnum):
    USER = "user"
    TEMPLATE = "template"


class PriceType(StrEnum):
    SUBSCRIPTION = "subscription"
    ONE_TIME = "one_time"
    USAGE = "usage"


class ModelType(StrEnum):
    LLM = "llm"
    IMAGE = "image"
    VIDEO = "video"
    