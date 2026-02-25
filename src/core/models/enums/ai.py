from enum import StrEnum


class ProviderType(StrEnum):
    OPENROUTER = "open_router"
    WAVESPEED = "wave_speed"
    

class AIModelType(StrEnum):
    LLM = "llm"
    IMAGE = "image"
    VIDEO = "video"
    

class GenerationStatus(StrEnum):
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELED = "canceled"
