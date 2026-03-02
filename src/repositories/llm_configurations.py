from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from src.core.models import LLMConfiguration
from src.core.models.enums import LLMConfigurationType

from .abstract_repo import AbstractRepository


class LLMConfigurationRepository(AbstractRepository[LLMConfiguration]):
    model = LLMConfiguration

    def add_user_config(
        self,
        session: AsyncSession,
        *,
        user_id: UUID,
        data: dict,
    ) -> LLMConfiguration:
        llm_config = LLMConfiguration(
            user_id=user_id,
            configuration_type=LLMConfigurationType.USER,
            **data,
        )
        session.add(llm_config)
        return llm_config
