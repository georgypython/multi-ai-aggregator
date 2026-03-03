from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from src.core.exceptions.llm import (
    InactiveModelError,
    UserBalanceNotConfiguredError,
    ProviderError,
)
from src.core.schemas.ai import (
    GenerationRequestSchema,
    GenerationResultSchema,
    LLMRequestDataSchema,
    LLMProviderResponseSchema,
    LLMResultResponseSchema,
)
from src.repositories import (
    UserRepository,
    LLMRepository,
    ChatMemoryRepository,
)
from .openrouter import OpenRouterService
from .generation_billing import GenerationBillingService
from src.core.logger_setup import logger


class LLMGenerationService:
    def __init__(
        self,
        session: AsyncSession,
        llm_client: OpenRouterService,
        user_repo: UserRepository,
        llm_repo: LLMRepository,
        chat_memory_repo: ChatMemoryRepository,
        generation_billing_service: GenerationBillingService,
    ) -> None:
        self.session = session
        self.llm_client = llm_client
        self.user_repo = user_repo
        self.llm_repo = llm_repo
        self.chat_memory_repo = chat_memory_repo
        self.generation_billing_service = generation_billing_service

    async def _create_and_validate_request_llm_data(
        self,
        user_id: UUID,
        model_id: UUID,
        prompt: str,
    ) -> LLMRequestDataSchema:
        async with self.session.begin():
            user = await self.user_repo.get_one_with_balance_and_llm_configuration(
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

            instructions = None
            temperature = None
            if user.llm_configuration:
                llm_configuration = user.llm_configuration
                instructions = llm_configuration.instructions
                temperature = (
                    llm_configuration.temperature
                    if llm_model.is_temperature_support
                    else None
                )

            return LLMRequestDataSchema(
                user_id=user_id,
                ai_model_id=model_id,
                provider_model_key=ai_model.provider_key,
                prompt=prompt,
                min_charge_tokens=ai_model.min_charge_tokens,
                free_requests_limit=ai_model.free_requests_limit,
                input_price_per_million_usd=llm_model.input_price_per_million_usd,
                output_price_per_million_usd=llm_model.output_price_per_million_usd,
                temperature=temperature if temperature else None,
                instructions=instructions if instructions else None,
            )

    def _calculate_provider_cost(
        self,
        response: LLMProviderResponseSchema,
        request: LLMRequestDataSchema,
    ) -> float:
        if (
            request.input_price_per_million_usd is None
            or request.output_price_per_million_usd is None
        ):
            raise RuntimeError("Unable to calculate provider cost without model prices")

        input_cost = (
            response.input_tokens / 1_000_000
        ) * request.input_price_per_million_usd
        output_cost = (
            response.output_tokens / 1_000_000
        ) * request.output_price_per_million_usd
        return input_cost + output_cost

    async def _finish_llm_generation(
        self,
        response: LLMProviderResponseSchema,
        request: LLMRequestDataSchema,
        generation_id: UUID,
    ) -> LLMResultResponseSchema:
        provider_cost = 0.0
        if request.min_charge_tokens > 0:
            provider_cost = self._calculate_provider_cost(
                response=response,
                request=request,
            )
        response.provider_cost = provider_cost
        final_tokens_cost = await self.generation_billing_service.finalize_generation_billing(
            data=GenerationResultSchema(
                user_id=request.user_id,
                generation_id=generation_id,
                hold_amount=float(request.min_charge_tokens),
                provider_cost=provider_cost,
            ),
        )

        return LLMResultResponseSchema(
            text=response.text,
            ai_model_id=request.ai_model_id,
            user_id=request.user_id,
            generation_id=generation_id,
            tokens_cost=final_tokens_cost,
        )

    async def generate_llm_response(
        self,
        user_id: UUID,
        model_id: UUID,
        prompt: str,
    ):
        llm_request_data = await self._create_and_validate_request_llm_data(
            user_id=user_id,
            model_id=model_id,
            prompt=prompt,
        )
        billing_request_data = GenerationRequestSchema(
            user_id=llm_request_data.user_id,
            ai_model_id=llm_request_data.ai_model_id,
            min_charge_tokens=llm_request_data.min_charge_tokens,
            free_requests_limit=llm_request_data.free_requests_limit,
        )

        chat_history = await self.chat_memory_repo.get_chat_history(user_id=user_id)

        generation = await self.generation_billing_service.prepare_generation_and_freeze_user_tokens(
            data=billing_request_data
        )
        generation_id = generation.id
        try:
            llm_response = await self.llm_client.get_llm_response(
                data=llm_request_data,
                chat_history=chat_history,
            )
        except ProviderError:
            await self.generation_billing_service.rollback_failed_generation(
                data=billing_request_data,
                generation_id=generation_id,
            )
            raise
        except Exception as e:
            await self.generation_billing_service.rollback_failed_generation(
                data=billing_request_data,
                generation_id=generation_id,
            )
            logger.exception("Unexpected LLM provider error for user_id=%s", user_id)
            raise RuntimeError(f"Unexpected LLM provider error: {e}")

        await self.chat_memory_repo.append_user_and_assistant_messages(
            user_id=user_id,
            user_prompt=prompt,
            assistant_response=llm_response.text,
        )

        try:
            final_llm_result = await self._finish_llm_generation(
                response=llm_response,
                request=llm_request_data,
                generation_id=generation_id,
            )
        except Exception as e:
            await self.generation_billing_service.rollback_failed_generation(
                data=billing_request_data,
                generation_id=generation_id,
            )
            logger.exception("Failed to finalize generation for user_id=%s", user_id)
            raise RuntimeError(f"Failed to finalize generation: {e}")
        
        return final_llm_result
