from sqlalchemy.ext.asyncio import AsyncSession

from src.core.logger_setup import logger
from src.models import AIGeneration
from src.models.enums import GenerationStatus
from src.schemas import GenerationFinishData, WavespeedWebhookPayloadSchema
from src.services.db_access import DBAccessService
from src.services.generation_billing import GenerationBillingService


class GenerationWebhookService(DBAccessService):
    def __init__(
        self,
        session: AsyncSession,
        generation_billing_service: GenerationBillingService,
    ) -> None:
        self.session = session
        self.generation_billing_service = generation_billing_service

    async def _complete_webhook_generation(
        self,
        result_url: str | None,
        webhook_generation_status: GenerationStatus,
        generation: AIGeneration,
    ) -> None:
        try:
            await self.generation_billing_service.finish_generation(
                data=GenerationFinishData(
                    ai_model_id=generation.ai_model_id,
                    generation_id=generation.id,
                    user_id=generation.user_id,
                    generation_type=generation.generation_type,
                    hold_amount=generation.hold_tokens_amount,
                    final_tokens_cost=generation.hold_tokens_amount,
                    provider_status=webhook_generation_status,
                    result_url=result_url,
                )
            )
            logger.info(
                "wavespeed_webhook_generation_completed generation_id=%s task_id=%s",
                generation.id,
                generation.task_id,
            )
        except RuntimeError as e:
            logger.warning(
                "wavespeed_webhook_generation_failed generation_id=%s status=%s task_id=%s error_text=%s",
                generation.id,
                webhook_generation_status,
                generation.task_id,
                e,
            )
        return None

    async def handle_wavespeed_webhook(
        self,
        payload: WavespeedWebhookPayloadSchema,
    ) -> None:
        task_id = payload.id
        async with self.session.begin():
            generation = await self.get_one(model=AIGeneration, task_id=task_id)
            if not generation:
                logger.warning(
                    "wavespeed_webhook_generation_not_found task_id=%s", task_id
                )
                return None

            if generation.status != GenerationStatus.PROCESSING:
                logger.info(
                    "wavespeed_webhook_generation_already_finalized generation_id=%s status=%s task_id=%s",
                    generation.id,
                    generation.status,
                    task_id,
                )
                return None

            webhook_generation_status = payload.status
            if webhook_generation_status == GenerationStatus.PROCESSING:
                logger.info(
                    "wavespeed_webhook_generation_ignored generation_id=%s status=%s task_id=%s",
                    generation.id,
                    webhook_generation_status,
                    task_id,
                )
                return None

            result_url = None
            if payload.urls and payload.urls.get:
                result_url = payload.urls.get

        await self._complete_webhook_generation(
            result_url=result_url or generation.result_url,
            webhook_generation_status=webhook_generation_status,
            generation=generation,
        )
        return None
