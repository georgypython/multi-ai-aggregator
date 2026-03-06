from enum import StrEnum


class GenerationStatus(StrEnum):
    CREATED = "created"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELED = "canceled"


class GenerationType(StrEnum):
    LLM = "llm"
    IMAGE = "image"
    VIDEO = "video"


class ModelProvider(StrEnum):
    OPENAI = "openai"
    GOOGLE = "google"


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
    