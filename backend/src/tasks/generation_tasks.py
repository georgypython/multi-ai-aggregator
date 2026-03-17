import asyncio
from httpx import AsyncClient

from .broker import broker
from src.core.logger_setup import logger
from src.core.models.db_helper import db_helper
from src.core.models.enums import GenerationStatus
from src.core.schemas.ai import PollWaveSpeedGenerationTaskSchema
from src.repositories import GenerationRepository, TokenPriceRepository, UserRepository
from src.services.generation_billing import GenerationBillingService
from src.services.wavespeed import WaveSpeedService
from src.core.schemas.ai import GenerationFinishData


async def _complete_generation_polling(
    status: GenerationStatus,
    data: PollWaveSpeedGenerationTaskSchema,
) -> None:
    generation_repo = GenerationRepository()
    user_repo = UserRepository()
    token_price_repo = TokenPriceRepository()
    
    async with db_helper.session_factory() as session:
        generation_billing_service = GenerationBillingService(
            session=session,
            user_repo=user_repo,
            generation_repo=generation_repo,
            token_price_repo=token_price_repo,
        )
        if status == GenerationStatus.COMPLETED:
            await generation_billing_service.finish_generation(
                data=GenerationFinishData(
                    provider_status=status,
                    **data.model_dump()
                )
            )
            logger.info(
                "generation_polling_completed generation_id=%s status=%s final_tokens_cost=%s",
                data.generation_id,
                status,
                data.final_tokens_cost,
            )
        else:
            await generation_billing_service.rollback_failed_generation(
                user_id=data.user_id,
                hold_amount=data.hold_amount,
                generation_id=data.generation_id,
            )
            logger.warning(
                "generation_polling_failed generation_id=%s status=%s hold_amount=%s",
                data.generation_id,
                status,
                data.hold_amount,
            )
    return None


async def _continue_generation_polling(
    data: PollWaveSpeedGenerationTaskSchema,
    api_key: str,
    base_url: str,
) -> None:
    await asyncio.sleep(data.poll_interval_seconds)
    data.current_attempt += 1
    await poll_generation_status.kiq(
        data=data,
        api_key=api_key,
        base_url=base_url,
    )
    return None


@broker.task(task_name="generation.poll_wavespeed_status.v1")
async def poll_generation_status(
    data: PollWaveSpeedGenerationTaskSchema,
    api_key: str,
    base_url: str,
) -> None:
    generation = None
    try:
        async with AsyncClient(timeout=data.timeout) as client:
            wavespeed = WaveSpeedService(
                client=client,
                api_key=api_key,
                base_url=base_url,
            )
            generation = await wavespeed.get_generation_status(task_id=data.wavespeed_task_id)
    except Exception as exc:
        logger.exception(
            "poll_generation_status_error generation_id=%s task_id=%s attempt=%s error=%s",
            data.generation_id,
            data.wavespeed_task_id,
            data.current_attempt,
            exc,
        )

        if data.current_attempt >= data.max_attempts:
            await _complete_generation_polling(status=GenerationStatus.FAILED, data=data)
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
        data.result_url = generation.result_url or data.result_url
        await _complete_generation_polling(status=current_status, data=data)
        return None

    await _continue_generation_polling(
        data=data, api_key=api_key, base_url=base_url
    )
    return None