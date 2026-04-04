from unittest.mock import AsyncMock
from uuid import uuid4
from decimal import Decimal

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.models import (
    AIModel,
    LLMConfiguration,
    LLMModel,
    User,
    UserBalance,
    AIGeneration,
)
from src.core.models.enums import GenerationStatus, LLMConfigurationType, ModelType
from src.core.schemas.ai import GenerationRequestSchema
from src.services.generation_billing import GenerationBillingService
from src.services.llm_generation import LLMGenerationService

pytestmark = pytest.mark.asyncio


async def test_create_and_validate_request_llm_data_uses_user_llm_configuration(
    db_session: AsyncSession,
) -> None:
    provider_key = f"openai/gpt-4o-mini-{uuid4()}"

    ai_model = AIModel(
        name="GPT-4o mini",
        provider_key=provider_key,
        is_active=True,
        model_type=ModelType.LLM,
        min_charge_tokens=10,
        free_requests_limit=0,
    )
    db_session.add(ai_model)
    await db_session.flush()

    llm_model = LLMModel(
        ai_model_id=ai_model.id,
        input_price_per_million_usd=0.15,
        output_price_per_million_usd=0.60,
        is_temperature_support=True,
    )
    db_session.add(llm_model)
    await db_session.flush()

    user = User(telegram_id=10_000_001, is_active=True)
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
    await db_session.commit()

    generation_billing = GenerationBillingService(
        session=db_session,
        token_scale=Decimal("0.000001"),
    )

    llm_service = LLMGenerationService(
        session=db_session,
        llm_client=AsyncMock(),
        chat_memory_service=AsyncMock(),
        generation_billing_service=generation_billing,
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

    ai_model = AIModel(
        name="GPT-4o mini",
        provider_key=provider_key,
        is_active=True,
        model_type=ModelType.LLM,
        min_charge_tokens=15,
        free_requests_limit=0,
    )
    db_session.add(ai_model)
    await db_session.flush()

    llm_model = LLMModel(
        ai_model_id=ai_model.id,
        input_price_per_million_usd=0.15,
        output_price_per_million_usd=0.60,
        is_temperature_support=True,
    )
    db_session.add(llm_model)
    await db_session.flush()

    user = User(telegram_id=10_000_002, is_active=True)
    db_session.add(user)
    await db_session.flush()

    db_session.add(
        UserBalance(user_id=user.id, available_tokens=100.0, hold_tokens=0.0)
    )
    await db_session.flush()
    await db_session.commit()

    generation_billing = GenerationBillingService(
        session=db_session,
        token_scale=Decimal("0.000001"),
    )

    llm_service = LLMGenerationService(
        session=db_session,
        llm_client=AsyncMock(),
        chat_memory_service=AsyncMock(),
        generation_billing_service=generation_billing,
    )

    data = GenerationRequestSchema(
        user_id=user.id,
        ai_model_id=llm_model.ai_model_id,
        min_charge_tokens=15,
        free_requests_limit=0,
    )

    result = await generation_billing.prepare_generation_and_freeze_user_tokens(
        data=data
    )

    assert isinstance(result, AIGeneration)
    assert result.user_id == user.id
    assert result.ai_model_id == llm_model.ai_model_id
    assert result.status == GenerationStatus.PROCESSING

    balance = await db_session.scalar(
        select(UserBalance).where(UserBalance.user_id == user.id)
    )
    assert balance is not None
    assert balance.available_tokens == 85.0
    assert balance.hold_tokens == 15.0

    generation_in_db = await db_session.scalar(
        select(AIGeneration).where(AIGeneration.id == result.id)
    )
    assert generation_in_db is not None
