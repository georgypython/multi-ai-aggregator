from uuid import UUID
from decimal import Decimal, ROUND_CEILING

from sqlalchemy.ext.asyncio import AsyncSession

from src.exceptions.generation import (
    InsufficientBalanceError,
    UserBalanceNotConfiguredError,
)
from src.models import AIGeneration
from src.models.enums import GenerationStatus, GenerationType
from src.schemas import (
    GenerationRequestSchema,
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
        token_scale: Decimal,
    ) -> None:
        self.session = session
        self.user_repo = user_repo
        self.generation_repo = generation_repo
        self.token_price_repo = token_price_repo
        self._token_scale = token_scale

    def _round_tokens_up(self, tokens_cost: Decimal) -> Decimal:
        return tokens_cost.quantize(
            self._token_scale,
            rounding=ROUND_CEILING,
        )

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
                data.hold_amount = Decimal("0")
                return await self.generation_repo.create_processing(
                    session=self.session,
                    user_id=user_id,
                    ai_model_id=data.ai_model_id,
                    generation_type=data.generation_type,
                    hold_tokens_amount=data.hold_amount,
                )

            else:
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
                    hold_tokens_amount=data.hold_amount,
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
        user_id: UUID,
        hold_amount: Decimal,
        generation_id: UUID,
    ) -> None:
        async with self.session.begin():
            if hold_amount > 0:
                await self.user_repo.release_tokens(
                    session=self.session,
                    user_id=user_id,
                    amount=hold_amount,
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
            return await self._complete_billing_and_calculate_final_cost(data=data)
        except Exception as e:
            await self._rollback_by_finish_data(data=data)
            raise RuntimeError("Failed to finalize generation billing") from e

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

    async def _complete_billing_and_calculate_final_cost(
        self,
        data: GenerationFinishData,
    ) -> GenerationResultResponseDataSchema:
        async with self.session.begin():
            final_tokens_cost = await self.calculate_final_tokens_cost(
                hold_amount=data.hold_amount,
                model_token_price_id=data.model_token_price_id,
                provider_cost=data.provider_cost,
            )

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

        return GenerationResultResponseDataSchema(
            ai_model_id=data.ai_model_id,
            user_id=data.user_id,
            generation_id=data.generation_id,
            tokens_cost=final_tokens_cost,
            status=completed_generation.status,
            is_free_request=data.hold_amount == 0,
            text=data.text,
        )

    async def _calculate_tokens_cost_from_providers_cost(
        self,
        provider_cost: Decimal,
        model_token_price_id: UUID,
    ) -> Decimal:
        token_price = await self.token_price_repo.get_one(
            session=self.session,
            id=model_token_price_id,
            is_active=True,
        )
        if not token_price:
            raise RuntimeError("Active token price not configured")
        if token_price.usd_per_token <= 0:
            raise RuntimeError("usd_per_token must be greater than 0")

        provider_cost_multiplier = token_price.provider_cost_multiplier or Decimal("1")
        final_usd_cost = provider_cost * provider_cost_multiplier
        return final_usd_cost / token_price.usd_per_token

    async def calculate_hold_tokens_cost_from_providers_cost(
        self,
        provider_cost: Decimal,
        model_token_price_id: UUID,
        min_hold_amount: Decimal,
    ) -> Decimal:
        expected_tokens_cost = await self._calculate_tokens_cost_from_providers_cost(
            provider_cost=provider_cost,
            model_token_price_id=model_token_price_id,
        )
        rounded_expected_tokens_cost = self._round_tokens_up(expected_tokens_cost)
        return max(min_hold_amount, rounded_expected_tokens_cost)

    async def calculate_final_tokens_cost(
        self,
        provider_cost: Decimal,
        model_token_price_id: UUID,
        hold_amount: Decimal,
    ) -> Decimal:
        if hold_amount > 0:
            final_tokens_cost = await self._calculate_tokens_cost_from_providers_cost(
                provider_cost=provider_cost,
                model_token_price_id=model_token_price_id,
            )
            return self._round_tokens_up(final_tokens_cost)

        return hold_amount
