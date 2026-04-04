from uuid import UUID
from decimal import Decimal, ROUND_CEILING
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.exceptions.generation import (
    InsufficientBalanceError,
    UserBalanceNotConfiguredError,
)
from src.models import AIGeneration, TokenPrice, UserBalance
from src.models.enums import GenerationStatus, GenerationType
from src.schemas import (
    GenerationRequestSchema,
    GenerationFinishData,
    GenerationResultResponseDataSchema,
)


class GenerationBillingService:
    def __init__(
        self,
        session: AsyncSession,
        token_scale: Decimal,
    ) -> None:
        self.session = session
        self._token_scale = token_scale

    async def _get_balance_for_update(self, *, user_id: UUID) -> UserBalance | None:
        stmt = (
            select(UserBalance).where(UserBalance.user_id == user_id).with_for_update()
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def _freeze_tokens(
        self, *, user_id: UUID, amount: Decimal
    ) -> UserBalance | None:
        if amount <= 0:
            raise ValueError("amount must be greater than 0")

        balance = await self._get_balance_for_update(user_id=user_id)
        if not balance:
            return None

        if balance.available_tokens < amount:
            raise InsufficientBalanceError(
                "amount must be less than or equal to available_tokens"
            )

        balance.available_tokens -= amount
        balance.hold_tokens += amount
        await self.session.flush()
        return balance

    async def _release_tokens(
        self, *, user_id: UUID, amount: Decimal
    ) -> UserBalance | None:
        if amount <= 0:
            raise ValueError("amount must be greater than 0")

        balance = await self._get_balance_for_update(user_id=user_id)
        if not balance:
            return None

        release_amount = min(balance.hold_tokens, amount)
        balance.hold_tokens -= release_amount
        balance.available_tokens += release_amount
        await self.session.flush()
        return balance

    async def _settle_hold_tokens(
        self,
        *,
        user_id: UUID,
        hold_amount: Decimal,
        final_charge_amount: Decimal,
    ) -> UserBalance | None:
        if hold_amount < 0:
            raise ValueError("hold_amount must be greater or equal to 0")
        if final_charge_amount < 0:
            raise ValueError("final_charge_amount must be greater or equal to 0")

        balance = await self._get_balance_for_update(user_id=user_id)
        if not balance:
            return None

        actual_hold = min(balance.hold_tokens, hold_amount)
        balance.hold_tokens -= actual_hold
        balance.available_tokens += actual_hold

        if balance.available_tokens < final_charge_amount:
            raise InsufficientBalanceError(
                "insufficient available_tokens for final charge"
            )
        balance.available_tokens -= final_charge_amount
        await self.session.flush()
        return balance

    async def _create_processing_generation(
        self,
        *,
        user_id: UUID,
        ai_model_id: UUID,
        generation_type: GenerationType,
        hold_tokens_amount: Decimal,
    ) -> AIGeneration:
        generation = AIGeneration(
            user_id=user_id,
            ai_model_id=ai_model_id,
            status=GenerationStatus.PROCESSING,
            generation_type=generation_type,
            charged_tokens=Decimal("0"),
            hold_tokens_amount=hold_tokens_amount,
        )
        self.session.add(generation)
        await self.session.flush()
        return generation

    async def _set_generation_task_id(
        self,
        *,
        generation_id: UUID,
        task_id: str,
    ) -> AIGeneration | None:
        generation = await self.session.get(AIGeneration, generation_id)
        if not generation:
            return None
        generation.task_id = task_id
        await self.session.flush()
        return generation

    async def _mark_generation_failed(
        self, *, generation_id: UUID
    ) -> AIGeneration | None:
        generation = await self.session.get(AIGeneration, generation_id)
        if not generation:
            return None
        generation.status = GenerationStatus.FAILED
        await self.session.flush()
        return generation

    async def _mark_generation_completed(
        self,
        *,
        generation_id: UUID,
        charged_tokens: Decimal,
        result_url: str | None = None,
    ) -> AIGeneration | None:
        generation = await self.session.get(AIGeneration, generation_id)
        if not generation:
            return None

        generation.status = GenerationStatus.COMPLETED
        generation.charged_tokens = charged_tokens
        generation.result_url = result_url
        generation.completed_at = datetime.now(timezone.utc)
        await self.session.flush()
        return generation

    async def _count_generations_by_user_and_model(
        self,
        *,
        user_id: UUID,
        ai_model_id: UUID,
        max_count: int | None = None,
    ) -> int:
        base_stmt = select(AIGeneration.id).where(
            AIGeneration.user_id == user_id,
            AIGeneration.ai_model_id == ai_model_id,
            AIGeneration.status.in_(
                (
                    GenerationStatus.PROCESSING,
                    GenerationStatus.COMPLETED,
                    GenerationStatus.FAILED,
                )
            ),
        )
        if max_count is not None and max_count > 0:
            base_stmt = base_stmt.limit(max_count)

        stmt = select(func.count()).select_from(base_stmt.subquery())
        result = await self.session.execute(stmt)
        return int(result.scalar_one() or 0)

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

            balance = await self._get_balance_for_update(user_id=user_id)
            if not balance:
                raise UserBalanceNotConfiguredError(
                    f"User balance is not configured for user_id={user_id}"
                )

            has_free_request = False
            if data.free_requests_limit > 0:
                generation_count = await self._count_generations_by_user_and_model(
                    user_id=user_id,
                    ai_model_id=data.ai_model_id,
                    max_count=data.free_requests_limit,
                )
                has_free_request = generation_count < data.free_requests_limit

            if has_free_request:
                data.hold_amount = Decimal("0")
                return await self._create_processing_generation(
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

                balance = await self._freeze_tokens(
                    user_id=user_id,
                    amount=data.hold_amount,
                )
                if not balance:
                    raise UserBalanceNotConfiguredError(
                        f"User balance is not configured for user_id={user_id}"
                    )
                return await self._create_processing_generation(
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
            generation = await self._set_generation_task_id(
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
                await self._release_tokens(user_id=user_id, amount=hold_amount)
            await self._mark_generation_failed(generation_id=generation_id)

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
                await self._release_tokens(
                    user_id=data.user_id, amount=data.hold_amount
                )
            await self._mark_generation_failed(generation_id=data.generation_id)

    async def _complete_billing_and_calculate_final_cost(
        self,
        data: GenerationFinishData,
    ) -> GenerationResultResponseDataSchema:
        async with self.session.begin():
            final_tokens_cost = data.final_tokens_cost

            balance = await self._settle_hold_tokens(
                user_id=data.user_id,
                hold_amount=data.hold_amount,
                final_charge_amount=final_tokens_cost,
            )
            if not balance:
                raise UserBalanceNotConfiguredError(
                    f"User balance is not configured for user_id={data.user_id}"
                )

            completed_generation = await self._mark_generation_completed(
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
        stmt = select(TokenPrice).where(
            TokenPrice.id == model_token_price_id,
            TokenPrice.is_active.is_(True),
        )
        result = await self.session.execute(stmt)
        token_price = result.scalar_one_or_none()
        if not token_price or not token_price.is_active:
            raise RuntimeError("Active token price not configured")
        if token_price.usd_per_token <= 0:
            raise RuntimeError("usd_per_token must be greater than 0")

        provider_cost_multiplier = token_price.provider_cost_multiplier or Decimal("1")
        final_usd_cost = provider_cost * provider_cost_multiplier
        final_tokens_cost = final_usd_cost / token_price.usd_per_token
        return self._round_tokens_up(final_tokens_cost)

    async def calculate_hold_tokens_cost_from_providers_cost(
        self,
        provider_cost: Decimal,
        model_token_price_id: UUID,
    ) -> Decimal:
        return await self._calculate_tokens_cost_from_providers_cost(
            provider_cost=provider_cost,
            model_token_price_id=model_token_price_id,
        )

    async def calculate_final_tokens_cost(
        self,
        provider_cost: Decimal,
        model_token_price_id: UUID,
        hold_amount: Decimal,
    ) -> Decimal:
        if hold_amount > 0:
            return await self._calculate_tokens_cost_from_providers_cost(
                provider_cost=provider_cost,
                model_token_price_id=model_token_price_id,
            )

        return hold_amount
