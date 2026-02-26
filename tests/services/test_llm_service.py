from uuid import uuid4
from unittest.mock import AsyncMock

import pytest

from src.services.llm import LLMService


@pytest.mark.asyncio
async def test_generate_llm_response_delegates_to_llm_client() -> None:
    user_id = uuid4()
    model_id = uuid4()
    prompt = "hello"
    expected = {"text": "ok"}

    session = AsyncMock()
    llm_client = AsyncMock()
    llm_client.generate_llm_response = AsyncMock(return_value=expected)

    service = LLMService(session=session, llm_client=llm_client)

    result = await service.generate_llm_response(
        user_id=user_id,
        model_id=model_id,
        prompt=prompt,
    )

    assert result == expected
    llm_client.generate_llm_response.assert_awaited_once_with(
        user_id=user_id,
        model_id=model_id,
        prompt=prompt,
    )
