from decimal import Decimal

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.logger_setup import logger
from src.schemas.lava_top_api import LavaTopWebhookRequestData
from src.services.payment_lifecycle import PaymentLifecycleService


class PaymentWebhookService:
    def __init__(
        self,
        session: AsyncSession,
        payment_lifecycle_service: PaymentLifecycleService,
    ) -> None:
        self.session = session
        self.payment_lifecycle_service = payment_lifecycle_service

    @staticmethod
    def _build_provider_data(payload: LavaTopWebhookRequestData) -> dict:
        return {
            "event_type": payload.eventType.value,
            "contract_id": payload.contractId,
            "parent_contract_id": payload.parentContractId,
            "buyer_email": payload.buyer.email,
            "amount": str(payload.amount) if payload.amount is not None else None,
            "currency": payload.currency.value if payload.currency else None,
            "status": payload.status.value if payload.status else None,
            "timestamp": payload.timestamp.isoformat() if payload.timestamp else None,
            "error_message": payload.errorMessage,
            "cancelled_at": (
                payload.cancelledAt.isoformat() if payload.cancelledAt else None
            ),
            "will_expire_at": (
                payload.willExpireAt.isoformat() if payload.willExpireAt else None
            ),
        }

    async def process_lava_top_regular_webhook(
        self,
        payload: LavaTopWebhookRequestData,
    ) -> dict:
        try:
            async with self.session.begin():
                if payload.is_cancellation():
                    return await self._process_subscription_cancelled(payload)

                if not payload.contractId:
                    logger.error("LavaTop regular webhook: missing contractId")
                    return {"status": "ignored", "reason": "missing_contract_id"}

                payment_intent = await self.payment_lifecycle_service.find_payment_intent_for_webhook(
                    provider_invoice_id=str(payload.contractId),
                    provider_contract_id=None,
                )
                if not payment_intent:
                    logger.warning(
                        "PaymentIntent not found for regular webhook contract=%s",
                        payload.contractId,
                    )
                    return {"status": "ignored", "reason": "payment_intent_not_found"}

                provider_data = self._build_provider_data(payload)

                if payload.is_successful():
                    tx, sub = (
                        await self.payment_lifecycle_service.handle_payment_success(
                            payment_intent=payment_intent,
                            provider_transaction_id=str(payload.contractId),
                            provider_contract_id=str(payload.contractId),
                            amount=(
                                Decimal(str(payload.amount))
                                if payload.amount is not None
                                else None
                            ),
                            provider_data=provider_data,
                        )
                    )
                    return {
                        "status": "ok",
                        "transaction_id": str(tx.id),
                        "subscription_id": str(sub.id),
                    }

                if payload.is_failed():
                    tx = await self.payment_lifecycle_service.handle_payment_failed(
                        payment_intent=payment_intent,
                        provider_transaction_id=str(payload.contractId),
                        error_message=payload.errorMessage,
                        provider_data=provider_data,
                    )
                    return {"status": "failed", "transaction_id": str(tx.id)}
        except IntegrityError:
            return {"status": "ok", "duplicate": True}

        return {"status": "ignored", "reason": "unsupported_event"}

    async def process_lava_top_recurrent_webhook(
        self,
        payload: LavaTopWebhookRequestData,
    ) -> dict:
        try:
            async with self.session.begin():
                if not payload.contractId:
                    logger.error("LavaTop recurrent webhook: missing contractId")
                    return {"status": "ignored", "reason": "missing_contract_id"}

                payment_intent = await self.payment_lifecycle_service.find_payment_intent_for_webhook(
                    provider_invoice_id=None,
                    provider_contract_id=(
                        str(payload.parentContractId)
                        if payload.parentContractId
                        else None
                    ),
                )

                if not payment_intent and payload.buyer and payload.buyer.email:
                    payment_intent = await self.payment_lifecycle_service.find_payment_intent_by_email(
                        email=payload.buyer.email
                    )

                if not payment_intent:
                    logger.warning(
                        "PaymentIntent not found for recurrent webhook parent=%s email=%s",
                        payload.parentContractId,
                        payload.buyer.email if payload.buyer else None,
                    )
                    return {"status": "ignored", "reason": "payment_intent_not_found"}

                provider_data = self._build_provider_data(payload)

                if payload.is_successful():
                    tx, sub = (
                        await self.payment_lifecycle_service.handle_recurrent_payment_success(
                            payment_intent=payment_intent,
                            provider_transaction_id=str(payload.contractId),
                            parent_contract_id=(
                                str(payload.parentContractId)
                                if payload.parentContractId
                                else None
                            ),
                            amount=(
                                Decimal(str(payload.amount))
                                if payload.amount is not None
                                else None
                            ),
                            provider_data=provider_data,
                        )
                    )
                    return {
                        "status": "ok",
                        "transaction_id": str(tx.id),
                        "subscription_id": str(sub.id),
                    }

                if payload.is_failed():
                    tx = await self.payment_lifecycle_service.handle_payment_failed(
                        payment_intent=payment_intent,
                        provider_transaction_id=str(payload.contractId),
                        error_message=payload.errorMessage,
                        provider_data=provider_data,
                    )
                    return {"status": "failed", "transaction_id": str(tx.id)}
        except IntegrityError:
            return {"status": "ok", "duplicate": True}

        return {"status": "ignored", "reason": "unsupported_event"}

    async def _process_subscription_cancelled(
        self, payload: LavaTopWebhookRequestData
    ) -> dict:
        if not payload.contractId:
            return {"status": "ignored", "reason": "missing_contract_id"}

        payment_intent = (
            await self.payment_lifecycle_service.find_payment_intent_for_webhook(
                provider_invoice_id=None,
                provider_contract_id=str(payload.contractId),
            )
        )
        if not payment_intent and payload.buyer and payload.buyer.email:
            payment_intent = (
                await self.payment_lifecycle_service.find_payment_intent_by_email(
                    email=payload.buyer.email
                )
            )

        if not payment_intent:
            return {"status": "ignored", "reason": "payment_intent_not_found"}

        provider_data = self._build_provider_data(payload)
        sub = await self.payment_lifecycle_service.handle_subscription_cancelled(
            payment_intent=payment_intent,
            cancelled_at=payload.cancelledAt,
            will_expire_at=payload.willExpireAt,
            provider_data=provider_data,
        )
        if not sub:
            return {"status": "ignored", "reason": "subscription_not_found"}
        return {"status": "ok", "subscription_id": str(sub.id)}
