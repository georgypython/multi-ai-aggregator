import asyncio
from httpx import AsyncClient
from uuid import UUID

from .broker import broker
from src.core.logger_setup import logger
from src.core.models.db_helper import db_helper
from src.core.models.enums import GenerationStatus
from src.core.schemas.ai import PollWaveSpeedGenerationTaskSchema
from src.repositories import GenerationRepository
from src.services.wavespeed import WaveSpeedService


async def _update_generation_status(
    generation_id: UUID,
    status: GenerationStatus,
    result_url: str,
    final_token_cost: float,
) -> None:
    generation_repo = GenerationRepository()
    async with db_helper.session_factory() as session:
        if status == GenerationStatus.COMPLETED:
            await generation_repo.mark_completed(
                session=session,
                generation_id=generation_id,
                charged_tokens=final_token_cost,
                result_url=result_url,
            )
        else:
            await generation_repo.mark_failed(
                session=session,
                generation_id=generation_id,
            )
        await session.commit()


@broker.task(task_name="generation.poll_wavespeed_status.v1")
async def poll_generation_status(
    data: PollWaveSpeedGenerationTaskSchema,
    api_key: str,
    base_url: str,
):
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
            "poll_generation_status_error generation_id=%s task_id=%s attempt=%s",
            data.generation_id,
            data.wavespeed_task_id,
            data.current_attempt,
        )

        if data.current_attempt >= data.max_attempts:
            await _update_generation_status(
                generation_id=data.generation_id,
                status=GenerationStatus.FAILED,
                result_url=data.result_url,
                final_token_cost=data.final_tokens_cost,
            )
            return

        await asyncio.sleep(data.poll_interval_seconds)
        data.current_attempt += 1
        await poll_generation_status.kiq(
            data=data,
            api_key=api_key,
            base_url=base_url,
        )
        return

    current_status = GenerationStatus.PROCESSING
    if generation.status == GenerationStatus.COMPLETED:
        current_status = GenerationStatus.COMPLETED
    elif generation.status in (GenerationStatus.FAILED, GenerationStatus.CANCELED):
        current_status = GenerationStatus.FAILED

    if data.current_attempt >= data.max_attempts:
        current_status = GenerationStatus.FAILED

    if current_status != GenerationStatus.PROCESSING:
        await _update_generation_status(
            generation_id=data.generation_id,
            status=current_status,
            result_url=generation.result_url,
            final_token_cost=data.final_tokens_cost
        )
        return
    
    await asyncio.sleep(data.poll_interval_seconds)

    data.current_attempt += 1
    await poll_generation_status.kiq(
        data=data,
        api_key=api_key,
        base_url=base_url,
    )