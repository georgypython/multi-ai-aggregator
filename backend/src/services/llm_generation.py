from uuid import UUID
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.models.enums import GenerationType, GenerationStatus
from src.models import LLMProfile, User
from src.exceptions.generation import (
    InactiveModelError,
    ProviderError,
    UserBalanceNotConfiguredError,
)
from src.schemas import (
    GenerationFinishData,
    GenerationResultResponseDataSchema,
    LLMRequestDataSchema,
    LLMProviderResponseSchema,
)
from .openrouter import OpenRouterService
from .generation_billing import GenerationBillingService
from src.core.logger_setup import logger
from src.services.chat_memory import ChatMemoryService
from src.services.db_access import DBAccessService


class LLMGenerationService(DBAccessService):
    def __init__(
        self,
        session: AsyncSession,
        llm_client: OpenRouterService,
        chat_memory_service: ChatMemoryService,
        generation_billing_service: GenerationBillingService,
    ) -> None:
        self.session = session
        self.llm_client = llm_client
        self.chat_memory_service = chat_memory_service
        self.generation_billing_service = generation_billing_service

    async def _get_user_with_balance_and_llm_config(
        self, *, user_id: UUID
    ) -> User | None:
        stmt = (
            select(User)
            .options(
                selectinload(User.balance),
                selectinload(User.llm_configuration),
            )
            .filter_by(id=user_id, is_active=True)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def _get_llm_profile_with_ai_model(
        self, *, ai_model_id: UUID
    ) -> LLMProfile | None:
        stmt = (
            select(LLMProfile)
            .options(selectinload(LLMProfile.ai_model))
            .where(LLMProfile.ai_model_id == ai_model_id)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def _create_and_validate_request_llm_data(
        self,
        user_id: UUID,
        model_id: UUID,
        prompt: str,
    ) -> LLMRequestDataSchema:
        async with self.session.begin():
            user = await self._get_user_with_balance_and_llm_config(user_id=user_id)
            if not user:
                raise ValueError(f"Active user not found for user_id={user_id}")

            if not user.balance:
                raise UserBalanceNotConfiguredError(
                    f"User balance is not configured for user_id={user_id}"
                )

            llm_profile = await self._get_llm_profile_with_ai_model(
                ai_model_id=model_id
            )
            if not llm_profile or not llm_profile.ai_model:
                raise ValueError(f"LLMModel not found for ai_model_id={model_id}")

            ai_model = llm_profile.ai_model
            if not ai_model.is_active:
                raise InactiveModelError(f"AIModel innactive for model_id={model_id}")

            instructions = None
            temperature = None
            if user.llm_configuration:
                llm_configuration = user.llm_configuration
                instructions = llm_configuration.instructions
                temperature = (
                    llm_configuration.temperature
                    if llm_profile.is_temperature_support
                    else None
                )

            return LLMRequestDataSchema(
                user_id=user_id,
                ai_model_id=model_id,
                generation_type=GenerationType.LLM,
                provider_model_key=ai_model.provider_key,
                prompt=prompt,
                model_token_price_id=llm_profile.ai_model.token_price_id,
                hold_amount=ai_model.min_charge_tokens,
                free_requests_limit=ai_model.free_requests_limit,
                input_price_per_million_usd=llm_profile.input_price_per_million_usd,
                output_price_per_million_usd=llm_profile.output_price_per_million_usd,
                temperature=temperature if temperature else None,
                instructions=instructions if instructions else None,
            )

    def _calculate_provider_cost(
        self,
        response: LLMProviderResponseSchema,
        request: LLMRequestDataSchema,
    ) -> Decimal:
        if (
            request.input_price_per_million_usd is None
            or request.output_price_per_million_usd is None
        ):
            raise RuntimeError("Unable to calculate provider cost without model prices")

        million = Decimal("1000000")
        input_cost = (
            Decimal(response.input_tokens) / million
        ) * request.input_price_per_million_usd
        output_cost = (
            Decimal(response.output_tokens) / million
        ) * request.output_price_per_million_usd
        return input_cost + output_cost

    async def generate_llm_response(
        self,
        user_id: UUID,
        model_id: UUID,
        prompt: str,
    ) -> GenerationResultResponseDataSchema:
        llm_request_data = await self._create_and_validate_request_llm_data(
            user_id=user_id,
            model_id=model_id,
            prompt=prompt,
        )

        chat_history = await self.chat_memory_service.get_chat_history(user_id=user_id)

        generation = await self.generation_billing_service.prepare_generation_and_freeze_user_tokens(
            data=llm_request_data
        )
        generation_id = generation.id
        try:
            llm_response = await self.llm_client.get_llm_response(
                data=llm_request_data,
                chat_history=chat_history,
            )
        except ProviderError:
            await self.generation_billing_service.rollback_failed_generation(
                user_id=llm_request_data.user_id,
                hold_amount=llm_request_data.hold_amount,
                generation_id=generation_id,
            )
            raise
        except Exception as e:
            await self.generation_billing_service.rollback_failed_generation(
                user_id=llm_request_data.user_id,
                hold_amount=llm_request_data.hold_amount,
                generation_id=generation_id,
            )
            logger.exception("Unexpected LLM provider error for user_id=%s", user_id)
            raise RuntimeError(f"Unexpected LLM provider error: {e}")

        await self.chat_memory_service.append_user_and_assistant_messages(
            user_id=user_id,
            user_prompt=prompt,
            assistant_response=llm_response.text,
        )

        provider_cost = Decimal("0")
        final_tokens_cost = llm_request_data.hold_amount
        if llm_request_data.hold_amount > 0:
            provider_cost = self._calculate_provider_cost(
                response=llm_response,
                request=llm_request_data,
            )
            async with self.session.begin():
                final_tokens_cost = (
                    await self.generation_billing_service.calculate_final_tokens_cost(
                        hold_amount=llm_request_data.hold_amount,
                        model_token_price_id=llm_request_data.model_token_price_id,
                        provider_cost=provider_cost,
                    )
                )

        return await self.generation_billing_service.finish_generation(
            data=GenerationFinishData(
                ai_model_id=llm_request_data.ai_model_id,
                generation_id=generation_id,
                user_id=llm_request_data.user_id,
                generation_type=llm_request_data.generation_type,
                hold_amount=llm_request_data.hold_amount,
                final_tokens_cost=final_tokens_cost,
                provider_status=GenerationStatus.COMPLETED,
                text=llm_response.text,
            )
        )
