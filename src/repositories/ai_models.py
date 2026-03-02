from src.core.models import AIModel

from .abstract_repo import AbstractRepository


class AIModelRepository(AbstractRepository[AIModel]):
    model = AIModel
