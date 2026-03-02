from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from src.core.exceptions.llm import (
    InactiveModelError,
    InsufficientBalanceError,
    UserBalanceNotConfiguredError,
    ProviderError,
)
from src.core.models import AIGeneration, LLMConfiguration
from src.core.models.enums import PriceType, ModelType, LLMConfigurationType
from src.core.schemas.ai import (
    AIModelListItemResponseSchema,
    LLMConfigCreateRequestSchema,
    LLMConfigResponseSchema,
    LLMRequestDataSchema,
    LLMProviderResponseSchema,
    LLMResultResponseSchema,
)
from src.repositories import (
    AIModelRepository,
    UserRepository,
    LLMRepository,
    LLMConfigurationRepository,
    GenerationRepository,
    ChatMemoryRepository,
    TokenPriceRepository,
)
from .openrouter import OpenRouterService
from src.core.logger_setup import logger


class LLMService:
    def __init__(
        self,
        session: AsyncSession,
        llm_client: OpenRouterService,
        ai_model_repo: AIModelRepository,
        user_repo: UserRepository,
        llm_repo: LLMRepository,
        llm_configuration_repo: LLMConfigurationRepository,
        generation_repo: GenerationRepository,
        chat_memory_repo: ChatMemoryRepository,
        token_price_repo: TokenPriceRepository,
    ) -> None:
        self.session = session
        self.llm_client = llm_client
        self.ai_model_repo = ai_model_repo
        self.user_repo = user_repo
        self.llm_repo = llm_repo
        self.llm_configuration_repo = llm_configuration_repo
        self.generation_repo = generation_repo
        self.chat_memory_repo = chat_memory_repo
        self.token_price_repo = token_price_repo

    def _build_llm_config_response(self, config: LLMConfiguration) -> LLMConfigResponseSchema:
        return LLMConfigResponseSchema(
            id=config.id,
            user_id=config.user_id,
            name=config.name,
            configuration_type=config.configuration_type,
            temperature=config.temperature,
            instructions=config.instructions,
            created_at=config.created_at,
        )

    async def create_or_update_user_llm_config(
        self,
        user_id: UUID,
        payload: LLMConfigCreateRequestSchema,
    ) -> LLMConfigResponseSchema:
        user = await self.user_repo.get_one(
            session=self.session,
            id=user_id,
            is_active=True,
        )
        if not user:
            raise ValueError(f"Active user not found for user_id={user_id}")

        llm_config = await self.llm_configuration_repo.get_one(
            session=self.session,
            user_id=user_id,
            configuration_type=LLMConfigurationType.USER,
        )

        payload_data = payload.model_dump(exclude_unset=True)
        if not llm_config:
            llm_config = self.llm_configuration_repo.add_user_config(
                session=self.session,
                user_id=user_id,
                data=payload_data,
            )
        else:
            for key, value in payload_data.items():
                setattr(llm_config, key, value)

        await self.session.commit()
        await self.session.refresh(llm_config)

        return self._build_llm_config_response(llm_config)

    async def get_user_llm_config(
        self,
        user_id: UUID,
    ) -> LLMConfigResponseSchema:
        user = await self.user_repo.get_one(
            session=self.session,
            id=user_id,
            is_active=True,
        )
        if not user:
            raise ValueError(f"Active user not found for user_id={user_id}")

        config = await self.llm_configuration_repo.get_one(
            session=self.session,
            user_id=user_id,
            configuration_type=LLMConfigurationType.USER,
        )
        if not config:
            raise ValueError(f"LLMConfiguration not found for user_id={user_id}")

        return self._build_llm_config_response(config=config)

    async def get_ai_models_list(
        self,
        user_id: UUID,
        model_type: ModelType | None = None,
        active_only: bool = True,
    ) -> list[AIModelListItemResponseSchema]:
        async with self.session.begin():
            user = await self.user_repo.get_one(
                session=self.session,
                id=user_id,
                is_active=True,
            )
            if not user:
                raise ValueError(f"Active user not found for user_id={user_id}")

            filters: dict[str, object] = {}
            if model_type is not None:
                filters["model_type"] = model_type
            if active_only:
                filters["is_active"] = True

            ai_models = await self.ai_model_repo.get_all(session=self.session, **filters)

        result: list[AIModelListItemResponseSchema] = []
        for ai_model in ai_models:
            result.append(
                AIModelListItemResponseSchema(
                    id=ai_model.id,
                    name=ai_model.name,
                    provider_key=ai_model.provider_key,
                    is_active=ai_model.is_active,
                    description=ai_model.description,
                    model_type=ai_model.model_type,
                    created_at=ai_model.created_at,
                )
            )
        return result

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
                min_charge_tokens=llm_model.min_charge_tokens,
                free_requests_limit=llm_model.free_requests_limit,
                input_price_per_million_usd=llm_model.input_price_per_million_usd,
                output_price_per_million_usd=llm_model.output_price_per_million_usd,
                temperature=temperature if temperature else None,
                instructions=instructions if instructions else None,
            )

    async def _prepare_generation_and_freeze_user_tokens(
        self, data: LLMRequestDataSchema
    ) -> AIGeneration:
        async with self.session.begin():
            user_id = data.user_id

            balance = await self.user_repo.get_balance_for_update(
                session=self.session,
                user_id=user_id,
            )
            if not balance:
                raise UserBalanceNotConfiguredError(
                    f"User balance is not configured for user_id={user_id}"
                )

            has_free_request = False
            if data.free_requests_limit > 0:
                generation_count = await self.generation_repo.count_by_user_and_model(
                    session=self.session,
                    user_id=user_id,
                    ai_model_id=data.ai_model_id,
                    max_count=data.free_requests_limit,
                )
                has_free_request = generation_count < data.free_requests_limit

            if has_free_request:
                data.min_charge_tokens = 0
                return await self.generation_repo.create_processing(
                    session=self.session,
                    user_id=user_id,
                    ai_model_id=data.ai_model_id,
                )

            if balance.available_tokens < data.min_charge_tokens:
                raise InsufficientBalanceError(
                    f"User balance insufficient for this model. Minimal={data.min_charge_tokens}"
                )

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

    async def _rollback_failed_generation(
        self,
        data: LLMRequestDataSchema,
        generation_id: UUID,
    ) -> None:
        async with self.session.begin():
            if data.min_charge_tokens > 0:
                await self.user_repo.release_tokens(
                    session=self.session,
                    user_id=data.user_id,
                    amount=data.min_charge_tokens,
                )
            await self.generation_repo.mark_failed(
                session=self.session,
                generation_id=generation_id,
            )
    
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

        final_tokens_cost = 0.0

        async with self.session.begin():
            usage_token_price = await self.token_price_repo.get_one(
                session=self.session,
                price_type=PriceType.USAGE,
                is_active=True,
            )
            if not usage_token_price:
                raise RuntimeError("Active USAGE token price not configured")
            if usage_token_price.usd_per_token <= 0:
                raise RuntimeError("USAGE usd_per_token must be greater than 0")
            if usage_token_price.provider_cost_multiplier is None:
                raise RuntimeError("USAGE provider_cost_multiplier is None")

            if request.min_charge_tokens > 0:
                provider_cost_multiplier = usage_token_price.provider_cost_multiplier
                final_usd_cost = provider_cost * provider_cost_multiplier
                final_tokens_cost = final_usd_cost / usage_token_price.usd_per_token
            else:
                final_tokens_cost = 0.0

            balance = await self.user_repo.settle_hold_tokens(
                session=self.session,
                user_id=request.user_id,
                hold_amount=float(request.min_charge_tokens),
                final_charge_amount=final_tokens_cost,
            )
            if not balance:
                raise UserBalanceNotConfiguredError(
                    f"User balance is not configured for user_id={request.user_id}"
                )

            completed_generation = await self.generation_repo.mark_completed(
                session=self.session,
                generation_id=generation_id,
                charged_tokens=final_tokens_cost,
            )
            if not completed_generation:
                raise RuntimeError(
                    f"Generation not found for generation_id={generation_id}"
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

        chat_history = await self.chat_memory_repo.get_chat_history(user_id=user_id)

        generation = await self._prepare_generation_and_freeze_user_tokens(
            data=llm_request_data
        )
        generation_id = generation.id
        try:
            llm_response = await self.llm_client.get_llm_response(
                data=llm_request_data,
                chat_history=chat_history,
            )
        except ProviderError:
            await self._rollback_failed_generation(
                data=llm_request_data,
                generation_id=generation_id,
            )
            raise
        except Exception as e:
            await self._rollback_failed_generation(
                data=llm_request_data,
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
            await self._rollback_failed_generation(
                data=llm_request_data,
                generation_id=generation_id,
            )
            logger.exception("Failed to finalize generation for user_id=%s", user_id)
            raise RuntimeError(f"Failed to finalize generation: {e}")
        
        return final_llm_result
