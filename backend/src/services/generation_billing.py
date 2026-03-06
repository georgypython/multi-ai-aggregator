from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from src.core.exceptions.llm import (
    InsufficientBalanceError,
    UserBalanceNotConfiguredError,
)
from src.core.models import AIGeneration
from src.core.models.enums import PriceType, GenerationStatus, GenerationType
from src.core.schemas.ai import (
    GenerationRequestSchema,
    GenerationResultSchema,
    GenerationFinishData,
    GenerationResultResponseDataSchema,
)
from src.repositories import (
    UserRepository,
    GenerationRepository,
    TokenPriceRepository,
)


class GenerationBillingService:
    def __init__(
        self,
        session: AsyncSession,
        user_repo: UserRepository,
        generation_repo: GenerationRepository,
        token_price_repo: TokenPriceRepository,
    ) -> None:
        self.session = session
        self.user_repo = user_repo
        self.generation_repo = generation_repo
        self.token_price_repo = token_price_repo

    async def prepare_generation_and_freeze_user_tokens(
        self, data: GenerationRequestSchema
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
                data.hold_amount = 0
                return await self.generation_repo.create_processing(
                    session=self.session,
                    user_id=user_id,
                    ai_model_id=data.ai_model_id,
                    generation_type=data.generation_type,
                )

            if balance.available_tokens < data.hold_amount:
                raise InsufficientBalanceError(
                    f"User balance insufficient for this model. Minimal={data.hold_amount}"
                )

            balance = await self.user_repo.freeze_tokens(
                session=self.session, user_id=user_id, amount=data.hold_amount
            )
            if not balance:
                raise UserBalanceNotConfiguredError(
                    f"User balance is not configured for user_id={user_id}"
                )
            return await self.generation_repo.create_processing(
                session=self.session,
                user_id=user_id,
                ai_model_id=data.ai_model_id,
                generation_type=data.generation_type,
            )

    async def set_generation_task_id(
        self,
        generation_id: UUID,
        task_id: str,
    ) -> AIGeneration:
        async with self.session.begin():
            generation = await self.generation_repo.set_task_id(
                session=self.session,
                generation_id=generation_id,
                task_id=task_id,
            )
            if not generation:
                raise RuntimeError(
                    f"Generation not found for generation_id={generation_id}"
                )
            return generation
        
    async def rollback_failed_generation(
        self,
        data: GenerationRequestSchema,
        generation_id: UUID,
    ) -> None:
        async with self.session.begin():
            if data.hold_amount > 0:
                await self.user_repo.release_tokens(
                    session=self.session,
                    user_id=data.user_id,
                    amount=data.hold_amount,
                )
            await self.generation_repo.mark_failed(
                session=self.session,
                generation_id=generation_id,
            )

    async def finish_generation(
        self,
        data: GenerationFinishData,
    ) -> GenerationResultResponseDataSchema:
        if data.provider_status != GenerationStatus.COMPLETED:
            await self._rollback_by_finish_data(data=data)
            raise RuntimeError(f"Generation failed with status={data.provider_status}")

        if (
            data.generation_type in (GenerationType.IMAGE, GenerationType.VIDEO)
            and data.result_url is None
        ):
            await self._rollback_by_finish_data(data=data)
            raise RuntimeError("Generation completed without result URL")

        try:
            final_tokens_cost = await self.finalize_generation_billing(
                data=GenerationResultSchema(
                    user_id=data.user_id,
                    generation_id=data.generation_id,
                    hold_amount=data.hold_amount,
                    provider_cost=data.provider_cost,
                    result_url=data.result_url,
                )
            )
        except Exception as e:
            await self._rollback_by_finish_data(data=data)
            raise RuntimeError("Failed to finalize generation billing") from e

        return GenerationResultResponseDataSchema(
            ai_model_id=data.ai_model_id,
            user_id=data.user_id,
            generation_id=data.generation_id,
            tokens_cost=final_tokens_cost,
            text=data.text,
        )

    async def _rollback_by_finish_data(
        self,
        data: GenerationFinishData,
    ) -> None:
        async with self.session.begin():
            if data.hold_amount > 0:
                await self.user_repo.release_tokens(
                    session=self.session,
                    user_id=data.user_id,
                    amount=data.hold_amount,
                )
            await self.generation_repo.mark_failed(
                session=self.session,
                generation_id=data.generation_id,
            )

    async def finalize_generation_billing(
        self,
        data: GenerationResultSchema,
    ) -> float:
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

            if data.hold_amount > 0:
                provider_cost_multiplier = usage_token_price.provider_cost_multiplier
                final_usd_cost = data.provider_cost * provider_cost_multiplier
                final_tokens_cost = final_usd_cost / usage_token_price.usd_per_token

            balance = await self.user_repo.settle_hold_tokens(
                session=self.session,
                user_id=data.user_id,
                hold_amount=data.hold_amount,
                final_charge_amount=final_tokens_cost,
            )
            if not balance:
                raise UserBalanceNotConfiguredError(
                    f"User balance is not configured for user_id={data.user_id}"
                )

            completed_generation = await self.generation_repo.mark_completed(
                session=self.session,
                generation_id=data.generation_id,
                charged_tokens=final_tokens_cost,
                result_url=data.result_url,
            )
            if not completed_generation:
                raise RuntimeError(
                    f"Generation not found for generation_id={data.generation_id}"
                )

        return final_tokens_cost

    async def calculate_tokens_cost_from_provider_cost(
        self,
        provider_cost: float,
    ) -> float:
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

        final_usd_cost = provider_cost * usage_token_price.provider_cost_multiplier
        return final_usd_cost / usage_token_price.usd_per_token