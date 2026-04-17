from httpx import AsyncClient
from botocore.client import BaseClient
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from dishka import Provider, Scope, provide

from src.core.config import settings
from src.services.ai_models import AIModelsService
from src.services.generation_billing import GenerationBillingService
from src.services.generation_info import GenerationInfoService
from src.services.generation_webhook import GenerationWebhookService
from src.services.image_profile import ImageProfileService
from src.services.image_generation import ImageGenerationService
from src.services.llm_configuration import LLMConfigurationService
from src.services.llm_generation import LLMGenerationService
from src.services.lava_top import LavaTopService
from src.services.openrouter import OpenRouterService
from src.services.payment_lifecycle import PaymentLifecycleService
from src.services.payment_webhook import PaymentWebhookService
from src.services.invoice import PaymentInvoiceService
from src.services.chat_memory import ChatMemoryService
from src.services.storage import StorageService
from src.services.video_profile import VideoProfileService
from src.services.video_generation import VideoGenerationService
from src.services.users import UsersService
from src.services.wavespeed import WaveSpeedService


class ServicesProvider(Provider):
    @provide(scope=Scope.REQUEST)
    def get_lava_top_service(
        self,
        client: AsyncClient,
    ) -> LavaTopService:
        return LavaTopService(client=client)

    @provide(scope=Scope.REQUEST)
    def get_payment_lifecycle_service(
        self,
        session: AsyncSession,
    ) -> PaymentLifecycleService:
        return PaymentLifecycleService(session=session)

    @provide(scope=Scope.REQUEST)
    def get_invoice_service(
        self,
        session: AsyncSession,
        lava_top_service: LavaTopService,
    ) -> PaymentInvoiceService:
        return PaymentInvoiceService(
            session=session,
            lava_top_service=lava_top_service,
            order_expire_minutes=settings.payment.order_expire_minutes,
        )

    @provide(scope=Scope.REQUEST)
    def get_payment_webhook_service(
        self,
        session: AsyncSession,
        payment_lifecycle_service: PaymentLifecycleService,
    ) -> PaymentWebhookService:
        return PaymentWebhookService(
            session=session,
            payment_lifecycle_service=payment_lifecycle_service,
        )

    @provide(scope=Scope.REQUEST)
    def get_generation_webhook_service(
        self,
        session: AsyncSession,
        generation_billing_service: GenerationBillingService,
    ) -> GenerationWebhookService:
        return GenerationWebhookService(
            session=session,
            generation_billing_service=generation_billing_service,
        )

    @provide(scope=Scope.APP)
    def get_chat_memory_service(
        self,
        redis_client: Redis,
    ) -> ChatMemoryService:
        return ChatMemoryService(redis_client=redis_client)

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
            webhook_url=settings.wavespeed.wavespeed_webhook_url,
        )

    @provide(scope=Scope.REQUEST)
    def get_storage_service(
        self,
        s3_client: BaseClient,
        session: AsyncSession,
    ) -> StorageService:
        return StorageService(
            client=s3_client,
            session=session,
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
    ) -> GenerationBillingService:
        return GenerationBillingService(
            session=session,
            token_scale=settings.billing.token_scale_decimal,
        )

    @provide(scope=Scope.REQUEST)
    def get_generation_info_service(
        self,
        session: AsyncSession,
        wavespeed_service: WaveSpeedService,
    ) -> GenerationInfoService:
        return GenerationInfoService(
            session=session,
            wavespeed_service=wavespeed_service,
        )

    @provide(scope=Scope.REQUEST)
    def get_llm_generation_service(
        self,
        session: AsyncSession,
        llm_client: OpenRouterService,
        chat_memory_service: ChatMemoryService,
        generation_billing_service: GenerationBillingService,
    ) -> LLMGenerationService:
        return LLMGenerationService(
            session=session,
            llm_client=llm_client,
            chat_memory_service=chat_memory_service,
            generation_billing_service=generation_billing_service,
        )

    @provide(scope=Scope.REQUEST)
    def get_ai_models_service(
        self,
        session: AsyncSession,
    ) -> AIModelsService:
        return AIModelsService(
            session=session,
        )

    @provide(scope=Scope.REQUEST)
    def get_users_service(
        self,
        session: AsyncSession,
    ) -> UsersService:
        return UsersService(
            session=session,
        )

    @provide(scope=Scope.REQUEST)
    def get_image_generation_service(
        self,
        session: AsyncSession,
        generation_billing_service: GenerationBillingService,
        image_configuration_service: ImageProfileService,
        wavespeed_service: WaveSpeedService,
        storage_service: StorageService,
    ) -> ImageGenerationService:
        return ImageGenerationService(
            session=session,
            generation_billing_service=generation_billing_service,
            image_profile_service=image_configuration_service,
            wavespeed_service=wavespeed_service,
            storage_service=storage_service,
        )

    @provide(scope=Scope.REQUEST)
    def get_video_generation_service(
        self,
        session: AsyncSession,
        generation_billing_service: GenerationBillingService,
        video_configuration_service: VideoProfileService,
        wavespeed_service: WaveSpeedService,
        storage_service: StorageService,
    ) -> VideoGenerationService:
        return VideoGenerationService(
            session=session,
            generation_billing_service=generation_billing_service,
            video_profile_service=video_configuration_service,
            wavespeed_service=wavespeed_service,
            storage_service=storage_service,
        )

    @provide(scope=Scope.REQUEST)
    def get_image_configuration_service(
        self,
        session: AsyncSession,
        generation_billing_service: GenerationBillingService,
    ) -> ImageProfileService:
        return ImageProfileService(
            session=session,
            generation_billing_service=generation_billing_service,
        )

    @provide(scope=Scope.REQUEST)
    def get_video_configuration_service(
        self,
        session: AsyncSession,
        generation_billing_service: GenerationBillingService,
    ) -> VideoProfileService:
        return VideoProfileService(
            session=session,
            generation_billing_service=generation_billing_service,
        )

    @provide(scope=Scope.REQUEST)
    def get_llm_configuration_service(
        self,
        session: AsyncSession,
    ) -> LLMConfigurationService:
        return LLMConfigurationService(
            session=session,
        )
