from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import pytest
import pytest_asyncio
from httpx import HTTPStatusError, Request, Response, TimeoutException

from src.core.exceptions.llm import (
    ProviderHTTPError,
    ProviderResponseFormatError,
    ProviderTimeoutError,
)
from src.core.schemas.ai import LLMRequestDataSchema
from src.services.openrouter import OpenRouterService


@pytest_asyncio.fixture(autouse=True)
async def clean_db():
    yield


def _build_request_data() -> LLMRequestDataSchema:
    return LLMRequestDataSchema(
        user_id=uuid4(),
        ai_model_id=uuid4(),
        provider_model_key="openai/gpt-4o-mini",
        prompt="hello",
        min_charge_tokens=10,
        temperature=0.3,
        instructions="Be concise",
    )


@pytest.mark.asyncio
async def test_get_llm_response_success_builds_payload_and_parses_response() -> None:
    data = _build_request_data()
    client = AsyncMock()

    response = Mock()
    response.raise_for_status = Mock()
    response.json = Mock(
        return_value={
            "model": "openai/gpt-4o-mini",
            "choices": [{"message": {"content": "ok"}}],
            "usage": {
                "prompt_tokens": 12,
                "completion_tokens": 8,
                "total_tokens": 20,
            },
        }
    )
    client.post = AsyncMock(return_value=response)

    service = OpenRouterService(client=client, api_key="test-key", base_url="https://openrouter.ai/api/v1")

    result = await service.get_llm_response(
        data=data,
        chat_history=[{"role": "assistant", "content": "prev"}],
    )

    assert result.text == "ok"
    assert result.model == "openai/gpt-4o-mini"
    assert result.total_tokens == 20

    _, kwargs = client.post.call_args
    assert kwargs["json"]["model"] == "openai/gpt-4o-mini"
    assert kwargs["json"]["temperature"] == 0.3
    assert kwargs["json"]["messages"][0] == {"role": "system", "content": "Be concise"}


@pytest.mark.asyncio
async def test_get_llm_response_raises_provider_timeout_error() -> None:
    data = _build_request_data()
    client = AsyncMock()
    client.post = AsyncMock(side_effect=TimeoutException("timeout"))
    service = OpenRouterService(client=client, api_key="test-key", base_url="https://openrouter.ai/api/v1")

    with pytest.raises(ProviderTimeoutError):
        await service.get_llm_response(data=data)


@pytest.mark.asyncio
async def test_get_llm_response_raises_provider_http_error() -> None:
    data = _build_request_data()
    client = AsyncMock()

    request = Request("POST", "https://openrouter.ai/api/v1/chat/completions")
    response = Response(status_code=429, request=request)
    client.post = AsyncMock(
        side_effect=HTTPStatusError("rate limited", request=request, response=response)
    )
    service = OpenRouterService(client=client, api_key="test-key", base_url="https://openrouter.ai/api/v1")

    with pytest.raises(ProviderHTTPError) as exc_info:
        await service.get_llm_response(data=data)

    assert exc_info.value.status_code == 429


@pytest.mark.asyncio
async def test_get_llm_response_raises_format_error_on_missing_choices() -> None:
    data = _build_request_data()
    client = AsyncMock()

    response = Mock()
    response.raise_for_status = Mock()
    response.json = Mock(return_value={"model": "openai/gpt-4o-mini"})
    client.post = AsyncMock(return_value=response)

    service = OpenRouterService(client=client, api_key="test-key", base_url="https://openrouter.ai/api/v1")

    with pytest.raises(ProviderResponseFormatError):
        await service.get_llm_response(data=data)
