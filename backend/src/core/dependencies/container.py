from dishka import make_async_container

from .infrastructure import InfrastructureProvider
from .services import ServicesProvider
from .repositories import RepositoriesProvider

container = make_async_container(
    InfrastructureProvider(), ServicesProvider(), RepositoriesProvider()
)
