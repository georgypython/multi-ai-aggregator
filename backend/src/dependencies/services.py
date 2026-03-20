from httpx import AsyncClient
from botocore.client import BaseClient
from sqlalchemy.ext.asyncio import AsyncSession

from dishka import Provider, Scope, provide

from src.core.config import settings
from src.core.utils.image_configs import IMAGE_MODEL_CONFIGS
from src.core.utils.video_configs import VIDEO_MODEL_CONFIGS
from src.services.ai_models import AIModelsService
from src.services.generation_billing import GenerationBillingService
from src.services.image_profile import ImageProfileService
from src.services.image_generation import ImageGenerationService
from src.services.llm_configuration import LLMConfigurationService
from src.services.llm_generation import LLMGenerationService
from src.services.openrouter import OpenRouterService
from src.services.storage import StorageService
from src.services.video_profile import VideoProfileService
from src.services.video_generation import VideoGenerationService
from src.services.users import UsersService
from src.services.wavespeed import WaveSpeedService
from src.repositories import (
    AIModelRepository,
    UserRepository,
    LLMProfileRepository,
    LLMConfigurationRepository,
    GenerationRepository,
    MediaFilesRepository,
    ChatMemoryRepository,
    TokenPriceRepository,
    ImagePriceRepository,
    VideoPriceRepository,
)


class ServicesProvider(Provider):
    @provide(scope=Scope.APP)
    def get_image_model_configs(self) -> dict[str, dict]:
        return IMAGE_MODEL_CONFIGS

    @provide(scope=Scope.APP)
    def get_video_model_configs(self) -> dict[str, dict]:
        return VIDEO_MODEL_CONFIGS

    @provide(scope=Scope.APP)
    def get_openrouter_service(
        self,
        client: AsyncClient,
    ) -> OpenRouterService:
        return OpenRouterService(
            client=client,
            api_key=settings.openrouter.api_key,
            base_url=settings.openrouter.base_url,
        )

    @provide(scope=Scope.APP)
    def get_wavespeed_service(
        self,
        client: AsyncClient,
    ) -> WaveSpeedService:
        return WaveSpeedService(
            client=client,
            api_key=settings.wavespeed.api_key,
            base_url=settings.wavespeed.base_url,
        )

    @provide(scope=Scope.REQUEST)
    def get_storage_service(
        self,
        s3_client: BaseClient,
        session: AsyncSession,
        media_files_repo: MediaFilesRepository,
    ) -> StorageService:
        return StorageService(
            client=s3_client,
            session=session,
            media_files_repo=media_files_repo,
            bucket=settings.storage.bucket,
            presigned_ttl_seconds=settings.storage.presigned_ttl_seconds,
            input_retention_hours=settings.storage.input_retention_hours,
            input_prefix=settings.storage.input_prefix,
            max_upload_bytes=settings.storage.max_upload_bytes,
            allowed_image_content_types=settings.storage.allowed_image_content_types,
            image_extensions=settings.storage.image_extensions,
            operation_timeout_seconds=settings.storage.operation_timeout_seconds,
        )

    @provide(scope=Scope.REQUEST)
    def get_generation_billing_service(
        self,
        session: AsyncSession,
        user_repo: UserRepository,
        token_price_repo: TokenPriceRepository,
        generation_repo: GenerationRepository,
    ) -> GenerationBillingService:
        return GenerationBillingService(
            session=session,
            user_repo=user_repo,
            generation_repo=generation_repo,
            token_price_repo=token_price_repo,
        )

    @provide(scope=Scope.REQUEST)
    def get_llm_generation_service(
        self,
        session: AsyncSession,
        llm_client: OpenRouterService,
        user_repo: UserRepository,
        llm_repo: LLMProfileRepository,
        chat_memory_repo: ChatMemoryRepository,
        generation_billing_service: GenerationBillingService,
    ) -> LLMGenerationService:
        return LLMGenerationService(
            session=session,
            llm_client=llm_client,
            user_repo=user_repo,
            llm_repo=llm_repo,
            chat_memory_repo=chat_memory_repo,
            generation_billing_service=generation_billing_service,
        )

    @provide(scope=Scope.REQUEST)
    def get_ai_models_service(
        self,
        session: AsyncSession,
        ai_model_repo: AIModelRepository,
        user_repo: UserRepository,
    ) -> AIModelsService:
        return AIModelsService(
            session=session,
            ai_model_repo=ai_model_repo,
            user_repo=user_repo,
        )

    @provide(scope=Scope.REQUEST)
    def get_users_service(
        self,
        session: AsyncSession,
        user_repo: UserRepository,
    ) -> UsersService:
        return UsersService(
            session=session,
            user_repo=user_repo,
        )

    @provide(scope=Scope.REQUEST)
    def get_image_generation_service(
        self,
        session: AsyncSession,
        user_repo: UserRepository,
        ai_model_repo: AIModelRepository,
        generation_repo: GenerationRepository,
        generation_billing_service: GenerationBillingService,
        image_configuration_service: ImageProfileService,
        wavespeed_service: WaveSpeedService,
        storage_service: StorageService,
    ) -> ImageGenerationService:
        return ImageGenerationService(
            session=session,
            user_repo=user_repo,
            ai_model_repo=ai_model_repo,
            generation_repo=generation_repo,
            generation_billing_service=generation_billing_service,
            image_profile_service=image_configuration_service,
            wavespeed_service=wavespeed_service,
            storage_service=storage_service,
            poll_interval_seconds=settings.wavespeed.poll_interval_seconds,
            poll_max_attempts=settings.wavespeed.poll_max_attempts,
        )

    @provide(scope=Scope.REQUEST)
    def get_video_generation_service(
        self,
        session: AsyncSession,
        user_repo: UserRepository,
        ai_model_repo: AIModelRepository,
        generation_repo: GenerationRepository,
        generation_billing_service: GenerationBillingService,
        video_configuration_service: VideoProfileService,
        wavespeed_service: WaveSpeedService,
    ) -> VideoGenerationService:
        return VideoGenerationService(
            session=session,
            user_repo=user_repo,
            ai_model_repo=ai_model_repo,
            generation_repo=generation_repo,
            generation_billing_service=generation_billing_service,
            video_profile_service=video_configuration_service,
            wavespeed_service=wavespeed_service,
            poll_interval_seconds=settings.wavespeed.poll_interval_seconds,
            poll_max_attempts=settings.wavespeed.poll_max_attempts,
        )

    @provide(scope=Scope.REQUEST)
    def get_image_configuration_service(
        self,
        session: AsyncSession,
        ai_model_repo: AIModelRepository,
        image_price_repo: ImagePriceRepository,
        generation_repo: GenerationRepository,
        generation_billing_service: GenerationBillingService,
    ) -> ImageProfileService:
        return ImageProfileService(
            session=session,
            ai_model_repo=ai_model_repo,
            image_price_repo=image_price_repo,
            generation_repo=generation_repo,
            generation_billing_service=generation_billing_service,
        )

    @provide(scope=Scope.REQUEST)
    def get_video_configuration_service(
        self,
        session: AsyncSession,
        ai_model_repo: AIModelRepository,
        video_price_repo: VideoPriceRepository,
        generation_repo: GenerationRepository,
        generation_billing_service: GenerationBillingService,
    ) -> VideoProfileService:
        return VideoProfileService(
            session=session,
            ai_model_repo=ai_model_repo,
            video_price_repo=video_price_repo,
            generation_repo=generation_repo,
            generation_billing_service=generation_billing_service,
        )

    @provide(scope=Scope.REQUEST)
    def get_llm_configuration_service(
        self,
        session: AsyncSession,
        user_repo: UserRepository,
        llm_configuration_repo: LLMConfigurationRepository,
    ) -> LLMConfigurationService:
        return LLMConfigurationService(
            session=session,
            user_repo=user_repo,
            llm_configuration_repo=llm_configuration_repo,
        )
