from httpx import AsyncClient

from src.core.schemas.ai import LLMProviderResponseSchema


class OpenRouterService:
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

    async def get_llm_response(
        self,
        *,
        provider_model_key: str,
        prompt: str,
        instruction: str | None = None,
        chat_history: list[dict[str, str]] | None = None,
    ) -> LLMProviderResponseSchema:
        messages: list[dict[str, str]] = []
        if instruction:
            messages.append({"role": "system", "content": instruction})

        if chat_history:
            for item in chat_history:
                role = item.get("role")
                content = item.get("content")
                if role in {"system", "user", "assistant"} and isinstance(content, str):
                    messages.append({"role": role, "content": content})

        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": provider_model_key,
            "messages": messages,
        }
        response = await self.client.post(
            f"{self._base_url}/chat/completions",
            headers=self._base_headers,
            json=payload,
        )
        response.raise_for_status()

        data = response.json()
        choices = data.get("choices", [])
        first_choice = choices[0] if choices else {}
        message = first_choice.get("message", {})
        usage = data.get("usage", {})

        return LLMProviderResponseSchema(
            text=message.get("content", ""),
            model=data.get("model", provider_model_key),
            input_tokens=usage.get("prompt_tokens", 0),
            output_tokens=usage.get("completion_tokens", 0),
            total_tokens=usage.get("total_tokens", 0),
            raw=data,
        )
