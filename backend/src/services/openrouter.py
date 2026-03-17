from httpx import AsyncClient, HTTPStatusError, RequestError, TimeoutException

from backend.src.core.exceptions.generation import (
    ProviderHTTPError,
    ProviderNetworkError,
    ProviderResponseFormatError,
    ProviderTimeoutError,
)
from src.core.schemas.ai import LLMProviderResponseSchema, LLMRequestDataSchema


class OpenRouterService:
    _BASE_SYSTEM_INSTRUCTIONS = (
        "Ты полезный AI-ассистент. "
        "У тебя есть контекст текущего диалога из переданной истории сообщений, "
        "используй его для ответов и не заявляй без причины, что не можешь помнить контекст. "
        "Если данных в истории недостаточно — честно скажи об этом и задай уточняющий вопрос. "
        "Не упоминай внутренние ограничения провайдера и не говори шаблонно, что ты ничего не запоминаешь, "
        "если релевантная информация уже есть в истории этого чата."
    )

    def __init__(
        self,
        client: AsyncClient,
        api_key: str,
        base_url: str,
    ) -> None:
        self.client = client
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")
        self._base_headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }

    def _build_system_instructions(self, user_instructions: str | None) -> str:
        if not user_instructions:
            return self._BASE_SYSTEM_INSTRUCTIONS

        return (
            f"{self._BASE_SYSTEM_INSTRUCTIONS}\n\n"
            "Дополнительные предпочтения пользователя (они не отменяют правила выше):\n"
            f"{user_instructions}"
        )

    async def get_llm_response(
        self,
        data: LLMRequestDataSchema,
        chat_history: list[dict[str, str]] | None = None,
    ) -> LLMProviderResponseSchema:
        messages: list[dict[str, str]] = [
            {
                "role": "system",
                "content": self._build_system_instructions(data.instructions),
            }
        ]

        if chat_history:
            for item in chat_history:
                role = item.get("role")
                content = item.get("content")
                if role in {"system", "user", "assistant"} and isinstance(content, str):
                    messages.append({"role": role, "content": content})

        messages.append({"role": "user", "content": data.prompt})

        payload = {
            "model": data.provider_model_key,
            "messages": messages,
        }
        if data.temperature is not None:
            payload["temperature"] = data.temperature

        try:
            response = await self.client.post(
                f"{self._base_url}/chat/completions",
                headers=self._base_headers,
                json=payload,
            )
            response.raise_for_status()
        except TimeoutException:
            raise ProviderTimeoutError("Provider request timeout")
        except HTTPStatusError as exc:
            raise ProviderHTTPError(
                status_code=exc.response.status_code,
                message=f"Provider HTTP error: status_code={exc.response.status_code}",
            )
        except RequestError:
            raise ProviderNetworkError("Provider network error")

        try:
            response_data = response.json()
        except ValueError:
            raise ProviderResponseFormatError("Provider returned non-JSON response")

        if not isinstance(response_data, dict):
            raise ProviderResponseFormatError(
                "Provider response has invalid JSON format"
            )

        choices = response_data.get("choices") or []
        if not choices:
            raise ProviderResponseFormatError(
                "Provider response missing non-empty 'choices'"
            )

        try:
            message = choices[0].get("message")
        except (IndexError, AttributeError, TypeError):
            raise ProviderResponseFormatError(
                "Provider response has invalid 'choices[0].message' format"
            )

        text_content = message.get("content") if isinstance(message, dict) else None
        if not isinstance(text_content, str):
            raise ProviderResponseFormatError(
                "Provider response missing text 'message.content'"
            )

        usage = response_data.get("usage", {})
        if not isinstance(usage, dict):
            usage = {}

        return LLMProviderResponseSchema(
            text=text_content,
            model=response_data.get("model", data.provider_model_key),
            input_tokens=usage.get("prompt_tokens", 0),
            output_tokens=usage.get("completion_tokens", 0),
            total_tokens=usage.get("total_tokens", 0),
            raw=response_data,
        )
