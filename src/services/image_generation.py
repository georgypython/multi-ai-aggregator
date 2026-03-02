from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from .generation_billing import GenerationBillingService

class ImageGenerationService:
    def __init__(
        self,
        session: AsyncSession,
        generation_billing_service: GenerationBillingService,
    ):
        self.session = session
        self.generation_billing_service = generation_billing_service
        
    async def generate_image(
        self, 
        user_id: UUID,
        model_id: UUID,
        prompt: str,
    ):
        pass