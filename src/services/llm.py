from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from src.core.exceptions.llm import (
    InactiveModelError,
    InsufficientBalanceError,
    UserBalanceNotConfiguredError,
)
from src.core.models import AIGeneration
from src.core.schemas.ai import LLMRequestDataSchema
from src.repositories import (
    UserRepository,
    LLMRepository,
    GenerationRepository,
)
from .openrouter import OpenRouterService


class LLMService:
    def __init__(
        self,
        session: AsyncSession,
        llm_client: OpenRouterService,
        user_repo: UserRepository,
        llm_repo: LLMRepository,
        generation_repo: GenerationRepository,
    ) -> None:
        self.session = session
        self.llm_client = llm_client
        self.user_repo = user_repo
        self.llm_repo = llm_repo
        self.generation_repo = generation_repo

    async def _create_and_validate_request_llm_data(
        self, user_id: UUID, model_id: UUID, prompt: str
    ) -> LLMRequestDataSchema:
        user = await self.user_repo.get_one_with_balance(
            session=self.session, id=user_id, is_active=True
        )
        if not user:
            raise ValueError(f"Active user not found for user_id={user_id}")

        if not user.balance:
            raise UserBalanceNotConfiguredError(
                f"User balance is not configured for user_id={user_id}"
            )

        llm_model = await self.llm_repo.get_one_with_ai_model(
            session=self.session, ai_model_id=model_id
        )
        if not llm_model or not llm_model.ai_model:
            raise ValueError(f"LLMModel not found for ai_model_id={model_id}")

        ai_model = llm_model.ai_model
        if not ai_model.is_active:
            raise InactiveModelError(f"AIModel innactive for model_id={model_id}")

        if user.balance.available_tokens < llm_model.min_charge_tokens:
            raise InsufficientBalanceError(
                f"User balance insufficient for this model. Minimal={llm_model.min_charge_tokens}"
            )
        return LLMRequestDataSchema(
            user_id=user_id,
            ai_model_id=model_id,
            provider_model_key=ai_model.provider_key,
            prompt=prompt,
            min_charge_tokens=llm_model.min_charge_tokens,
        )

    async def _prepare_generation_and_freeze_user_tokens(
        self, data: LLMRequestDataSchema
    ) -> AIGeneration:
        async with self.session.begin():
            user_id = data.user_id

            balance = await self.user_repo.freeze_tokens(
                session=self.session, user_id=user_id, amount=data.min_charge_tokens
            )
            if not balance:
                raise UserBalanceNotConfiguredError(
                    f"User balance is not configured for user_id={user_id}"
                )
            return await self.generation_repo.create_processing(
                session=self.session,
                user_id=user_id,
                ai_model_id=data.ai_model_id,
            )

    async def generate_llm_response(self, user_id: UUID, model_id: UUID, prompt: str):
        llm_request_data = await self._create_and_validate_request_llm_data(
            user_id=user_id, model_id=model_id, prompt=prompt
        )
        generation = await self._prepare_generation_and_freeze_user_tokens(
            data=llm_request_data
        )
        llm_response = await self.llm_client.get_llm_response(
            provider_model_key=llm_request_data.provider_model_key,
            prompt=llm_request_data.prompt,
        )
        # TODO(next):
        # 1) Добавить user-specific instruction:
        #    - получить из БД/настроек пользователя (опционально),
        #    - передавать в llm_client.get_llm_response(..., instruction=...).
        # 2) Добавить user-specific temperature (опционально):
        #    - валидировать диапазон,
        #    - учитывать поддержку моделью (is_temperature_support),
        #    - передавать в llm_client только если поддерживается.
        # 3) Добавить историю чата из Redis (опционально):
        #    - читать последние N сообщений (10-15),
        #    - прокидывать как chat_history в llm_client,
        #    - после ответа дописывать user/assistant сообщения обратно в Redis,
        #    - на ключ поставить TTL (например, 7 days).
        # 4) Добавить обработку ошибок провайдера:
        #    - timeout/network/http (401/403/429/5xx),
        #    - невалидный формат ответа,
        #    - маппинг на доменные исключения для API-слоя.
        # 5) Реализовать финализацию биллинга и generation:
        #    - success path: tx -> пересчет hold/available + update generation (COMPLETED, charged_tokens),
        #    - fail path: tx -> release hold обратно в available + update generation (FAILED),
        #    - вернуть финальный DTO ответа.
