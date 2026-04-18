from datetime import datetime, timedelta, timezone
from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.exceptions.payment import PaymentConflictError, PaymentNotFoundError
from src.models import (
    BalanceTransaction,
    Order,
    PaymentIntent,
    PaymentTransaction,
    Plan,
    Subscription,
    UserBalance,
)
from src.models.enums import (
    BalanceTransactionType,
    OrderStatus,
    PaymentIntentStatus,
    ProductPaymentType,
    SubscriptionStatus,
    TransactionStatus,
    TransactionType,
)


class PaymentLifecycleService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def _get_payment_intent_with_order_plan(
        self,
        payment_intent_id: UUID,
    ) -> PaymentIntent | None:
        stmt = (
            select(PaymentIntent)
            .options(selectinload(PaymentIntent.order).selectinload(Order.plan))
            .where(PaymentIntent.id == payment_intent_id)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def _get_or_create_user_balance_for_update(
        self, user_id: UUID
    ) -> UserBalance:
        stmt = (
            select(UserBalance).where(UserBalance.user_id == user_id).with_for_update()
        )
        result = await self.session.execute(stmt)
        balance = result.scalar_one_or_none()
        if balance:
            return balance

        balance = UserBalance(
            user_id=user_id,
            available_tokens=Decimal("0"),
            hold_tokens=Decimal("0"),
        )
        self.session.add(balance)
        await self.session.flush()
        return balance

    async def _credit_tokens(
        self,
        *,
        user_id: UUID,
        plan: Plan,
        payment_transaction_id: UUID,
        reason: str,
        meta_data: dict,
    ) -> None:
        balance = await self._get_or_create_user_balance_for_update(user_id)
        balance.available_tokens += Decimal(plan.tokens_amount)

        ledger = BalanceTransaction(
            user_id=user_id,
            payment_transaction_id=payment_transaction_id,
            plan_id=plan.id,
            type=BalanceTransactionType.CREDIT,
            amount_tokens=Decimal(plan.tokens_amount),
            reason=reason,
            meta_data=meta_data,
        )
        self.session.add(ledger)
        await self.session.flush()

    async def _get_active_subscription_for_update(
        self,
        user_id: UUID,
    ) -> Subscription | None:
        stmt = (
            select(Subscription)
            .where(
                Subscription.user_id == user_id,
                Subscription.status == SubscriptionStatus.ACTIVE,
            )
            .order_by(Subscription.current_period_end.desc())
            .with_for_update()
        )
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def _create_subscription(
        self,
        *,
        user_id: UUID,
        plan: Plan,
        payment_type: ProductPaymentType,
    ) -> Subscription:
        now = datetime.now(timezone.utc)
        subscription = Subscription(
            user_id=user_id,
            plan_id=plan.id,
            payment_type=payment_type,
            status=SubscriptionStatus.ACTIVE,
            current_period_start=now,
            current_period_end=now + timedelta(days=plan.duration_days),
            payment_count=1,
            last_payment_at=now,
            cancel_at_period_end=False,
        )
        self.session.add(subscription)
        await self.session.flush()
        return subscription

    async def _extend_subscription(
        self,
        *,
        subscription: Subscription,
        plan: Plan,
    ) -> Subscription:
        now = datetime.now(timezone.utc)
        base_start = subscription.current_period_end
        if base_start < now:
            base_start = now

        subscription.status = SubscriptionStatus.ACTIVE
        subscription.current_period_start = base_start
        subscription.current_period_end = base_start + timedelta(
            days=plan.duration_days
        )
        subscription.payment_count += 1
        subscription.last_payment_at = now
        subscription.cancel_at_period_end = False
        subscription.cancelled_at = None
        subscription.cancellation_reason = None
        await self.session.flush()
        return subscription

    async def find_payment_intent_for_webhook(
        self,
        *,
        provider_invoice_id: str | None = None,
        provider_contract_id: str | None = None,
    ) -> PaymentIntent | None:
        if provider_invoice_id:
            stmt = select(PaymentIntent).where(
                PaymentIntent.provider_invoice_id == provider_invoice_id
            )
            result = await self.session.execute(stmt)
            intent = result.scalar_one_or_none()
            if intent:
                return intent

        if provider_contract_id:
            stmt = select(PaymentIntent).where(
                PaymentIntent.provider_contract_id == provider_contract_id
            )
            result = await self.session.execute(stmt)
            intent = result.scalar_one_or_none()
            if intent:
                return intent

        return None

    async def find_payment_intent_by_email(self, *, email: str) -> PaymentIntent | None:
        stmt = (
            select(PaymentIntent)
            .where(PaymentIntent.provider_data["buyer_email"].astext == email)
            .order_by(PaymentIntent.created_at.desc())
        )
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def handle_payment_success(
        self,
        *,
        payment_intent: PaymentIntent,
        provider_transaction_id: str,
        provider_contract_id: str | None,
        amount: Decimal | None,
        provider_data: dict,
    ) -> tuple[PaymentTransaction, Subscription]:
        intent = await self._get_payment_intent_with_order_plan(payment_intent.id)
        if not intent or not intent.order or not intent.order.plan:
            raise PaymentNotFoundError("Payment intent/order/plan not found")

        order = intent.order
        plan = order.plan

        if provider_contract_id and not intent.provider_contract_id:
            intent.provider_contract_id = provider_contract_id

        intent.status = PaymentIntentStatus.COMPLETED
        intent.provider_data = {**(intent.provider_data or {}), **provider_data}

        if order.status == OrderStatus.PENDING:
            order.status = OrderStatus.PAID
            order.paid_at = datetime.now(timezone.utc)

        existing_subscription = await self._get_active_subscription_for_update(
            order.user_id
        )
        if existing_subscription:
            subscription = await self._extend_subscription(
                subscription=existing_subscription,
                plan=plan,
            )
            tx_type = TransactionType.RENEWAL
        else:
            subscription = await self._create_subscription(
                user_id=order.user_id,
                plan=plan,
                payment_type=order.payment_type,
            )
            tx_type = TransactionType.PAYMENT

        tx = PaymentTransaction(
            user_id=order.user_id,
            payment_intent_id=intent.id,
            subscription_id=subscription.id,
            type=tx_type,
            amount=amount or order.amount,
            currency=order.currency,
            status=TransactionStatus.SUCCESS,
            provider_transaction_id=provider_transaction_id,
            provider_data=provider_data or {},
        )
        self.session.add(tx)
        await self.session.flush()

        await self._credit_tokens(
            user_id=order.user_id,
            plan=plan,
            payment_transaction_id=tx.id,
            reason="subscription_payment_success",
            meta_data={
                "provider": intent.provider.value,
                "provider_transaction_id": provider_transaction_id,
                "subscription_id": str(subscription.id),
            },
        )

        return tx, subscription

    async def handle_recurrent_payment_success(
        self,
        *,
        payment_intent: PaymentIntent,
        provider_transaction_id: str,
        parent_contract_id: str | None,
        amount: Decimal | None,
        provider_data: dict,
    ) -> tuple[PaymentTransaction, Subscription]:
        existing_tx_stmt = select(PaymentTransaction).where(
            PaymentTransaction.provider_transaction_id == provider_transaction_id
        )
        existing_tx_result = await self.session.execute(existing_tx_stmt)
        existing_tx = existing_tx_result.scalar_one_or_none()
        if existing_tx:
            sub = await self.session.get(Subscription, existing_tx.subscription_id)
            if not sub:
                raise PaymentConflictError(
                    "Duplicate recurrent tx without subscription"
                )
            return existing_tx, sub

        intent = await self._get_payment_intent_with_order_plan(payment_intent.id)
        if not intent or not intent.order or not intent.order.plan:
            raise PaymentNotFoundError("Payment intent/order/plan not found")

        order = intent.order
        plan = order.plan

        if parent_contract_id and not intent.provider_contract_id:
            intent.provider_contract_id = parent_contract_id

        intent.status = PaymentIntentStatus.COMPLETED
        intent.provider_data = {**(intent.provider_data or {}), **provider_data}

        active_subscription = await self._get_active_subscription_for_update(
            order.user_id
        )
        if active_subscription:
            subscription = await self._extend_subscription(
                subscription=active_subscription,
                plan=plan,
            )
        else:
            subscription = await self._create_subscription(
                user_id=order.user_id,
                plan=plan,
                payment_type=ProductPaymentType.RECURRING,
            )

        tx = PaymentTransaction(
            user_id=order.user_id,
            payment_intent_id=intent.id,
            subscription_id=subscription.id,
            type=TransactionType.RENEWAL,
            amount=amount or order.amount,
            currency=order.currency,
            status=TransactionStatus.SUCCESS,
            provider_transaction_id=provider_transaction_id,
            provider_data=provider_data or {},
        )
        self.session.add(tx)
        await self.session.flush()

        await self._credit_tokens(
            user_id=order.user_id,
            plan=plan,
            payment_transaction_id=tx.id,
            reason="subscription_recurrent_success",
            meta_data={
                "provider": intent.provider.value,
                "provider_transaction_id": provider_transaction_id,
                "subscription_id": str(subscription.id),
            },
        )

        return tx, subscription

    async def handle_payment_failed(
        self,
        *,
        payment_intent: PaymentIntent,
        provider_transaction_id: str,
        error_message: str | None,
        provider_data: dict,
    ) -> PaymentTransaction:
        intent = await self._get_payment_intent_with_order_plan(payment_intent.id)
        if not intent or not intent.order:
            raise PaymentNotFoundError("Payment intent/order not found")

        order = intent.order
        intent.status = PaymentIntentStatus.FAILED
        intent.provider_data = {**(intent.provider_data or {}), **provider_data}

        tx = PaymentTransaction(
            user_id=order.user_id,
            payment_intent_id=intent.id,
            subscription_id=None,
            type=TransactionType.PAYMENT,
            amount=order.amount,
            currency=order.currency,
            status=TransactionStatus.FAILED,
            provider_transaction_id=provider_transaction_id,
            provider_data=provider_data or {},
            error_message=error_message,
        )
        self.session.add(tx)
        await self.session.flush()
        return tx

    async def handle_subscription_cancelled(
        self,
        *,
        payment_intent: PaymentIntent,
        cancelled_at: datetime | None,
        will_expire_at: datetime | None,
        provider_data: dict,
    ) -> Subscription | None:
        intent_stmt = (
            select(PaymentIntent)
            .options(selectinload(PaymentIntent.order))
            .where(PaymentIntent.id == payment_intent.id)
        )
        intent_result = await self.session.execute(intent_stmt)
        intent = intent_result.scalar_one_or_none()
        if not intent or not intent.order:
            return None

        intent.provider_data = {**(intent.provider_data or {}), **provider_data}

        subscription = await self._get_active_subscription_for_update(
            intent.order.user_id
        )
        if not subscription:
            return None

        subscription.cancel_at_period_end = True
        subscription.cancelled_at = cancelled_at or datetime.now(timezone.utc)
        subscription.cancellation_reason = "lavatop_subscription_cancelled"
        if will_expire_at:
            subscription.current_period_end = will_expire_at
        await self.session.flush()
        return subscription
