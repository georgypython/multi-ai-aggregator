from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.models import AIModel, LLMConfiguration, LLMModel, User, UserBalance, AIGeneration
from src.core.models.enums import GenerationStatus, LLMConfigurationType
from src.core.schemas.ai import LLMRequestDataSchema
from src.repositories.generation import GenerationRepository
from src.repositories.llm import LLMRepository
from src.repositories.users import UserRepository
from src.services.llm import LLMService

pytestmark = pytest.mark.asyncio



async def test_create_and_validate_request_llm_data_uses_user_llm_configuration(
    db_session: AsyncSession,
) -> None:
    provider_key = f"openai/gpt-4o-mini-{uuid4()}"

    ai_model = AIModel(name="GPT-4o mini", provider_key=provider_key, is_active=True)
    db_session.add(ai_model)
    await db_session.flush()

    llm_model = LLMModel(
        ai_model_id=ai_model.id,
        input_price_per_million_usd=0.15,
        output_price_per_million_usd=0.60,
        min_charge_tokens=10,
        is_temperature_support=True,
        provider_price_usd=0.001,
        our_price_tokens=10,
        min_req_tokens=1,
    )
    db_session.add(llm_model)
    await db_session.flush()

    user = User(is_active=True)
    db_session.add(user)
    await db_session.flush()

    db_session.add_all(
        [
            UserBalance(user_id=user.id, available_tokens=100.0, hold_tokens=0.0),
            LLMConfiguration(
                user_id=user.id,
                configuration_type=LLMConfigurationType.USER,
                temperature=0.3,
                instructions="Be concise",
            ),
        ]
    )
    await db_session.flush()

    llm_service = LLMService(
        session=db_session,
        llm_client=AsyncMock(),
        user_repo=UserRepository(),
        llm_repo=LLMRepository(),
        generation_repo=GenerationRepository(),
        chat_memory_repo=AsyncMock(),
        token_price_repo=AsyncMock(),
    )

    data = await llm_service._create_and_validate_request_llm_data(
        user_id=user.id,
        model_id=llm_model.ai_model_id,
        prompt="test prompt",
    )

    assert data.user_id == user.id
    assert data.ai_model_id == llm_model.ai_model_id
    assert data.provider_model_key == provider_key
    assert data.min_charge_tokens == 10
    assert data.temperature == 0.3
    assert data.instructions == "Be concise"


async def test_prepare_generation_and_freeze_user_tokens_creates_processing_generation(
    db_session: AsyncSession,
) -> None:
    provider_key = f"openai/gpt-4o-mini-{uuid4()}"

    ai_model = AIModel(name="GPT-4o mini", provider_key=provider_key, is_active=True)
    db_session.add(ai_model)
    await db_session.flush()

    llm_model = LLMModel(
        ai_model_id=ai_model.id,
        input_price_per_million_usd=0.15,
        output_price_per_million_usd=0.60,
        min_charge_tokens=15,
        is_temperature_support=True,
        provider_price_usd=0.001,
        our_price_tokens=10,
        min_req_tokens=1,
    )
    db_session.add(llm_model)
    await db_session.flush()

    user = User(is_active=True)
    db_session.add(user)
    await db_session.flush()

    db_session.add(UserBalance(user_id=user.id, available_tokens=100.0, hold_tokens=0.0))
    await db_session.flush()
    await db_session.commit()

    llm_service = LLMService(
        session=db_session,
        llm_client=AsyncMock(),
        user_repo=UserRepository(),
        llm_repo=LLMRepository(),
        generation_repo=GenerationRepository(),
        chat_memory_repo=AsyncMock(),
        token_price_repo=AsyncMock(),
    )

    data = LLMRequestDataSchema(
        user_id=user.id,
        ai_model_id=llm_model.ai_model_id,
        provider_model_key=provider_key,
        prompt="test",
        min_charge_tokens=15,
        temperature=None,
        instructions=None,
    )

    result = await llm_service._prepare_generation_and_freeze_user_tokens(data=data)

    assert isinstance(result, AIGeneration)
    assert result.user_id == user.id
    assert result.ai_model_id == llm_model.ai_model_id
    assert result.status == GenerationStatus.PROCESSING

    balance = await db_session.scalar(select(UserBalance).where(UserBalance.user_id == user.id))
    assert balance is not None
    assert balance.available_tokens == 85.0
    assert balance.hold_tokens == 15.0

    generation_in_db = await db_session.scalar(
        select(AIGeneration).where(AIGeneration.id == result.id)
    )
    assert generation_in_db is not None
