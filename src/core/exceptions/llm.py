class LLMGenerationError(Exception): ...


class InactiveModelError(LLMGenerationError): ...


class InsufficientBalanceError(LLMGenerationError): ...


class InvalidModelTypeError(LLMGenerationError): ...


class UserBalanceNotConfiguredError(LLMGenerationError): ...


class ProviderError(LLMGenerationError): ...


class ProviderTimeoutError(ProviderError): ...


class ProviderNetworkError(ProviderError): ...


class ProviderHTTPError(ProviderError):
    def __init__(self, status_code: int, message: str | None = None) -> None:
        self.status_code = status_code
        super().__init__(message or f"Provider HTTP error: status_code={status_code}")


class ProviderResponseFormatError(ProviderError): ...
