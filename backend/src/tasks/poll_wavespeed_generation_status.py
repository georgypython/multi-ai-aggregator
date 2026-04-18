import asyncio
from httpx import AsyncClient

from .broker import broker
from src.core.config import settings
from src.core.logger_setup import logger
from src.models.db_helper import db_helper
from src.models.enums import GenerationStatus, GenerationType
from src.schemas import PollWaveSpeedGenerationTaskSchema
from src.services.generation_billing import GenerationBillingService
from src.services.wavespeed import WaveSpeedService
from src.schemas import GenerationFinishData
from .utils import delivery_generation_result


async def _complete_generation_polling(
    status: GenerationStatus,
    data: PollWaveSpeedGenerationTaskSchema,
    wavespeed: WaveSpeedService,
    result_url: str,
) -> None:
    async with db_helper.session_factory() as session:
        generation_billing_service = GenerationBillingService(
            session=session,
            token_scale=settings.billing.token_scale_decimal,
        )
        try:
            await generation_billing_service.finish_generation(
                data=GenerationFinishData(provider_status=status, **data.model_dump())
            )
            logger.info(
                "generation_polling_completed generation_id=%s status=%s final_tokens_cost=%s",
                data.generation_id,
                status,
                data.final_tokens_cost,
            )
        except RuntimeError as e:
            logger.warning(
                "generation_polling_failed generation_id=%s status=%s hold_amount=%s error_text=%s",
                data.generation_id,
                status,
                data.hold_amount,
                e,
            )
        await delivery_generation_result(
            status=status,
            result_url=result_url,
            wavespeed=wavespeed,
            user_telegram_id=data.user_tg_id,
            generation_id=data.generation_id,
            generation_type=data.generation_type,
        )
    return None


async def _continue_generation_polling(
    data: PollWaveSpeedGenerationTaskSchema,
    api_key: str,
    base_url: str,
) -> None:
    await asyncio.sleep(data.poll_interval_seconds)
    data.current_attempt += 1
    await poll_wavespeed_generation_status.kiq(
        data=data,
        api_key=api_key,
        base_url=base_url,
    )
    return None


@broker.task(task_name="generation.poll_wavespeed_status.v1")
async def poll_wavespeed_generation_status(
    data: PollWaveSpeedGenerationTaskSchema,
    api_key: str,
    base_url: str,
) -> None:
    generation = None
    async with AsyncClient(timeout=data.timeout) as client:
        wavespeed = WaveSpeedService(
            client=client,
            api_key=api_key,
            base_url=base_url,
            webhook_url=settings.wavespeed.wavespeed_webhook_url,
        )
        try:
            generation = await wavespeed.get_generation_status(
                task_id=data.wavespeed_task_id
            )
            if not generation:
                logger.error(
                    "poll_db_generation_not_found generation_id=%s",
                    data.generation_id,
                )
                return None

            data.result_url = generation.result_url

        except Exception as exc:
            logger.exception(
                "poll_generation_status_error generation_id=%s task_id=%s attempt=%s error=%s",
                data.generation_id,
                data.wavespeed_task_id,
                data.current_attempt,
                exc,
            )
            if data.current_attempt >= data.max_attempts:
                await _complete_generation_polling(
                    status=GenerationStatus.FAILED,
                    data=data,
                    wavespeed=wavespeed,
                    result_url=data.result_url,
                )
                return None

            await _continue_generation_polling(
                data=data, api_key=api_key, base_url=base_url
            )
            return None

        current_status = GenerationStatus.PROCESSING
        if generation.status == GenerationStatus.COMPLETED:
            current_status = GenerationStatus.COMPLETED
        elif generation.status in (GenerationStatus.FAILED, GenerationStatus.CANCELED):
            current_status = GenerationStatus.FAILED

        if data.current_attempt >= data.max_attempts:
            current_status = GenerationStatus.FAILED

        if current_status != GenerationStatus.PROCESSING:
            await _complete_generation_polling(
                status=current_status,
                data=data,
                result_url=data.result_url,
                wavespeed=wavespeed,
            )
            return None

        await _continue_generation_polling(
            data=data, api_key=api_key, base_url=base_url
        )
        return None
