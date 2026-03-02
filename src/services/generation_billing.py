from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from src.core.exceptions.llm import (
    InsufficientBalanceError,
    UserBalanceNotConfiguredError,
)
from src.core.models import AIGeneration
from src.core.models.enums import PriceType
from src.core.schemas.ai import GenerationRequestSchema, GenerationResultSchema
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
        
    async def rollback_failed_generation(
        self,
        data: GenerationRequestSchema,
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
            )
            if not completed_generation:
                raise RuntimeError(
                    f"Generation not found for generation_id={data.generation_id}"
                )

        return final_tokens_cost