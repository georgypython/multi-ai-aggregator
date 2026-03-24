class AIGenerationError(Exception): ...


class InactiveModelError(AIGenerationError): ...


class InsufficientBalanceError(AIGenerationError): ...


class UserBalanceNotConfiguredError(AIGenerationError): ...


class ProviderError(AIGenerationError): ...


class ProviderTimeoutError(ProviderError): ...


class ProviderNetworkError(ProviderError): ...


class ProviderHTTPError(ProviderError):
    def __init__(self, status_code: int, message: str | None = None) -> None:
        self.status_code = status_code
        super().__init__(message or f"Provider HTTP error: status_code={status_code}")


class ProviderResponseFormatError(ProviderError): ...


class ModelConfigError(AIGenerationError): ...


class MediaGenerationNotCompletedError(AIGenerationError): ...


class ImageGenerationNotCompletedError(MediaGenerationNotCompletedError): ...
