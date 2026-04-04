from dishka import make_async_container

from .infrastructure import InfrastructureProvider
from .services import ServicesProvider

container = make_async_container(InfrastructureProvider(), ServicesProvider())
