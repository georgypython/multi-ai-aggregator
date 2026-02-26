from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from src.core.exceptions.llm import (
    LLMGenerationError,
    InactiveModelError,
    InsufficientBalanceError,
    InvalidModelTypeError,
    UserBalanceNotConfiguredError,
)
from src.core.models.enums import AIModelType
from src.core.schemas.ai import LLMRequestDataSchema
from src.repositories import (
    UserRepository,
    AIModelRepository
)
from .openrouter import OpenRouterService


class LLMService:
    def __init__(
        self,
        session: AsyncSession,
        llm_client: OpenRouterService,
        user_repo: UserRepository,
        ai_model_repo: AIModelRepository,
    ) -> None:
        self.session = session
        self.llm_client = llm_client
        self.user_repo = user_repo
        self.ai_model_repo = ai_model_repo

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

        ai_model = await self.ai_model_repo.get_one_with_llm_prices(
            session=self.session, id=model_id
        )
        if not ai_model:
            raise ValueError(f"AIModel not found or model_id={model_id}")

        if ai_model.model_type != AIModelType.LLM:
            raise InvalidModelTypeError(
                f"Model type is not LLM, model_type={ai_model.model_type}"
            )

        if not ai_model.is_active:
            raise InactiveModelError(f"AIModel innactive for model_id={model_id}")

        llm_price = ai_model.llm_price
        if not llm_price:
            raise ValueError(
                f"AIModel price configuration not found for model_id={model_id}"
            )

        if user.balance.available_tokens < llm_price.min_charge_tokens:
            raise InsufficientBalanceError(
                f"User balance insufficient for this model. Minimal={llm_price.min_charge_tokens}"
            )
        return LLMRequestDataSchema(
            user_id=user_id,
            ai_model_id=model_id,
            provider_model_key=ai_model.provider_key,
            prompt=prompt,
        )
    
    async def generate_llm_response(self, user_id: UUID, model_id: UUID, prompt: str):
        llm_request_data = await self._create_and_validate_request_llm_data(
            user_id=user_id, model_id=model_id, prompt=prompt
        )

        # TODO добавить транзакцию на заморозку баланса юзера + списание + создание генерации
        # Далее реализовать логику запроса. В зависимости от статуса ответа
        # сделать еще одну транзакцию на итоговое списание / отмену списания.
        # вернуть ответ.
