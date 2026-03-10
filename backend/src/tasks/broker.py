from taskiq_aio_pika import AioPikaBroker

from src.core.config import settings


broker = AioPikaBroker(settings.rabbitmq.url)
