import asyncio

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from aiogram import Bot

from .broker import broker
from src.core.logger_setup import logger
from src.core.config import settings
from src.models.db_helper import db_helper
from src.models import AIGeneration
from src.schemas.generations import (
    PollWaveSpeedGenerationTaskSchema,
    PollDbGenerationTaskSchema,
    GenerationFinishData,
)
from src.models.enums import GenerationStatus, GenerationType
from src.services import (
    GenerationBillingService,
    WaveSpeedService,
)
from .utils import delivery_generation_result
from src.tasks.poll_wavespeed_generation_status import poll_wavespeed_generation_status


async def _complete_generation_polling(
    generation: AIGeneration,
    data: PollWaveSpeedGenerationTaskSchema,
    generation_billing_service: GenerationBillingService,
    api_key: str,
    base_url: str,
) -> None:
    current_status = generation.status
    try:
        await generation_billing_service.finish_generation(
            data=GenerationFinishData(
                provider_status=current_status, **data.model_dump()
            )
        )
        logger.info(
            "generation_polling_completed generation_id=%s status=%s final_tokens_cost=%s",
            data.generation_id,
            current_status,
            data.final_tokens_cost,
        )
    except RuntimeError as e:
        logger.warning(
            "generation_polling_failed generation_id=%s status=%s hold_amount=%s error_text=%s",
            data.generation_id,
            current_status,
            data.hold_amount,
            e,
        )
    if not generation.result_url:
        logger.warning(
            "poll_db_generation_missing_result_url generation_id=%s status=%s",
            data.generation_id,
            current_status,
        )
        return None
    async with AsyncClient(timeout=data.timeout) as client:
        wavespeed = WaveSpeedService(
            client=client,
            api_key=api_key,
            base_url=base_url,
        )
        await delivery_generation_result(
            status=current_status,
            generation_type=generation.generation_type,
            generation_id=generation.id,
            result_url=generation.result_url,
            user_telegram_id=data.user_tg_id,
            wavespeed=wavespeed,
        )
    return None


async def _continue_generation_polling(
    data: PollDbGenerationTaskSchema,
    api_key: str,
    base_url: str,
    generation_task_id: str,
) -> None:
    await asyncio.sleep(data.poll_interval_seconds)
    if data.current_attempt >= data.max_attempts and generation_task_id is not None:
        await poll_wavespeed_generation_status.kiq(
            data=PollWaveSpeedGenerationTaskSchema(
                **data.model_dump(), wavespeed_task_id=generation_task_id, timeout=30
            ),
            api_key=api_key,
            base_url=base_url,
        )
    else:
        data.current_attempt += 1
        await poll_db_generation_status.kiq(
            data=data,
            api_key=api_key,
            base_url=base_url,
        )
    return None


@broker.task("generation.poll_db_status.v1")
async def poll_db_generation_status(
    data: PollDbGenerationTaskSchema,
    api_key: str,
    base_url: str,
):
    async with db_helper.session_factory() as session:
        stmt = select(AIGeneration).where(AIGeneration.id == data.generation_id)
        res = await session.execute(stmt)
        generation = res.scalar_one_or_none()
        if (
            not generation
            or not generation.task_id
            or not generation.result_url
            or generation.generation_type == GenerationType.LLM
        ):
            logger.error(
                "poll db generation failed for generation_id=%s",
                data.generation_id,
            )
            return None

        generation_billing_service = GenerationBillingService(
            session=session,
            token_scale=settings.billing.token_scale_decimal,
        )

        current_status = generation.status
        if current_status in (GenerationStatus.COMPLETED, GenerationStatus.FAILED):
            await _complete_generation_polling(
                generation=generation,
                data=data,
                generation_billing_service=generation_billing_service,
                api_key=api_key,
                base_url=base_url,
            )
            return None
        else:
            logger.warning(
                "poll_db_generation_not_final generation_id=%s status=%s",
                data.generation_id,
                current_status,
            )
            await _continue_generation_polling(
                data=data,
                api_key=api_key,
                base_url=base_url,
                generation_task_id=generation.task_id,
            )
            return None
