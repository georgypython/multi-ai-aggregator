from src.core.models import TokenPrice

from .abstract_repo import AbstractRepository


class TokenPriceRepository(AbstractRepository[TokenPrice]):
    model = TokenPrice
