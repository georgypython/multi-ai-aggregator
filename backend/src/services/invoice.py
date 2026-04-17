from datetime import datetime, timedelta, timezone
from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from src.exceptions.payment import (
    PaymentError,
    PaymentNotFoundError,
    PaymentProcessingError,
    PaymentValidationError,
)
from src.models import (
    Order,
    PaymentIntent,
    Plan,
    PaymentProviderConfig,
    PaymentProviderMethod,
    Product,
    User,
)
from src.models.enums import (
    OrderStatus,
    PaymentCurrency,
    PaymentIntentStatus,
    PaymentMethod,
    PaymentProvider,
    ProductPaymentType,
)
from src.schemas.billing import InvoiceCreateRequestSchema, InvoiceCreateResponseSchema
from src.schemas.billing import PaymentProductItemSchema
from src.services.lava_top import LavaTopService


class PaymentInvoiceService:
    def __init__(
        self,
        session: AsyncSession,
        lava_top_service: LavaTopService,
        order_expire_minutes: int,
    ) -> None:
        self.session = session
        self.lava_top_service = lava_top_service
        self.order_expire_minutes = order_expire_minutes

    async def create_order(
        self,
        *,
        user_id: UUID,
        plan_id: UUID,
        payment_type: ProductPaymentType,
        currency: PaymentCurrency,
        amount: Decimal,
        discount_amount: Decimal = Decimal("0"),
    ) -> Order:
        now = datetime.now(timezone.utc)
        order = Order(
            user_id=user_id,
            plan_id=plan_id,
            payment_type=payment_type,
            amount=amount,
            currency=currency,
            discount_amount=discount_amount,
            status=OrderStatus.PENDING,
            expires_at=now + timedelta(minutes=self.order_expire_minutes),
        )
        self.session.add(order)
        await self.session.flush()
        return order

    async def create_payment_intent(
        self,
        *,
        order_id: UUID,
        provider: PaymentProvider,
        provider_invoice_id: str | None,
        provider_offer_id: str | None,
        invoice_url: str | None,
        provider_data: dict,
    ) -> PaymentIntent:
        payment_intent = PaymentIntent(
            order_id=order_id,
            provider=provider,
            provider_invoice_id=provider_invoice_id,
            provider_offer_id=provider_offer_id,
            status=PaymentIntentStatus.AWAITING_PAYMENT,
            invoice_url=invoice_url,
            provider_data=provider_data,
        )
        self.session.add(payment_intent)
        await self.session.flush()
        return payment_intent

    async def cancel_order(self, order: Order) -> None:
        order.status = OrderStatus.CANCELED
        await self.session.flush()

    @staticmethod
    def ensure_lavatop_provider(provider: PaymentProvider) -> None:
        if provider != PaymentProvider.LAVA_TOP:
            raise PaymentValidationError("Only LAVA_TOP is supported for now")

    @staticmethod
    def _determine_payment_type(payment_method: PaymentMethod) -> ProductPaymentType:
        if payment_method in (PaymentMethod.CARD_RU, PaymentMethod.CARD_INTERNATIONAL):
            return ProductPaymentType.RECURRING
        return ProductPaymentType.ONE_TIME

    @staticmethod
    def _build_buyer_email(user: User) -> str:
        # AI app users currently do not store email, but LavaTop requires one.
        # Keep it stable per user to avoid random identities in provider records.
        return f"tg-{user.telegram_id}@users.ai"

    async def _get_user(self, user_id: UUID) -> User:
        user = await self.session.get(User, user_id)
        if not user or not user.is_active:
            raise PaymentNotFoundError("User not found")
        return user

    async def _get_plan(self, plan_id: UUID) -> Plan:
        stmt = (
            select(Plan)
            .join(Product, Product.id == Plan.product_id)
            .where(Plan.id == plan_id, Plan.is_active.is_(True), Product.is_active.is_(True))
        )
        result = await self.session.execute(stmt)
        plan = result.scalar_one_or_none()
        if not plan:
            raise PaymentNotFoundError("Plan not found")
        return plan

    async def _validate_payment_method(self, payment_method: PaymentMethod) -> None:
        stmt = select(PaymentProviderMethod).where(
            PaymentProviderMethod.method_code == payment_method,
            PaymentProviderMethod.enabled.is_(True),
            PaymentProviderMethod.is_soon.is_(False),
        )
        result = await self.session.execute(stmt)
        method = result.scalar_one_or_none()
        if not method:
            raise PaymentValidationError(
                f"Payment method {payment_method.value} is not available"
            )

    async def list_payment_methods(self) -> list[PaymentProviderMethod]:
        stmt = (
            select(PaymentProviderMethod)
            .join(
                PaymentProviderConfig,
                PaymentProviderMethod.provider_id == PaymentProviderConfig.id,
            )
            .options(selectinload(PaymentProviderMethod.provider))
            .where(PaymentProviderConfig.enabled.is_(True))
            .where(
                (PaymentProviderMethod.enabled.is_(True))
                | (PaymentProviderMethod.is_soon.is_(True))
            )
            .order_by(PaymentProviderMethod.sort_order, PaymentProviderMethod.method_code)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def list_payment_products(self) -> list[PaymentProductItemSchema]:
        stmt = (
            select(Plan, Product)
            .join(Product, Product.id == Plan.product_id)
            .where(Plan.is_active.is_(True), Product.is_active.is_(True))
            .order_by(Plan.price_rub.asc(), Product.name.asc())
        )
        result = await self.session.execute(stmt)

        products: list[PaymentProductItemSchema] = []
        for plan, product in result.all():
            products.append(
                PaymentProductItemSchema(
                    plan_id=plan.id,
                    tariff_code=product.code.value,
                    name=product.name,
                    display_name=plan.display_name,
                    description=plan.description,
                    billing_interval=plan.billing_interval.value,
                    duration_days=plan.duration_days,
                    price_rub=Decimal(plan.price_rub),
                    tokens_amount=Decimal(plan.tokens_amount),
                    is_vpn_bonus_enabled=plan.is_vpn_bonus_enabled,
                )
            )

        return products

    @staticmethod
    def _resolve_lavatop_offer_id(
        plan: Plan,
        payment_type: ProductPaymentType,
    ) -> UUID | None:
        if payment_type == ProductPaymentType.RECURRING:
            return plan.lavatop_recurring_offer_id
        return plan.lavatop_one_time_offer_id

    async def create_invoice(
        self,
        *,
        user_id: UUID,
        payload: InvoiceCreateRequestSchema,
    ) -> InvoiceCreateResponseSchema:
        async with self.session.begin():
            user = await self._get_user(user_id)
            plan = await self._get_plan(payload.plan_id)

            await self._validate_payment_method(payload.payment_method)

            if plan.available_payment_methods and payload.payment_method.name not in plan.available_payment_methods:
                raise PaymentValidationError(
                    f"Payment method {payload.payment_method.value} is not available for this plan"
                )

            payment_type = self._determine_payment_type(payload.payment_method)
            provider = PaymentProvider.LAVA_TOP
            self.ensure_lavatop_provider(provider)

            offer_id = self._resolve_lavatop_offer_id(plan, payment_type)
            if not offer_id:
                raise PaymentValidationError(
                    "This plan is not available for selected payment method"
                )

            amount = Decimal(plan.price_rub)
            currency = PaymentCurrency.RUB

            order = await self.create_order(
                user_id=user.id,
                plan_id=plan.id,
                payment_type=payment_type,
                currency=currency,
                amount=amount,
            )

            try:
                provider_result = await self.lava_top_service.create_invoice(
                    currency=currency,
                    payment_method=payload.payment_method,
                    payment_type=payment_type,
                    periodicity=plan.billing_interval,
                    offer_id=offer_id,
                    email=self._build_buyer_email(user),
                )

                payment_intent = await self.create_payment_intent(
                    order_id=order.id,
                    provider=provider,
                    provider_invoice_id=provider_result["provider_invoice_id"],
                    provider_offer_id=str(offer_id),
                    invoice_url=provider_result["invoice_url"],
                    provider_data=provider_result["provider_data"],
                )
            except PaymentError:
                await self.cancel_order(order)
                raise
            except Exception as exc:
                await self.cancel_order(order)
                raise PaymentProcessingError("Failed to create invoice") from exc

            return InvoiceCreateResponseSchema(
                order_id=order.id,
                payment_intent_id=payment_intent.id,
                payment_url=payment_intent.invoice_url,
                amount=amount,
                currency=currency,
                provider=provider,
                payment_method=payload.payment_method,
            )
